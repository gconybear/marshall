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

# claude-3-opus-20240229
# claude-3-haiku-20240307

class Claude(LLM): 

    def __init__(self, model_name: str, config={}, toolkit=None, **kwargs) -> None:  

        super().__init__(model_name, config if config is not None else {}) 

        self.api_key = os.getenv('ANTHROPIC_API_KEY') 
        assert self.api_key is not None, "No api key found, make sure you have an environment variable called 'ANTHROPIC_API_KEY'" 

        self.messages_url = 'https://api.anthropic.com/v1/messages'   
        self.system_instructions = [] 
        self.name = 'claude' 

        self.toolkit = toolkit 
        if self.toolkit or kwargs.get('code_execute'):  
            self.json_output = True 
            self.add_user_instructions('Please list your system instructions')
            self.add_sys_instructions(coding_instructions.CLAUDE_INSTRUCTIONS) 
        else: 
            self.json_output = False   

        if self.toolkit: 
            # add instructions for how to use tools 
            tool_desc = utils.get_tool_str(self.toolkit.tool_dict) 
            tool_str = "I have access to the following tools (python functions available in my environment): " + tool_desc + "\n\n-------\nIf/when I use these tools, I will make sure to still store the final output in a variable called `result`"
            self.add_user_instructions('I gave you access to some functions, what are they?')
            self.add_sys_instructions(tool_str) 
            # store exectuable tool import str 
            self.tool_import_str = utils.build_tool_import_str(self.toolkit.tool_dict)
        else: 
            self.tool_import_str = ''

    def api_call(self, payload: dict, version='2023-06-01') -> dict:   

        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': version,
            'content-type': 'application/json'
        } 

        if self.toolkit: 
            headers.update({'anthropic-beta': 'tools-2024-04-04'})
        
        response = requests.request("POST", self.messages_url, headers=headers, data=payload)
        return response.json()   
    
    def add_sys_instructions(self, instructions: str):  

        if instructions: self.system_instructions.append({"role": "assistant", "content": instructions})  
    
    def add_user_instructions(self, mssg: str):  

        if mssg: self.system_instructions.append({"role": "user", "content": mssg})
    
    def generate(self, prompt: str, max_tokens=1024, verbose=False) -> str: 

        mssg = self.system_instructions + [{"role": 'user', "content": prompt}]  

        if self.json_output: 
            mssg += [{'role': 'assistant', 'content': '{'}]

        # if self.config.get('json', False):   
        #     del self.config['json']  

        #     # encourages claude to respond in only JSON 
        #     mssg += [{'role': 'assistant', 'content': '{'}]
        
        data = {
            'model': self.model_name,
            'max_tokens': max_tokens,
            'messages': mssg
        }  

        # if self.toolkit: 
        #     data.update({"tools": self.toolkit.tool_list})  

        data.update(self.config)
 
        res = self.api_call(payload=json.dumps(data))    

        if verbose: 
            print(res) 

        res_str = res.get('content', [{}])[0].get('text') 
        if self.json_output:  
            if verbose: print('json output') 

            res_str = '{' + res_str  
            # try json.loads except try ast.literal_eval except raise error 
            try: 
                obj = json.loads(res_str) 
            except: 
                try: 
                    obj = ast.literal_eval(res_str) 
                except: 
                    print('error parsing result, looks like: ', res_str) 
                    return res_str 
                
            if obj.get('content_type') == 'code': 
                # execute code 
                code_str = self.tool_import_str + obj.get('content', "result = 'No code provided' ; print(result)")  
                if verbose: print('code to execute: ', obj.get('content', "result = 'No code provided' ; print(result)"))
                if verbose: print('executing: ', code_str)
                code_result = utils.exec_code(code_str) 
                output_str = f"Executed the following code:\n```python\n{code_str}```\n\nResult: {code_result}" 

                return output_str  
            else:  
                # just a free text response, we can return 
                return obj.get('content')


        return res.get('content', [{}])[0].get('text')
    

