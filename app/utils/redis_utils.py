import redis
import os
import logging
from dotenv import load_dotenv
logger = logging.getLogger(__name__)
load_dotenv()

class RedisUtils:
    def __init__(self):
        self.redis_client = redis.Redis(host=os.environ.get('REDIS_HOST'), port=os.environ.get('REDIS_PORT'), db=0)

    def _check_key_type(self, key):
        """Check the type of the existing key in Redis"""
        key_type = self.redis_client.type(key).decode('utf-8')
        return key_type

    def _handle_non_list_key(self, key):
        """Handle the case where the key type is not a list"""
        logger.info(f"Key {key} is of type {self._check_key_type(key)}. Expected type: list.")
        # Optionally, clear the key and re-create it as a list
        self.redis_client.delete(key)

    def _push_to_redis(self, key, value):
        """Push a value to Redis"""
        key_type = self._check_key_type(key)
        if key_type == 'list':
            self.redis_client.rpush(key, value)
        else:
            self._handle_non_list_key(key)
            self.redis_client.rpush(key, value)

    def _get_redis_memory(self, key):
        """Retrieve and decode the Redis memory"""
        redis_memory = self.redis_client.lrange(key, 0, -1)
        redis_memory = [item.decode('utf-8') for item in redis_memory]
        return redis_memory

    def append_to_redis(self, key, value):
        """Append a value to Redis"""
        self._push_to_redis(key, value)

    def get_redis_memory(self, key):
        """Get the Redis memory"""
        return self._get_redis_memory(key)