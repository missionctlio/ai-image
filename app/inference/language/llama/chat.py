from app.inference.language.llama.model import LlamaModel
import logging
import redis
from sqlalchemy.orm import Session
from app.db.model.user import get_user_from_uuid
from app.utils.redis_utils import RedisUtils
# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _generate_chat_prompt(user_uuid: str, prompt: str) -> list:
    prompt_content = f"prompt: {prompt}"
    system_content = (
        "You are an advanced AI chatbot. You give helpful, respectful, and informational answers. "
    )
    
    conversation_id = user_uuid
    
    redis_client = RedisUtils()
    
    redis_client.append_to_redis(conversation_id, prompt)
    
    redis_memory = redis_client.get_redis_memory(conversation_id)
    
    # Append Redis conversation memory to the prompt
    system_content += "Chat Memory: \n" + "\n".join(redis_memory)
    prompt_list = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt_content}
    ]
    
    logger.info(f"Generated chat prompt: {prompt}")
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
    # Usage:
    llm_model = LlamaModel()
    llm_model.load_llama_model()
    answer = llm_model.generate_streaming_response(prompt=prompt, user_uuid=user_uuid)
    for chunk in answer:
        # Yield each chunk of the response.
        yield chunk