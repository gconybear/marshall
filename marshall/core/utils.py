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


# def exec_code(code: str):
#     # Redirect stdout to capture the output of exec
#     with io.StringIO() as buf, contextlib.redirect_stdout(buf):
#         exec(code)
#         # Get the output from the buffer
#         output = buf.getvalue()
#     return output 


