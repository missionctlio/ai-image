from llama_cpp import Llama
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "QuantFactory/Meta-Llama-3.1-8B-instruct-GGUF"
MODEL_FILENAME = "Meta-Llama-3.1-8B-Instruct.Q8_0.gguf"

"""
Loads and initializes a pre-trained LLaMA model with the specified configuration.

This function loads the LLaMA model from a pre-defined repository and file. It configures various model parameters 
such as the number of GPU layers, context size, and prediction settings. The model is prepared for use in generating 
responses based on the specified configuration options.

:return: An instance of the `Llama` class, representing the loaded and configured model.
"""
logger.info(f"Loading LLaMA model '{MODEL_NAME}' from file '{MODEL_FILENAME}'...")
llm = Llama.from_pretrained(
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
logger.info("LLaMA model loaded successfully.")
def generate_streaming_response(prompt: str) -> iter:
    """
    Generates a streaming response from the model based on the provided prompt.

    This function uses the LLaMA model to generate a streaming response to the given prompt.

    :param prompt: The prompt to send to the model.
    :return: A generator that yields cleaned chunks as they arrive.
    """
    logger.info("Streaming Chat")
    response_stream = llm.create_chat_completion(
        messages=prompt,
        stream=True
    )
    for chunk in response_stream:
        delta = chunk['choices'][0]['delta']
        if 'content' in delta:
            print(delta['content'], end="")
            yield delta['content']
def generate_non_streaming_response(prompt: str) -> str:
    """
    Generates a non-streaming response from the model based on the provided prompt.

    This function uses the LLaMA model to generate a response to the given prompt in a non-streaming mode.

    :param prompt: The prompt to send to the model.
    :return: The response content from the model.
    """
    answer = llm.create_chat_completion(
        messages=prompt,
    )
    response_content = answer['choices'][0]['message']['content']
    return response_content
