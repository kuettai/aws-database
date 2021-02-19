#!/usr/bin/env python3

import argparse
import time
import curses
import threading
import redis
import os
import random
import signal
import sys

class ClientSideCachingConnection():

    def __init__(self, redis, cache_size):
        self.log = ""
        self.caching_connection = redis.connection_pool.make_connection()
        self.caching_connection.send_command('CLIENT ID')
        client_id = self.caching_connection.read_response()
        self.caching_connection.send_command('subscribe', '__redis__:invalidate')
        self.thread = threading.Thread(target=self.caching_thread, args=())
        self.thread.daemon = True
        self.thread.start()

        self.client = redis
        self.log += self.client.execute_command('CLIENT TRACKING ON REDIRECT {}'.format(client_id)).decode('utf-8')

        self.shared_cache = {}

        self.hits = 0
        self.misses = 0
        self.invalidations = 0
        self.evictions = 0
        self.total_time = 0
        self.total_requests = 0

        self.cache_size = cache_size

    def _get(self, key):
        # Check if key is in the local cache
        if key in self.shared_cache:
            self.hits += 1
            return self.shared_cache[key]

        # Key is not cached locally, fetch it from Redis
        value = self.client.get(key).decode('utf-8')

        # Update the cache if necessary
        if self.cache_size:
            if len(self.shared_cache) == self.cache_size:
                self.shared_cache.popitem()
                self.evictions += 1
            self.shared_cache[key] = value
        self.misses += 1
        return value

    def get(self, key):
        # Wrapper around get to record the time taken
        start = time.time()
        response = self._get(key)
        self.total_time += int((time.time() - start) * 1000000) # time in us
        self.total_requests += 1
        return response

    def caching_thread(self):
        while True:
            # Constantly check for invalidation messages, when
            # we recieve one, kick the item out of the local
            # cache.
            invalidation = self.caching_connection.read_response()
            if invalidation[0].decode('utf-8') == 'message':
                key = invalidation[2][0].decode('utf-8')
                self.shared_cache.pop(key, None)
                self.invalidations += 1

def main_session(stdscr):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--local-cache-size', type=int)
    parser.add_argument('--cache-size', type=int)
    parser.add_argument('--read-ratio', default=1.0, type=float)

    args = parser.parse_args()

    redis_client = redis.Redis(host='clientcachetest.mils3x.0001.use1.cache.amazonaws.com')
    redis_client.flushall()

    caching_client = ClientSideCachingConnection(redis_client, args.local_cache_size)
    key_value = 'XXXXX'
    for i in range(args.cache_size):
        redis_client.set('X' + str(i), key_value)


    iteration = 0
    while True:
        key = 'X' + str(random.randrange(0, args.cache_size))
        if random.random() < args.read_ratio:
            caching_client.get(key)
        else:
            redis_client.set(key, key_value)
        iteration += 1
        if iteration % 1000 == 0:
            stdscr.clear()
            stdscr.addstr('Local Cache Hits: {}\n'.format(caching_client.hits))
            stdscr.addstr('Local Cache Misses: {}\n'.format(caching_client.misses))
            stdscr.addstr('Local Cache Invalidations: {}\n'.format(caching_client.invalidations))
            stdscr.addstr('Local Cache Evictions: {}\n'.format(caching_client.evictions))
            stdscr.addstr('Average Latency: {:.2f}us\n'.format(
                caching_client.total_time/caching_client.total_requests))
            stdscr.refresh()


def endfunc(sig, frame):
    print ('Finished.')
    sys.exit(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, endfunc)
    curses.wrapper(main_session)
    os.exit(1)
