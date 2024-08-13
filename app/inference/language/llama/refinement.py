from app.inference.language.llama.model import load_llama_model
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load LLaMA model
llm = load_llama_model()

def refine_prompt(prompt: str) -> list:
    prompt_content = f"prompt: {prompt}"
    system_content = (
        "You are an advanced AI prompt engineer. "
        "Create engaging and detailed prompts from the provided prompt. "
        "Your prompts must always be 77 tokens or less."
    )
    prompt_list = [
        {"role": "system", "content": system_content}, 
        {"role": "user", "content": prompt_content}
    ]
    logger.info(f"Refined prompt: {prompt_list}")
    return prompt_list

def refined_prompt(user_prompt: str) -> str:
    prompt = refine_prompt(user_prompt)
    answer = llm.create_chat_completion(
        messages=prompt,
    )
    refined_prompt = answer['choices'][0]['message']['content']
    logger.info(f"Refined prompt: {refined_prompt}")
    return refined_prompt