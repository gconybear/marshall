class LLM:

    def __init__(self, model_name: str, api_key=None, config={}) -> None:
        
        self.model_name = model_name
        self.api_key = api_key
        self.config = config

    def generate(self, prompt: str): 
        raise NotImplementedError("This method should be implemented by subclasses.")

