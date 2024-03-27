import requests 
import json   

# dotenv 
import os 
from dotenv import load_dotenv
load_dotenv()


# local 
from marshall.core.llm import LLM  

# claude-3-opus-20240229
# claude-3-haiku-20240307


class Claude(LLM): 

    def __init__(self, model_name: str, config={}, sys_instructions=None) -> None:  

        super().__init__(model_name, config if config is not None else {}) 

        self.api_key = os.getenv('ANTHROPIC_API_KEY') 
        assert self.api_key is not None, "No api key found, make sure you have an environment variable called 'ANTHROPIC_API_KEY'" 

        self.messages_url = 'https://api.anthropic.com/v1/messages'   
        self.system_instructions = [] 
        self.name = 'claude'

    def api_call(self, payload: dict, version='2023-06-01') -> dict:   
        

        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': version,
            'content-type': 'application/json',
        }
        
        response = requests.request("POST", self.messages_url, headers=headers, data=payload)
        return response.json()   
    
    def add_sys_instructions(self, instructions: str):  

        if instructions: self.system_instructions.append({"role": "assistant", "content": instructions})  
    
    def add_user_instructions(self, mssg: str):  

        if mssg: self.system_instructions.append({"role": "user", "content": mssg})
    
    def generate(self, prompt: str, max_tokens=1024, verbose=False) -> str: 

        mssg = self.system_instructions + [{"role": 'user', "content": prompt}] 

        if self.config.get('json', False):   
            del self.config['json']  

            # encourages claude to respond in only JSON 
            mssg += [{'role': 'assistant', 'content': '{'}]
        
        data = {
            'model': self.model_name,
            'max_tokens': max_tokens,
            'messages': mssg
        }  

        data.update(self.config)

        res = self.api_call(payload=json.dumps(data))   

        if verbose: 
            print(res)

        return res.get('content', [{}])[0].get('text')
    

