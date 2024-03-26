import requests 
import json   

# dotenv 
import os 
from dotenv import load_dotenv
load_dotenv()

# local 
from marshall.core.llm import LLM

class GPT(LLM): 

    def __init__(self, model_name: str, config={}, sys_instructions=None) -> None: 

        super().__init__(model_name, config if config is not None else {}) 

        self.api_key = os.getenv("OPENAI_API_KEY") 
        assert self.api_key is not None, "No api key found, make sure you have an environment variable called 'OPENAI_API_KEY'"
        
        self.completion_url = "https://api.openai.com/v1/chat/completions"  
        self.embedding_url = "https://api.openai.com/v1/embeddings"
        self.system_instructions = []   

        if sys_instructions: 
            self.add_sys_instructions(sys_instructions)

    def api_call(self, payload: dict, url: str) -> dict:  
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"  
            }
        
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

    def add_sys_instructions(self, instructions: str):  

        if instructions: self.system_instructions.append({"role": "system", "content": instructions}) 
    
    def add_user_message(self, mssg: str):  

        if mssg: self.system_instructions.append({"user": "system", "content": mssg})

    def generate(self, prompt: str) -> dict:

        p = {
            "model": self.model_name,
            "messages": self.system_instructions + [{"role": "user", "content": prompt}],
        }   

        if self.config.get('json', False): 
            # json=True is just for convenience, actual format is added below
            del self.config['json']   

            # restricting output type to json 
            self.config.update({"response_format": {'type': 'json_object'}})

        p.update(self.config)

        payload = json.dumps(p)  

        response = self.api_call(payload=payload, url=self.completion_url) 
        if 'choices' not in response: 
            return {'success': False, 'message': None, 'response': response} 
        
        return {'success': True, 
                'message': response['choices'][0]['message']['content']}
