# Marshall - a generalized lightweight framework for orchestrating AI agents and sub-agents 

--------

Research has shown that many AI applications can benefit from 1) encouraging the underlying LLMs to employ Chain-of-Thought (CoT) reasoning and 2) equipping LLM pipelines with external tools. `Marshall` implements a simple pipeline that starts with a task/query passed to an agent. The agent (and any downstream agent – the process is recursive) has three options:

- `dispatch`: break task town into a series of sub-tasks that are passed to sub-agents
- `answer`: directly answer the question 
- `code_execute`: write and execute some arbitrary code

The process runs recursively until all tasks/sub-tasks are completed – all intermediary results are stored in a single string which is finally passed into a *refiner* agent which is simply tasked with summarzing all the work done to provide a cohesive answer to the users original question. 

------- 

## Example




------ 

## Running Locally 


1. Clone repo and stand up virtual env 
2. `pip install -r requirements.txt` 
3. `pip install -e .` 
4. Run a task:  

```python
from marshall.core.agent import Agent 
from marshall.core.tools import Toolkit # holds user-defined tools 
from marshall.llms.gpt import GPT # gpt class  

# define some tools 
def large_number_adder(a, b):
    return a + b  

def multipler(a, b):
    return a * b 

tk = Toolkit() 
tk.add_tool(
    func=large_number_adder,
    tool_name='large_number_adder',
    tool_desc='Adds two large numbers. Use like large_number_adder(a=1, b=2)',
) 
tk.add_tool(
    func=multipler,
    tool_name='multipler',
    tool_desc='Multiplies two numbers. Use like multipler(a=1, b=2)',
)

task = "..."  

ag = Agent(
    base_model=GPT(model_name="gpt-4-0125-preview", 
         api_key=os.getenv("OPENAI_API_KEY"), 
         config={"temperature": 0.2, "response_format": {'type': 'json_object'}}), 
    subagent_model=GPT(model_name="gpt-3.5-turbo-0125", 
         api_key=os.getenv("OPENAI_API_KEY"), 
         config={"temperature": 0.2, "response_format": {'type': 'json_object'}}), 
    refiner_model=GPT(model_name="gpt-3.5-turbo-0125", 
         api_key=os.getenv("OPENAI_API_KEY"), 
         config={"temperature": 0.2, "response_format": {'type': 'json_object'}}), 
    toolkit=tk
) 



```


