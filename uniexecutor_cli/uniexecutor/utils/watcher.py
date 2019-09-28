from web3 import Web3

import traceback
import threading
import time
import logging

logger = logging.getLogger(__name__)

class Watcher:
    def __init__(self, web3):
        self.w3 = web3
        self.watching = False
        self.callbacks = []
    
    def on_new_block(self, callback):
        if not self.watching:
            self._start_block_watch()
            self.watching = True

        self.callbacks.append(callback)

    def _on_thread_die(self):
        self._start_block_watch()

    def _start_block_watch(self):
        def new_block_watch():
            def call_callbacks(block_number):
                for callback in self.callbacks:
                    callback(block_number)

            last_block_number = 0
            while True:
                try:
                    last_block = self.w3.eth.blockNumber
                    if last_block > last_block_number:
                        last_block_number = last_block
                        call_callbacks(last_block)
                except Exception:
                    logger.warn(traceback.format_exc())
                finally:
                    time.sleep(5)

        self.thread = threading.Thread(target=new_block_watch, daemon=False)
        self.thread.start()