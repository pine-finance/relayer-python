from web3.contract import ConciseContract

from .contracts import uniswap_factory
from .contracts import uniswap_ex
from .contracts import ierc20

from .utils import Watcher, safe_get_logs
from .model import Order

from web3 import Web3
import traceback
import logging

logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, pool, node, uniswapex_addr, uniswap_factory_addr, start_at, blacklist):
        self.pool = pool
        self.node = node
        self.w3 = Web3(Web3.HTTPProvider(node))
        self.watcher = Watcher(self.w3)
        self.last_block = start_at
        self.uniswap_cache = {}
        
        self.token_blacklist = set()
        for token in blacklist.split(','):
            self.token_blacklist.add(token.lower())

        self.uniswap_ex = self.w3.eth.contract(
            address=self.w3.toChecksumAddress(uniswapex_addr),
            abi=uniswap_ex.abi,
        )

        self.uniswap_factory = self.w3.eth.contract(
            address=self.w3.toChecksumAddress(uniswap_factory_addr),
            abi=uniswap_factory.abi,
        )

        self.uniswap_ex_concise = ConciseContract(self.uniswap_ex)
        self.uniswap_factory_concise = ConciseContract(self.uniswap_factory)

        def on_block(block_number):
            logger.debug("Crawler on block {}".format(block_number))
            self.search_for_orders(block_number)

        self.watcher.on_new_block(on_block)

    def on_order(self, raw_order, tx):
        logger.info("Found order {} {}".format(tx, raw_order))

        order = Order.fromList(self.uniswap_ex_concise.decodeOrder(raw_order), tx)
        
        logger.debug("Decoded order {} fromToken {}".format(tx, order.fromToken))
        logger.debug("Decoded order {} toToken   {}".format(tx, order.toToken))
        logger.debug("Decoded order {} minReturn {}".format(tx, order.minReturn))
        logger.debug("Decoded order {} fee       {}".format(tx, order.fee))
        logger.debug("Decoded order {} owner     {}".format(tx, order.owner))
        logger.debug("Decoded order {} secret    {}".format(tx, order.secret.hex()))
        logger.debug("Decoded order {} witness   {}".format(tx, order.witness))
        self.pool.add(order)

    def parse_order(self, tx_data, token):
        if 'a9059cbb' not in tx_data:
            return []

        orders = []
        transfers = tx_data.split('a9059cbb')

        for transfer in transfers[1:]:
            if len(transfer) >= 704:
                order = transfer[256:][:450]

                # UniswapEX orders have the fromToken encoded on the data itself
                # if we can't find the fromToken, this is not an UniswapEX order
                order_low = order.lower()
                token_low = token.replace('0x', '').lower()
                if token_low in order_low and order_low.index(token_low) == 24:
                    orders.append(order)
                    logger.debug("Found order n{} for token {}".format(len(orders), token))
                else:
                    logger.debug("Found false possitive for token {}".format(token))

        return orders


    def search_eth_orders(self, from_block, to_block):
        eth_deposits = self.uniswap_ex.events.DepositETH.getLogs(
            fromBlock=from_block,
            toBlock=to_block
        )

        logger.debug("Found {} ETH deposits".format(len(eth_deposits)))

        for deposit in eth_deposits:
            self.on_order(deposit.args._data, deposit.transactionHash.hex())

    def search_orders_for_token(self, token, from_block, to_block):
        if token.lower() in self.token_blacklist:
            logger.debug("Skipping blacklisted token {}".format(token))
            return

        token_contract = self.w3.eth.contract(
            address=self.w3.toChecksumAddress(token),
            abi=ierc20.abi,
        )

        all_token_transfers = safe_get_logs(
            token_contract.events.Transfer.getLogs,
            from_block,
            to_block
        )

        logger.debug("Found {} token transfers for {}".format(len(all_token_transfers), token))

        checked = 0
        last_check = None
        for transfer in all_token_transfers:
            tx_hash = transfer.transactionHash.hex()

            checked = checked + 1

            if tx_hash == last_check:
                continue

            tx = self.w3.eth.getTransaction(tx_hash)

            logger.debug("{}/{} Checking TX {}".format(checked, len(all_token_transfers), tx_hash))

            for order in self.parse_order(tx.input, token):
                self.on_order(order, tx_hash)

            last_check = tx_hash
    
    def get_uniswap_token(self, i):
        if i in self.uniswap_cache:
            return self.uniswap_cache[i]
        
        token = self.uniswap_factory_concise.getTokenWithId(i)
        self.uniswap_cache[i] = token
        return token

    def search_uniswap_tokens(self, from_block, to_block):
        total_tokens = self.uniswap_factory_concise.tokenCount()
        logger.debug("Found {} tokens on Uniswap".format(total_tokens))
        checked = 0
        for x in range(1, total_tokens):
            token = self.get_uniswap_token(x)
            checked = checked + 1
            logger.debug("{}/{} - Token {} on Uniswap is {}".format(checked, total_tokens, x, token))
            self.search_orders_for_token(token, from_block, to_block)

    def search_for_orders(self, to_block):
        try:
            from_block = self.last_block
            self.search_eth_orders(from_block, to_block)
            self.search_uniswap_tokens(from_block, to_block)
            self.last_block = to_block
        except Exception:
            logger.warn(traceback.format_exc())
