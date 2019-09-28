import uniexecutor

import configargparse
import logging
import logging.config
import sys
import getpass

def main():
    p = configargparse.get_argument_parser()
    p.add('-ue', '--uniswap-ex', help="Uniswap EX contract address", env_var="UNISWAP_EX_CONTRACT", default="0xbd2a43799b83d9d0ff56b85d4c140bce3d1d1c6c")
    p.add('-uf', '--uniswap-factory', help="Uniswap factory contract address", env_var="UNISWAP_FACTORY_CONTRACT", default="0xc0a47dfe034b400b47bdad5fecda2621de6c4d95")
    p.add('-pk', '--private-key', help="Private key of the Worker", required=False, env_var='PRIVATE_KEY')
    p.add('-n', '--node', help="URL Of the Ethereum node", required=True, env_var='ETHEREUM_NODE')
    p.add('-rf', '--redis-file', help="Path to store RedisLite db - DEFAULT: memory", required=False, env_var='RELAYER_REDIS_FILE')
    p.add('-rp', '--redis-port', help="Redis database port - DEFAULT: redis-lite", required=False, env_var='RELAYER_REDIS_PORT')
    p.add('-ru', '--redis-url', help="Redis database url - DEFAULT: redis-lite", required=False, env_var='RELAYER_REDIS_URL')
    p.add('-gm', '--gas-multiplier', help="Gas limit multiplier", required=False, env_var='RELAYER_GAS_MULTIPLIER', default="1.01")
    p.add('-lf', '--log-file', help="Log file", required=False, env_var='LOG_FILE')
    p.add('-cll', '--console-log-level', help='Log level for console output', required=False, env_var="CONSOLE_LOG_LEVEL", default=20)
    p.add('-fll', '--file-log-level', help='Log level for file output', required=False, env_var="FILE_LOG_LEVEL", default=10)
    p.add('-s', '--service', help='Service to run', required=False, env_var="SERVICE", default="full")
    p.add('-b', '--start-block', help="First block to start sync", required=False, env_var="START_BLOCK", default=8579313)
    p.add('-bl', '--black-listed-tokens', help="Uniswap tokens to ignore", required=False, env_var="UNISWAP_BLACKLIST", default="0xdac17f958d2ee523a2206206994597c13d831ec7")
    p.add('-wl', '--white-listed-tokens', help="Whitelist tokens to always relay", required=False, env_var="TOKEN_WHITELIST", default="")

    options = p.parse_args()

    logger = logging.getLogger("uniexecutor")
    logger.setLevel(int(options.console_log_level))
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s: %(name)s: %(message)s", 
        datefmt="%Y-%m-%d - %H:%M:%S"
    )

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(int(options.console_log_level))
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if options.log_file:
        fh = logging.FileHandler(options.log_file, "w")
        fh.setLevel(int(options.file_log_level))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if not options.private_key:
        options.private_key = getpass.getpass(prompt='PK: ') 

    uniexecutor.start(options)

if __name__ == "__main__":
    main()
