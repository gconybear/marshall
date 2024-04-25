import inspect

class Toolkit: 

    def __init__(self): 
        
        self.tool_dict = {}  
        self.tool_list = [] # for use with anthropic's api 

    def add_tool(self, func, tool_desc: str, input_dict: dict = {}, required_params: list = []): 

        """
        tool_desc: (str) a description of the tool
        input_dict: (dict) a dictionary with keys as param names and values as dict with (optional) keys 'type', 'description', 'enum'
        """

        assert isinstance(func, type(lambda: None)), "func must be a function"

        self.tool_dict[func.__name__] = {'func': func, 'desc': tool_desc, 'source': inspect.getsource(func)}  
        self.tool_list.append(
            {
                'name': func.__name__,
                'description': tool_desc,
                'input_schema': {
                    'type': 'object', 
                    'properties': input_dict, 
                    'required': required_params
                }, 
                
            }
        ) 