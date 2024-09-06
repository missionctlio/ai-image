import redis
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class ConversationalMemory:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.redis_client = redis.Redis(
            host=os.environ.get('REDIS_HOST'),
            port=os.environ.get('REDIS_PORT'),
            db=0
        )

    def _get_key(self, key: str) -> str:
        """Construct the Redis key using the conversation ID."""
        return f"{self.conversation_id}:{key}"

    def _check_key_type(self, key: str) -> str:
        """Check the type of the existing key in Redis."""
        redis_key = self._get_key(key)
        key_type = self.redis_client.type(redis_key).decode('utf-8')
        return key_type

    def _handle_non_list_key(self, key: str):
        """Handle the case where the key type is not a list."""
        redis_key = self._get_key(key)
        logger.info(f"Key {redis_key} is of type {self._check_key_type(redis_key)}. Expected type: list.")
        # Optionally, clear the key and re-create it as a list
        self.redis_client.delete(redis_key)

    def _push_to_redis(self, key: str, value: str):
        """Push a value to Redis."""
        redis_key = self._get_key(key)
        key_type = self._check_key_type(redis_key)
        if key_type == 'list':
            self.redis_client.rpush(redis_key, value)
        else:
            self._handle_non_list_key(redis_key)
            self.redis_client.rpush(redis_key, value)

    def _get_redis_memory(self, key: str) -> list:
        """Retrieve and decode the Redis memory."""
        redis_key = self._get_key(key)
        redis_memory = self.redis_client.lrange(redis_key, 0, -1)
        redis_memory = [item.decode('utf-8') for item in redis_memory]
        return redis_memory

    def append_to_memory(self, value: str):
        """Append a value to the conversation-specific memory."""
        self._push_to_redis('messages', value)

    def get_memory(self) -> list:
        """Get the conversation-specific memory."""
        return self._get_redis_memory('messages')
