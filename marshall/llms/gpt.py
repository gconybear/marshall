import requests 
import json   
import ast 

# dotenv 
import os 
from dotenv import load_dotenv
load_dotenv()

# local 
from marshall.core.llm import LLM
from marshall.core import utils
from marshall.prompts import coding_instructions

class GPT(LLM): 

    def __init__(self, model_name: str, config={}, sys_instructions=None, toolkit=None, **kwargs) -> None: 

        super().__init__(model_name, config if config is not None else {}) 

        self.api_key = os.getenv("OPENAI_API_KEY") 
        assert self.api_key is not None, "No api key found, make sure you have an environment variable called 'OPENAI_API_KEY'"
        
        self.completion_url = "https://api.openai.com/v1/chat/completions"  
        self.embedding_url = "https://api.openai.com/v1/embeddings"
        self.system_instructions = []    
        self.name = 'chatgpt'

        if sys_instructions: 
            self.add_sys_instructions(sys_instructions) 

        self.toolkit = toolkit 
        if self.toolkit or kwargs.get('code_execute'): 
            self.json_output = True 
            self.add_sys_instructions(coding_instructions.INSTRUCTIONS)
        else: 
            self.json_output = False

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

    def generate(self, prompt: str, verbose=False) -> dict:

        p = {
            "model": self.model_name,
            "messages": self.system_instructions + [{"role": "user", "content": prompt}],
        }   

        if self.json_output: 
            # restricting output type to json 
            self.config.update({"response_format": {'type': 'json_object'}})

        p.update(self.config)

        payload = json.dumps(p)  

        response = self.api_call(payload=payload, url=self.completion_url) 
        if 'choices' not in response:  
            return None
            #return {'success': False, 'message': None, 'response': response}   
        
        if self.json_output: 
            # result will be a JSON string, we want to parse it and execute code if necessary
            if verbose: print('json output')  
            res_str = response['choices'][0]['message']['content']
            try: 
                obj = json.loads(res_str) 
            except: 
                try: 
                    obj = ast.literal_eval(res_str) 
                except: 
                    print('error parsing result, looks like: ', res_str) 
                    return None 
                
            if obj.get('content_type') == 'code': 
                # execute code 
                if verbose: print('executing: ', obj.get('content'))
                code_result = utils.exec_code(obj.get('content')) 
                output_str = f"Executed the following code:\n```python\n{obj.get('content')}```\n\nResult: {code_result}" 

                return output_str  
            else:  
                # just a free text response, we can return 
                return obj.get('content')
        
        return response['choices'][0]['message']['content']
        
        # return {'success': True, 
        #         'message': response['choices'][0]['message']['content']}
