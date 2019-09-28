
from redis_collections import Deque, Dict, Set
import logging

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
