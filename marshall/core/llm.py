class LLM:

    def __init__(self, model_name: str, config={}) -> None:
        
        self.model_name = model_name
        self.config = config

    def generate(self, prompt: str): 
        raise NotImplementedError("This method should be implemented by subclasses.")

