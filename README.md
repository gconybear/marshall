# Marshall – frameworks for orchestrating AI agents 

![Marshall](marshall/assets/marshall_dalle.png) 

-------- 

## Motivation

[Research](https://arxiv.org/abs/2201.11903) [has](https://arxiv.org/abs/2402.05120) [shown](https://arxiv.org/abs/2309.07864) that many AI applications can benefit from 1) encouraging the underlying LLMs to employ Chain-of-Thought (CoT) reasoning and 2) equipping LLM pipelines with external tools. 

`Marshall` is an orchestration framework for building multi-agent LLM pipelines. 


Currently, the following pipelines are built out: 

- Delegation: A task/query is passed to a base agent. The agent (and any downstream agent – the process is recursive) has two options: `dispatch` (break the problem into steps and assign to sub-agents) or `answer` (provide direct response). 
- Homogeneous Ensemble: A task/query is passed to N separate agents who each provide a response. If `refinement_strategy` is set to "similarity", the response with the highest cross-similarity (euclidean distance) is chosen. If `refinement_strategy` == 'agent', all the responses are passed to a user-defined agent that is tasked with distilling the responses into a cohesive final output. 


------- 

## Example

#### Running Locally 


1. Clone repo and stand up virtual env 
2. `pip install -r requirements.txt` 
3. `pip install -e .` 
4. Run a task:  

```python
from marshall.core.pipelines import enemble, delegation  
from marshall.llms import gpt, claude # gpt and claude are both supported  
from marshall.core.tools import Toolkit # class that holds user-defined tools 

# define some tools 
def large_number_adder(a, b):
    return a + b  

def multipler(a, b):
    return a * b 

def random_joke(): 

    import requests

    response = requests.get('https://official-joke-api.appspot.com/jokes/random')
    joke = response.json() 

    return f"{joke.get('setup')} {joke.get('punchline')}"

tk = Toolkit()  

tk.add_tool(
    func=large_number_adder,
    tool_desc='Adds two large numbers. Use like large_number_adder(a=1, b=2)',
) 
tk.add_tool(
    func=multipler,
    tool_desc='Multiplies two numbers. Use like multipler(a=1, b=2)',
) 
tk.add_tool(
    func=random_joke, 
    tool_desc="returns a joke (string)"
)


task = "..."  


```


TODO

- [ ] build out delegation pipeline 
- [ ] expand toolkit for use in with any LLM class 
- [ ] rag func examples 


