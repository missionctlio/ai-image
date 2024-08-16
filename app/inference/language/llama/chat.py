from app.inference.language.llama.model import load_llama_model
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _generate_chat_prompt(prompt: str) -> list:
    prompt_content = f"prompt: {prompt}"
    system_content = (
        "You are an advanced ai chatbot. You give helpful, respectful and informational answers. "
        "You reply in markdown format whenever the response is appropriate"
        "You return codeblocks in the format of three backticks followed by the language. "
    )
    prompt_list = [
        {"role": "system", "content": system_content}, 
        {"role": "user", "content": prompt_content}
    ]
    logger.info(f"Generated chat prompt: {prompt_list}")
    return prompt_list

def generate_chat(user_prompt: str) -> str:
    """
    Generates a product chat based on the provided user prompt.

    This function uses a chat generation model to create a detailed product chat. It first creates
    a formatted prompt using `generate_chat_prompt`, then sends this prompt to the model to obtain a response. 
    The chat is extracted from the model's response and returned.

    :param user_prompt: The user-provided prompt that will be used to generate the product chat.
    :return: A string containing the generated product chat.
    """
    prompt = _generate_chat_prompt(user_prompt)
    answer = load_llama_model().create_chat_completion(
        messages=prompt,
    )
    chat = answer['choices'][0]['message']['content']
    logger.info(f"Generated chat: {chat}")
    return chat
