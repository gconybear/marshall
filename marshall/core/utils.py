import io 
import contextlib 

def exec_code(code: str):
    # Redirect stdout to capture the output of exec
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        exec(code)
        # Get the output from the buffer
        output = buf.getvalue()
    return output