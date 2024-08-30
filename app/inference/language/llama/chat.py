from app.inference.language.llama.model import generate_streaming_response
import logging
import redis
from sqlalchemy.orm import Session
from app.db.model.user import get_user_from_uuid
# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def _generate_chat_prompt(user_uuid: str, prompt: str) -> list:
    prompt_content = f"prompt: {prompt}"
    system_content = (
        "You are an advanced AI chatbot. You give helpful, respectful, and informational answers. "
    )
    
    conversation_id = user_uuid
    
    # Check the type of the existing key in Redis
    key_type = redis_client.type(conversation_id).decode('utf-8')
    
    if key_type == 'list':
        redis_client.rpush(conversation_id, prompt_content)
    else:
        # Handle the case where the key type is not a list
        logger.info(f"Key {conversation_id} is of type {key_type}. Expected type: list.")
        # Optionally, clear the key and re-create it as a list
        redis_client.delete(conversation_id)
        redis_client.rpush(conversation_id, prompt_content)
    
    # Retrieve and decode the Redis memory
    redis_memory = redis_client.lrange(conversation_id, 0, -1)
    redis_memory = [item.decode('utf-8') for item in redis_memory]
    logger.info(f"Redis memory: {redis_memory}")

    # Append Redis conversation memory to the prompt
    system_content += "Chat Memory: \n" + "\n".join(redis_memory)
    prompt_list = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt_content}
    ]
    
    logger.info(f"Generated chat prompt: {prompt_list}")
    return prompt_list

def generate_chat(user_uuid: str, user_prompt: str):
    """
    Generates a product chat based on the provided user prompt and user UUID.

    This function uses a chat generation model to create a detailed product chat. It first creates
    a formatted prompt using `generate_chat_prompt`, then sends this prompt to the model to obtain a response. 
    The chat is extracted from the model's response and returned.

    :param user_uuid: The UUID of the user to use as the conversation ID.
    :param user_prompt: The user-provided prompt that will be used to generate the product chat.
    :param db: The database session to use for user retrieval.
    :return: A string containing the generated product chat.
    """
    prompt = _generate_chat_prompt(user_uuid, user_prompt)
    answer = generate_streaming_response(prompt=prompt, user_uuid=user_uuid)
    for chunk in answer:
        # Yield each chunk of the response.
        yield chunk