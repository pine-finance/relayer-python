import traceback
import threading
import time
import logging

logger = logging.getLogger(__name__)

class Dumper:
    def __init__(self, pool, dump_file, interval):
        self.pool = pool

        def on_tick():
            while True:
                try:
                    self.pool.dump(dump_file)
                except Exception:
                    logger.warn("Error dumping orders {}".format(dump_file))
                    logger.warn(traceback.format_exc())
                finally:
                    time.sleep(interval)

        self.thread = threading.Thread(target=on_tick, daemon=True)
        self.thread.start()
