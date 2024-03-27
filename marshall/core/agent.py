# an agent is a process that runs a single task
# a task comes with pre-defined inputs and outputs 
import json 

# class DelegationAgent
class Agent:

    def __init__(self, base_model, subagent_model, refiner_model, toolkit=None):  

        """
        base_agent: initial agent task is passed to 
        subagent: agent that is spawned when a task is dispatched 
        refiner: agent applied to final output to summarize and provide a final response 
        toolkit (optional): a toolkit dict (needs `tool_dict` method) that is given to all agents in order to run tools
        """

        self.base_model = base_model
        self.subagent_model = subagent_model 
        
        # base and subagent models need to return json 
        self.base_model.config.update({'json': True}) 
        self.subagent_model.config.update({'json': True})

        self.refiner_model = refiner_model   
        self.toolkit = toolkit  

        self.current_agent = self.base_model  

        self.result_log = "" 
        self.logging = []

        # add general sys instructions to all agents
        instructions = f"""You are a highly intelligent AI agent who also has an army of sub-agents at your disposal. Your sole objective is to comprehensively answer a question/solve a problem provided to you. You may choose to answer the question directly (and optionally through the execution of code), or dispatch the task to your suite of sub-agents. Think deeply about the problem and then make your decision. ONLY dispatch when absolutely needed and when the task can be better fulfilled by breaking it down step by step into multiple chains of reasoning. 

        More concretely, you have three options:

        - "dispatch": send task to subagent
        - "answer": answer the question/task directly
        - "code_execute": execute code  

        You MUST return a JSON object with the following structure: 

        - `decision`: a str of the decision you made – one of "dispatch", "answer", or "code_execute"
        - `content`: If decision == "dispatch", then this is a list of strings where each string is a clear and comprehensive instruction for a subagent to follow. If decision == "answer", then this is a string that is the direct answer to the user's question. If decision == "code_execute", then this is a executable code in the form of a python string – the code **MUST** store the final result in a variable called `result`. It is crucial that the code execution output be in a variable called `result`! DO NOT FORGET.
        """ 

        if self.toolkit: 
            instructions += f"""\n\nYou also have access to the following tools (python functions available in your environment), use these as needed whenever you want: \n\n{self.get_tool_str(self.toolkit.tool_dict)}\n--------\n\nIf you choose to make decision == "code_execute", you may use these functions in your code and can assume they are aleady available in the global namespace."""  

        # instructions go to base and sub agents 
        self.base_model.add_sys_instructions(instructions) 
        self.subagent_model.add_sys_instructions(instructions)

    
    def get_tool_str(self, tool_dict: dict): 

        tool_str = ""
        for tool_name, tool_details in tool_dict.items(): 
            tool_str += f"Name: {tool_name}\nDescription: {tool_details.get('desc', '')}\nSource:\n```python\n{tool_details.get('source', '')}```\n\n" 

        return tool_str
    
    def build_tool_import_str(self, tk: dict) -> str: 
        """
        builds a python string that imports all tools in the toolkit
        """

        code = ""
        for fname, fdetails in tk.items():
            code += f"# {fname}\n"
            description = fdetails['desc'].replace('\n', '')
            code += f"# {description}\n"
            source = fdetails['source']
            code += f"{source}\n\n"

        return code 
    
    def make_decision1(self, task: str, agent='base'):  

        """
        protocol: 

        1. task is passed in 
        2. self.result_log contains previous info 
        - if no prev agent, just user task and sys instructions 
        - if prev agent: 
            - (meta task, current task, result, next task) for each step 

        """
        out = {}  
        log_separator = "\n--------\n"

        if agent == 'base':
            self.current_agent = self.base_model  
        else:
            self.current_agent = self.subagent_model 

        # append prev results to sys history 
        if self.result_log: 
            self.current_agent.add_sys_instructions("**RESULT LOG**\n\n" + self.result_log + log_separator)  

        # now, we need to chop off middle part of sys instructions 
        refined_instructions = [self.current_agent.system_instructions[0], self.current_agent.system_instructions[-1]] 
        self.current_agent.system_instructions = refined_instructions

        # generate decision 
        print('about to generate')
        res = self.current_agent.generate(task)   
        print('generated')
        mssg = json.loads(res['message'])
        
        decision = mssg['decision'] 

        assert decision in ('dispatch', 'code_execute', 'answer'), f"Agent decision needs to be one of 'dispatch', 'code_execute', 'answer' – got {decision}"  

        ########

        if decision == "answer":
            out['success'] = True 
            out['message'] = f"The task was: {task}\n\nThe answer provided was: {mssg['content']}" 
            out['done'] = True 

            self.result_log += f"Directive: {task}\nResult: {mssg['content']}" + log_separator

        elif decision == "code_execute": 
            # execute code  
            tool_imports = self.build_tool_import_str(self.toolkit.tool_dict)  
            print("code to be run: ", mssg['content'])
            code_str = tool_imports + mssg['content']
            
            namespace = {} 
            exec(code_str, namespace)  
            result = namespace.get('result', None)

            if result: 
                out['success'] = True
            else: 
                out['success'] = False  

                print('code execution failed... trying again') 

                revised_task = f"The following code execution (for the task {task}) did NOT work: {code_str}\n\nPlease try again and remember to store the final output in a variable called `result`)." 
                self.make_decision1(task=revised_task, agent='sub')

            out['message'] = f"The task was: {task}\n\nThe following code was executed: \n\n{code_str}\n\nThe result was: {result}" 

            out['done'] = True  

            self.result_log += f"Directive: {task}\nProcess: executed the following code ```python\n{mssg['content']}\n```\nResult: {result}" + log_separator

        # else, task was dispatched 
        else:
            out['success'] = True
            out['message'] = mssg['content']
            out['done'] = False  

            self.result_log += f"Directive: {task}\nResult: dispatched the following sub-tasks – {', '.join(mssg['content'])}" + log_separator

        return out 

    def make_decision(self, task, agent='base'): 

        """
        agent can make decision to either `dispatch`, `answer`, or `code_execute`

        dispatch: agent sends task to subagent
        answer: agent answers the task
        code_execute: agent executes code
        """  

        if agent == 'base':
            self.current_agent = self.base_model  
        else:
            self.current_agent = self.subagent_model   

        if self.result_log: 
            self.current_agent.add_sys_instructions("You have received the following previous inputs from other agents to aid in your decision making:\n\n" + self.result_log + "\n\n--------\n\n")


        res = self.current_agent.generate(task)  
        mssg = json.loads(res['message'])
        
        decision = mssg['decision']  

        out = {} # final out with 'success', 'message', 'done' keys
        if decision == "dispatch":  
            
            # set current agent subagent 
            out['success'] = True
            out['message'] = mssg['content']
            out['done'] = False  

            self.result_log += 'The following sub-tasks were dispatched: ' + ', '.join(out['message']) + "\n\n--------\n\n"  

            out['message'] = [f"Your sub-task is: " + x for x in mssg['content']] # just the list of str instructions with meta task concatenated on 

        if decision == "code_execute": 
            # execute code  
            tool_imports = self.build_tool_import_str(self.toolkit.tool_dict)  
            print("code to be run: ", mssg['content'])
            code_str = tool_imports + mssg['content']
            
            namespace = {} 
            exec(code_str, namespace)  
            result = namespace.get('result', None)

            if result: 
                out['success'] = True
            else: 
                out['success'] = False 

            out['message'] = f"The task was: {task}\n\nThe following code was executed: \n\n{code_str}\n\nThe result was: {result}" 

            out['done'] = True  

            self.result_log += out['message'] + "\n\n--------\n\n" 

        if decision == "answer":
            out['success'] = True 
            out['message'] = f"The task was: {task}\n\nThe answer provided was: {mssg['content']}" 
            out['done'] = True
        
            self.result_log += out['message'] + "\n\n--------\n\n"  

        self.logging.append(out)

        # final result object: dict with 'success' key, 'message' key, 'done' key 
        return out   
    
    def build_log(self, task: str, subagents=False):  

        print(f"The following task came in: {task}")

        done = False  
        current_task = task 
        while not done: 

            res = self.make_decision1(task=current_task, agent='base' if not subagents else 'sub') 
            print(f"Got result. Done={res.get('done')} | Success={res.get('success')} | Content={res.get('message')}")

            if not res.get('done', True): 
                # subtasks are a list of strings under `message` key 
                subtasks = res['message'] 
                for t in subtasks: 
                    self.build_log(task=t, subagents=True)  

                done = True 
                break 
            else: 
                print('DONE') 
                done = True 
                break 
    
    def build_scratchpad(self, task, subagents=False): 

        """
        this function receives a task and then recursively builds a scratchpad that's passed to the refiner agent
        """  

        SEPARATOR = "\n\n--------\n\n" 
        scratchpad = ""

        done = False 
        while not done: 

            res = self.make_decision(task=task, agent='sub' if subagents else 'base') # returns dict with 'success', 'message', 'done' keys 
            if res['done']: 
                print("done")
                done = True   
                scratchpad += res['message'] + SEPARATOR
                break 
            else: 
                # we need to dispatch the list of sub-tasks to subagents 
                tasks = res['message'] # list of str tasks   
                print("tasks: ", tasks)
                for t in tasks: 
                    sub_scratchpad = self.build_scratchpad(t, subagents=True) 
                    scratchpad += sub_scratchpad  
                
                done = True 
                break 

        return scratchpad

            

        

        

