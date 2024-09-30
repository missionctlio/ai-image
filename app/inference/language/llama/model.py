from llama_cpp import Llama
import logging
from app.utils.conversational_memory import ConversationalMemory

class LlamaModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LlamaModel, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if hasattr(self, 'initialized') and self.initialized:
            return  # Skip initialization if already done
        self.logger = logging.getLogger(__name__)
        self.model_name = "hugging-quants/Llama-3.2-3B-Instruct-Q8_0-GGUF"
        self.model_filename = "llama-3.2-3b-instruct-q8_0.gguf"
        self.llm = None
        self.redis_client = None  # Initialize redis_client later with conversation_id
        self.initialized = True

    def set_conversation_id(self, conversation_id: str):
        """Set the conversation ID and initialize the ConversationalMemory."""
        self.redis_client = ConversationalMemory(conversation_id)

    def load_llama_model(self):
        """
        Loads and initializes a pre-trained LLaMA model with the specified configuration.
        """
        if self.llm is None:  # Check if model is already loaded
            self.logger.info(f"Loading LLaMA model '{self.model_name}' from file '{self.model_filename}'...")
            self.llm = Llama.from_pretrained(
                repo_id=self.model_name,
                filename=self.model_filename,
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

    def generate_streaming_response(self, prompt: str, conversation_id: str) -> iter:
        """
        Generates a streaming response from the model based on the provided prompt.

        :param prompt: The prompt to send to the model.
        :param conversation_id: The unique identifier for the conversation.
        :return: A generator that yields cleaned chunks as they arrive.
        """
        if self.llm is None:
            self.load_llama_model()
        
        # Set or update the conversation ID
        self.set_conversation_id(conversation_id)
        
        if self.redis_client is None:
            raise ValueError("Conversation ID not set. Use set_conversation_id() to initialize.")
        
        self.logger.info("Streaming Chat")
        full_response = []
        response_stream = self.llm.create_chat_completion(
            messages=prompt,
            stream=True
        )
        for chunk in response_stream:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta:
                content = delta['content']
                full_response.append(content)
                yield content
        full_response_str = ''.join(full_response)
        self.redis_client.append_to_memory(full_response_str)

    def generate_non_streaming_response(self, prompt: str) -> str:
        """
        Generates a non-streaming response from the model based on the provided prompt.

        :param prompt: The prompt to send to the model.
        :return: The response content from the model.
        """
        if self.llm is None:
            self.load_llama_model()
        answer = self.llm.create_chat_completion(
            messages=prompt,
        )
        response_content = answer['choices'][0]['message']['content']
        return response_content
