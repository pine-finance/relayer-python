from web3.contract import ConciseContract

from .contracts import uniswap_factory
from .contracts import uniswap_ex
from .contracts import ierc20

from .utils import Watcher, safe_get_logs
from .model import Order

from web3 import Web3, middleware

import traceback

from eth_account import Account
from coincurve.keys import PrivateKey
from web3.gas_strategies.time_based import fast_gas_price_strategy
from Crypto.Hash import keccak
import logging
import time


logger = logging.getLogger(__name__)

class Executor:
    def __init__(self, pool, node, pk, gas_multiplier, uniswapex_addr, whitelisted):
        self.pool = pool
        self.node = node
        self.w3 = Web3(Web3.HTTPProvider(node))
        self.watcher = Watcher(self.w3)
        self.gas_multiplier = gas_multiplier
        self.account = Account.privateKeyToAccount(pk.replace('0x', ''))
        self.w3.eth.setGasPriceStrategy(fast_gas_price_strategy)

        self.whitelisted_tokens = set()

        for token in whitelisted.split(','):
            self.whitelisted_tokens.add(token.lower())

        self.uniswap_ex = self.w3.eth.contract(
            address=self.w3.toChecksumAddress(uniswapex_addr),
            abi=uniswap_ex.abi,
        )

        self.uniswap_ex_concise = ConciseContract(self.uniswap_ex)

        def on_block(block_number):
            logger.debug("Executor on block {}".format(block_number))
            self.check_open_orders()

        self.watcher.on_new_block(on_block)
        logger.info("Using account {}".format(self.account.address))

    def order_exists(self, order):
        result = self.uniswap_ex_concise.existOrder(
            order.fromToken,
            order.toToken,
            order.minReturn,
            order.fee,
            order.owner,
            order.witness
        )

        logger.debug("Order {} does{} exists".format(order.tx, "" if result else " not"))
        return result

    def order_ready(self, order):
        result = self.uniswap_ex_concise.canExecuteOrder(
            order.fromToken,
            order.toToken,
            order.minReturn,
            order.fee,
            order.owner,
            order.witness
        )

        logger.debug("Order {} is{} ready".format(order.tx, "" if result else " not"))
        return result

    def pull_nonce(self):
        return self.w3.eth.getTransactionCount(self.account.address)

    def check_and_fill_order(self, order):
        if not order or not order.fromToken or not order.toToken or not order.tx:
            return "error"

        if not self.order_exists(order):
            return "unknown"
        
        if not self.order_ready(order):
            return None

        gas_price = self.w3.eth.generateGasPrice()
        logger.debug("Loaded raw gas price {}".format(gas_price))
        gas_price = int(gas_price * float(self.gas_multiplier))

        nonce = self.pull_nonce()

        logger.debug("Using nonce {}, gasprice {}".format(nonce, gas_price))

        secret_pk = PrivateKey(order.secret)
        keccak_hash = keccak.new(digest_bits=256)
        keccak_hash.update(bytearray.fromhex(self.account.address.replace('0x', '')))
        witnesses = secret_pk.sign_recoverable(bytes(bytearray.fromhex(keccak_hash.hexdigest())), hasher=None)

        logger.debug("Signed order {} witnesses {}".format(order.tx, witnesses.hex()))

        calc_witness = Account.privateKeyToAccount(order.secret.hex().replace('0x', '')).address
        if calc_witness != order.witness:
            logger.warn("Witness missmatch order {} witness {} order witness {}".format(order.tx, calc_witness, order.witness))
            return "error"

        logger.debug("Sending tx for order {}".format(order.tx))
        transaction = self.uniswap_ex.functions.executeOrder(
            order.fromToken,
            order.toToken,
            order.minReturn,
            order.fee,
            order.owner,
            witnesses
        ).buildTransaction({
            'gasPrice': gas_price,
            'nonce': nonce,
            'from': self.account.address
        })

        if order.fromToken.lower() not in self.whitelisted_tokens and order.toToken.lower() not in self.whitelisted_tokens and transaction['gas'] * gas_price > order.fee:
            logger.debug("Order {} fee is not enought, cost {} vs {} -> {} * {}".format(order.tx, order.fee, transaction['gas'] * gas_price, transaction['gas'], gas_price))
            return None

        signed_txn = self.w3.eth.account.signTransaction(transaction, private_key=self.account.privateKey)
        logger.debug("Signed tx for order {}".format(order.tx))
        tx = Web3.toHex(self.w3.eth.sendRawTransaction(signed_txn.rawTransaction))
        logger.info("Relayed order {} tx {}".format(order.tx, tx))

        if not self.wait_for_confirmation(tx, nonce):
            return None

        return tx

    def wait_for_confirmation(self, tx, nonce, timeout = 300):
        start_time = time.time()
        logger.info("Waiting confirmation for TX {}".format(tx))
        while time.time() - start_time < timeout:
            # Wait for the nonce to increase
            try:
                if self.w3.eth.getTransactionReceipt(tx):
                    logger.info("TX {} confirmed (dettected by nonce increase)".format(tx))
                    return True
            except:
                pass

            time.sleep(5)
        
        logger.info("TX {} confirmation timeout".format(tx))
        return False

    def check_open_orders(self):
        for order in self.pool.all():
            if not order:
                continue

            try:
                logger.debug("Checking order {}".format(order.tx))
                receipt = self.check_and_fill_order(order)
                if receipt:
                    self.pool.finish(order, receipt)
            except Exception as e:
                logger.warn("Error filling order {} err {}".format(order.tx, str(e)))
