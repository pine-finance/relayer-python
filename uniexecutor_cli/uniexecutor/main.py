
from .crawler import Crawler
from .executor import Executor
from .pool import Pool

from redislite import Redis as RedisLite
from redis import Redis
import logging


logger = logging.getLogger(__name__)

def start(options):
    if not options.redis_port:
        redis = RedisLite(options.redis_file)
    else:
        redis = Redis(host=options.redis_url, port=options.redis_port, db=0)

    pool = Pool(redis)

    if options.service == "full" or options.service == "crawler":
        logger.info("Starting crawler, configured service {}".format(options.service))
        Crawler(pool, options.node, options.uniswap_ex, options.uniswap_factory, int(options.start_block), options.black_listed_tokens)
    if options.service == "full" or options.service == "executor":
        logger.info("Starting executor, configured service {}".format(options.service))
        Executor(pool, options.node, options.private_key, options.gas_multiplier, options.uniswap_ex, options.white_listed_tokens)

