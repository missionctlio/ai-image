from app.inference.language.llama.model import load_llama_model
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load LLaMA model
llm = load_llama_model()

def generate_description_prompt(prompt: str) -> list:
    prompt_content = f"prompt: {prompt}"
    system_content = (
        "You are a description generator for a wide variety of products with western and texas themes. "
        "Create engaging and detailed product descriptions from the provided prompt. Do not give sizes or colors, "
        "only describe the prompt in the form of a product description."
    )
    prompt_list = [
        {"role": "system", "content": system_content}, 
        {"role": "user", "content": prompt_content}
    ]
    logger.info(f"Generated description prompt: {prompt_list}")
    return prompt_list

def generate_description(user_prompt: str) -> str:
    prompt = generate_description_prompt(user_prompt)
    answer = llm.create_chat_completion(
        messages=prompt,
    )
    description = answer['choices'][0]['message']['content']
    logger.info(f"Generated description: {description}")
    return description