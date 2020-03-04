
from redis_collections import Deque, Dict, Set

from .model import OrderDecoder, OrderEncoder

import logging
import json

logger = logging.getLogger(__name__)

class Pool:
    def __init__(self, redis):
        self.orders = Set(key="orders", redis=redis)
        self.finished = Set(key="completed", redis=redis)

    def add(self, order):
        logger.debug("Added order {} to pool".format(order.tx))
        self.orders.add(order)
    
    def all(self):
        result = self.orders.difference(self.finished)
        logger.debug("Loading {} orders from redis".format(len(result)))
        return result

    def finish(self, order, tx):
        logger.debug("Finished order {} with tx {}".format(order.tx, tx))
        self.finished.add(order)

    def dump(self, dest):
        exp_file = open(dest, "wt")
        n = exp_file.write(json.dumps(list(self.orders), cls=OrderEncoder))
        logger.info("Dumping redis into {}".format(dest))
        exp_file.close()

    def load(self, source):
        content = open(source, "r").read()
        orders = json.loads(content, cls=OrderDecoder)
        for order in orders:
            logger.info("Imported from file order {}".format(order.tx))
            self.orders.add(order)
