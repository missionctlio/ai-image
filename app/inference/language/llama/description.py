from app.inference.language.llama.model import LlamaModel
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _generate_description_prompt(prompt: str) -> list:
    """
    Creates a structured prompt for generating product descriptions based on the given user prompt.

    This function constructs a prompt list formatted for a description generation model. It includes a system message 
    to instruct the model and a user message containing the specific prompt provided by the user.

    :param prompt: The user-provided text that will be used to generate a product description.
    :return: A list of dictionaries representing the prompt for the model, formatted as required by the chat completion API.
    """
    prompt_content = f"prompt: {prompt}"
    system_content = (
        "You are an advanced AI description generator for an online store that sells texas and western themed products."
        "Create engaging and detailed descriptions from the provided user provided prompt."
        "Your descriptions must always be 100 characters or less."
    )
    prompt_list = [
        {"role": "system", "content": system_content}, 
        {"role": "user", "content": prompt_content}
    ]
    logger.info(f"Generated description prompt: {prompt_list}")
    return prompt_list

def generate_description(user_prompt: str):
    """
    Generates a product description based on the provided user prompt.

    This function uses a description generation model to create a detailed product description. It first creates
    a formatted prompt using `generate_description_prompt`, then sends this prompt to the model to obtain a response. 
    The description is extracted from the model's response and returned.

    :param user_prompt: The user-provided prompt that will be used to generate the product description.
    :return: A string containing the generated product description.
    """
    prompt = _generate_description_prompt(user_prompt)
    llm_model = LlamaModel()
    llm_model.load_llama_model()    
    answer = llm_model.generate_non_streaming_response(prompt)
    description = answer
    logger.info(f"Generated description: {description}")
    return description
