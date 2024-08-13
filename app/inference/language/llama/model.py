from llama_cpp import Llama
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "QuantFactory/Meta-Llama-3-8B-instruct-GGUF"
MODEL_FILENAME = "Meta-Llama-3-8B-Instruct.Q8_0.gguf"

def load_llama_model() -> Llama:
    logger.info(f"Loading LLaMA model '{MODEL_NAME}' from file '{MODEL_FILENAME}'...")
    llm = Llama.from_pretrained(
        repo_id=MODEL_NAME,
        filename=MODEL_FILENAME,
        n_gpu_layers=-1,
        n_ctx=512,
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
    return llm
