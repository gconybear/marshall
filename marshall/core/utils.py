import io 
import contextlib 
import random
import math 

# def exec_code(code: str): 
#     namespace = {}
#     exec(code, namespace)

def exec_code(code):
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        # Include common libraries in the namespace for 'exec'
        namespace = {
            "__builtins__": __builtins__,
            "random": random,
            "math": math,
        }
        exec(code, namespace)
        output = buf.getvalue()
    return output 

def get_tool_str(tool_dict: dict) -> str: 

    tool_str = ""
    for tool_name, tool_details in tool_dict.items(): 
        tool_str += f"Name: {tool_name}\nDescription: {tool_details.get('desc', '')}\nSource:\n```python\n{tool_details.get('source', '')}```\n\n" 

    return tool_str 

def build_tool_import_str(tk: dict) -> str: 
    """
    builds an executable python string that imports all tools in the toolkit
    """

    code = ""
    for fname, fdetails in tk.items():
        code += f"# {fname}\n"
        description = fdetails['desc'].replace('\n', '')
        code += f"# {description}\n"
        source = fdetails['source']
        code += f"{source}\n\n"

    return code 


# def exec_code(code: str):
#     # Redirect stdout to capture the output of exec
#     with io.StringIO() as buf, contextlib.redirect_stdout(buf):
#         exec(code)
#         # Get the output from the buffer
#         output = buf.getvalue()
#     return output 


