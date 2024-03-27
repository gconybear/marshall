class HomogeneousEnsemble: 

    def __init__(self, base_agents, refiner_agent, num_base_agents: int): 

        self.base_agents = base_agents 
        self.base_agents.config.update({'temperature': 1.}) # temp needs to be set high to get diverse answers

        self.num_base_agents = num_base_agents 
        self.refiner_agent = refiner_agent   
    
    def similarity_refinement(self, answers: list[str]): 
        return None

    def run(self, query: str, verbose=False) -> str:  

        """
        - pass query to self.num_base_agents base agents with temperature = 1
        - (maybe) provide few shot examples about how to break a task down 
        - store responses in scratchpad and pass to refiner agent for final answer 
        """ 

        responses = "" 
        for i in range(self.num_base_agents): 
            ans = self.base_agents.generate(query) 
            responses += f"\nAgent {i+1}: {ans}\n\n---------"  
            if verbose: print(f'agent {i} answered')

        self.responses = responses   

        if self.refiner_agent.name == 'claude': 
            # user message needs to be first 
            self.refiner_agent.add_user_instructions(mssg=query) 

        self.refiner_agent.add_sys_instructions(f"Below is the output of {self.num_base_agents} agents to the query: {query}\n\n{responses}\n\nBased on these outputs and the original query, please provide a clear and concise answer.")
        final_answer = self.refiner_agent.generate(f"Given the query **{query}** and above outputs, provide the most helpful response for the user.")

        return final_answer
