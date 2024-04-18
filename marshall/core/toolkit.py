import inspect

class Toolkit: 

    def __init__(self): 
        
        self.tool_dict = {} 

    def add_tool(self, func, tool_desc: str):

        assert isinstance(func, type(lambda: None)), "func must be a function"

        self.tool_dict[func.__name__] = {'func': func, 'desc': tool_desc, 'source': inspect.getsource(func)} 