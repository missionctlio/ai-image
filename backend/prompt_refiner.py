# backend/prompt_refiner.py

from llama_cpp import Llama

import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define model cache directory
cache_dir = '/venv/models'
# Load the LLaMA-3 model and tokenizer
model_name = "QuantFactory/Meta-Llama-3-8B-instruct-GGUF"
llm = Llama.from_pretrained(
    repo_id=model_name,
    filename="Meta-Llama-3-8B-Instruct.Q8_0.gguf",
    n_gpu_layers=-1,
    n_ctx=8192,
    n_predict=-1,
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


def generate_prompt(prompt):
    prompt_content = f"prompt: {prompt}"
    system_content = "You are a prompt refiner for an online store creating humorous prompts for customers that generate images for a wide variety of prints like T-shirts, hoodies, coffee mugs and hats. The prompts you generate must never be more than 77 tokens."
    prompt = [
        {"role": "system", "content": system_content}, 
        {"role": "user", "content": prompt_content}
    ]
    logger.info(prompt)
    return prompt

def refine_prompt(user_prompt: str) -> str:
    answer = llm.create_chat_completion(
        messages=generate_prompt(user_prompt),
    )
    logger.info(answer['choices'][0]['message']['content'])
    return answer['choices'][0]['message']['content']