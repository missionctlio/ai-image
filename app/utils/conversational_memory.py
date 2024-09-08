import redis
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class ConversationalMemory:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        logger.debug(f"Initializing ConversationalMemory for conversation ID: {self.conversation_id}")
        
        redis_host = os.environ.get('REDIS_HOST')
        redis_port = os.environ.get('REDIS_PORT')

        logger.debug(f"Connecting to Redis on {redis_host}:{redis_port}")
        
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0
        )
        
        if self.redis_client.ping():
            logger.debug("Successfully connected to Redis.")
        else:
            logger.error("Failed to connect to Redis.")

    def _get_key(self, key: str) -> str:
        """Construct the Redis key using the conversation ID."""
        redis_key = f"{self.conversation_id}:{key}"
        logger.debug(f"Constructed Redis key: {redis_key}")
        return redis_key

    def _check_key_type(self, key: str) -> str:
        """Check the type of the existing key in Redis."""
        redis_key = self._get_key(key)
        logger.debug(f"Checking key type for {redis_key}")
        
        try:
            key_type = self.redis_client.type(redis_key).decode('utf-8')
            logger.debug(f"Key {redis_key} is of type {key_type}.")
            return key_type
        except Exception as e:
            logger.error(f"Error checking key type for {redis_key}: {e}")
            raise

    def _handle_non_list_key(self, key: str):
        """Handle the case where the key type is not a list."""
        redis_key = self._get_key(key)
        logger.warning(f"Key {redis_key} is not a list. Deleting the key.")
        
        try:
            self.redis_client.delete(redis_key)
            logger.debug(f"Key {redis_key} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting key {redis_key}: {e}")

    def _push_to_redis(self, key: str, value: str):
        """Push a value to Redis."""
        redis_key = self._get_key(key)
        key_type = self._check_key_type(redis_key)

        logger.debug(f"Attempting to push value to Redis key {redis_key}.")
        
        if key_type == 'list':
            try:
                self.redis_client.rpush(redis_key, value)
                logger.debug(f"Value pushed to Redis key {redis_key}: {value}")
            except Exception as e:
                logger.error(f"Error pushing value to Redis key {redis_key}: {e}")
        else:
            logger.warning(f"Redis key {redis_key} is not a list. Handling non-list key.")
            self._handle_non_list_key(redis_key)
            self.redis_client.rpush(redis_key, value)
            logger.debug(f"Recreated list key {redis_key} and pushed value: {value}")

    def _get_redis_memory(self, key: str) -> list:
        """Retrieve and decode the Redis memory."""
        redis_key = self._get_key(key)
        logger.debug(f"Retrieving memory for Redis key {redis_key}.")
        
        try:
            redis_memory = self.redis_client.lrange(redis_key, 0, -1)
            decoded_memory = [item.decode('utf-8') for item in redis_memory]
            logger.debug(f"Successfully retrieved memory for {redis_key}: {decoded_memory}")
            return decoded_memory
        except Exception as e:
            logger.error(f"Error retrieving memory for {redis_key}: {e}")
            return []

    def append_to_memory(self, value: str):
        """Append a value to the conversation-specific memory."""
        logger.debug(f"Appending value to memory: {value}")
        self._push_to_redis('messages', value)

    def get_memory(self) -> list:
        """Get the conversation-specific memory."""
        logger.debug(f"Fetching memory for conversation ID: {self.conversation_id}")
        return self._get_redis_memory('messages')

    def clear_memory(self):
        """Clear all memory for the current conversation."""
        logger.debug(f"Clearing memory for conversation ID: {self.conversation_id}")
        try:
            # Delete the key associated with the conversation's messages
            self.redis_client.delete(self._get_key('messages'))
            logger.debug(f"Memory cleared for conversation ID: {self.conversation_id}")
        except Exception as e:
            logger.error(f"Error clearing memory for conversation ID {self.conversation_id}: {e}")
