import inspect

class Toolkit: 

    def __init__(self): 
        
        self.tool_dict = {} 

    def add_tool(self, func, tool_name: str, tool_desc: str):

        assert isinstance(func, type(lambda: None)), "func must be a function"

        self.tool_dict[tool_name] = {'func': func, 'desc': tool_desc, 'source': inspect.getsource(func)} 