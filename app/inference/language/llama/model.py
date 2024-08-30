from llama_cpp import Llama
import logging
import torch
import redis

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "QuantFactory/Meta-Llama-3.1-8B-instruct-GGUF"
MODEL_FILENAME = "Meta-Llama-3.1-8B-Instruct.Q8_0.gguf"

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Clear CUDA memory
torch.cuda.empty_cache()
logger.info("CUDA memory cleared.")

def load_llama_model():
    """
    Loads and initializes a pre-trained LLaMA model with the specified configuration.

    :return: An instance of the `Llama` class, representing the loaded and configured model.
    """
    logger.info(f"Loading LLaMA model '{MODEL_NAME}' from file '{MODEL_FILENAME}'...")
    return Llama.from_pretrained(
        repo_id=MODEL_NAME,
        filename=MODEL_FILENAME,
        n_gpu_layers=-1,
        n_ctx=8192,
        n_predict=100,
        top_k=40,
        repeat_penalty=1.1,
        min_p=0.05,
        top_p=0.95,
        n_threads=8,
        n_batch=512,
        temperature=0.8,
        use_mlock=True,
        flash_attn=True,
        inp_prefix="user\n\n",
        inp_suffix="assistant\n\n",
    )


# Load the LLaMA model
llm = load_llama_model()
logger.info("LLaMA model loaded successfully.")

# Set up Redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def generate_streaming_response(prompt: str, user_uuid: str) -> iter:
    """
    Generates a streaming response from the model based on the provided prompt.

    :param llm: The loaded LLaMA model instance.
    :param prompt: The prompt to send to the model.
    :return: A generator that yields cleaned chunks as they arrive.
    """
    conversation_id = "1323"
    full_response = []
    logger.info("Streaming Chat")
    response_stream = llm.create_chat_completion(
        messages=prompt,
        stream=True
    )
    for chunk in response_stream:
        delta = chunk['choices'][0]['delta']
        if 'content' in delta:
            full_response.append(delta['content'])
            yield delta['content']
    
    conversation_id = user_uuid
    # Check the type of the existing key in Redis
    key_type = redis_client.type(conversation_id).decode('utf-8')
    full_response_str = ''.join(full_response)
    if key_type == 'list':
        redis_client.rpush(conversation_id, full_response_str)
    else:
        # Handle the case where the key type is not a list
        logger.info(f"Key {conversation_id} is of type {key_type}. Expected type: list.")
        # Optionally, clear the key and re-create it as a list
        redis_client.delete(conversation_id)
        redis_client.rpush(conversation_id,full_response_str)

def generate_non_streaming_response(prompt: str) -> str:
    """
    Generates a non-streaming response from the model based on the provided prompt.

    :param llm: The loaded LLaMA model instance.
    :param prompt: The prompt to send to the model.
    :return: The response content from the model.
    """
    answer = llm.create_chat_completion(
        messages=prompt,
    )
    response_content = answer['choices'][0]['message']['content']
    conversation_id = "123"
    redis_client.set(conversation_id, response_content)
    return response_content