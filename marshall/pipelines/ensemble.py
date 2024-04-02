import copy

from marshall.tools.embed import embed_text  
from marshall.core.llm import LLM

def euclidean_distance(vec1, vec2):
    """Compute the Euclidean distance between two vectors."""
    return sum((p - q) ** 2 for p, q in zip(vec1, vec2)) ** 0.5

class HomogeneousEnsemble: 

    def __init__(self, base_agents: LLM, num_base_agents: int, refinement_strategy='similarity', toolkit=None, **kwargs):   

        """
        Homogenous Ensemble Agent
        -------- 

        uses N (homogenous) agents to generate N sample answers, which is then refined by either a similarity or agent-based refinement strategy 

        - similarity: compute all cross-similarity (euclidean dist on embeddings) scores for each sampled answer and choose argmin 

        - agent-based: a refined agent (a copy of the base agent) is tasked with distilling the sampled answers
        """

        assert refinement_strategy in ['similarity', 'agent'], "refinement_strategy must be one of 'similarity', 'agent'"

        self.base_agents = base_agents 
        self.base_agents.config.update({'temperature': 1.}) # temp needs to be set high to get diverse answers

        self.num_base_agents = num_base_agents 
        self.refinement_strategy = refinement_strategy 
        if self.refinement_strategy == 'agent':  
            # Check if 'refinement_agent' is provided in kwargs when refinement_strategy is 'agent'
            if 'refinement_agent' not in kwargs: 
                raise ValueError("When refinement_strategy is 'agent', a 'refinement_agent' must be provided in kwargs")
            self.refiner_agent = kwargs['refinement_agent']
        else: 
            self.refiner_agent = None

        self.toolkit = toolkit
        if self.toolkit:  
            if self.toolkit: 
                tool_instructions = f"""\n\nYou also have access to the following tools (python functions available in your environment), use these as needed whenever you want: \n\n{self.get_tool_str(self.toolkit.tool_dict)}\n--------\n\nIf you choose to make decision == "code_execute", you may use these functions in your code and can assume they are aleady available in the global namespace."""
    
    def similarity_refinement(self, answers: list[str]):
        
        """
        Employs a similarity ranking strategy like in "More Agents Is All You Need": https://arxiv.org/pdf/2402.05120.pdf

        Algorithm:
        - For each answer in list, compute embedding.
        - For each embedding, get similarity (Euclidean) to all other embeddings.
        - Return the answer with the embedding with the highest average similarity.
        """

        # Step 1: Compute embeddings for each answer
        embeddings = [embed_text(answer) for answer in answers]

        # Step 2 & 3: Compute pairwise Euclidean distances and average them
        avg_similarities = []
        for i, emb_i in enumerate(embeddings):
            distances = []
            for j, emb_j in enumerate(embeddings):
                if i != j:
                    # Calculate Euclidean distance
                    dist = euclidean_distance(emb_i, emb_j)
                    # Invert the distance to represent similarity; smaller distances mean higher similarity
                    similarity = -dist
                    distances.append(similarity)
            avg_similarities.append(sum(distances) / len(distances))

        # Step 4: Find the answer with the highest average similarity (least distance)
        max_avg_sim_index = avg_similarities.index(max(avg_similarities))
        return answers[max_avg_sim_index]

    def run(self, query: str, verbosity=0) -> str:  

        """
        - pass query to self.num_base_agents base agents with temperature = 1
        - (maybe) provide few shot examples about how to break a task down 
        - store responses in scratchpad and pass to refiner agent for final answer 
        """ 

        # 1. gather responses from LLMs
        responses = ""  
        list_responses = []
        for i in range(self.num_base_agents): 
            ans = self.base_agents.generate(query)  
            list_responses.append(ans)
            responses += f"\nAgent {i+1}: {ans}\n\n---------"  
            if verbosity > 0: print(f'agent {i+1} answered') 
            if verbosity > 1: print(ans)

        self.responses = responses    

        # 2. refine 
        if self.refinement_strategy == 'similarity':  
            if verbosity > 0: print('refining via similarity')
            return self.similarity_refinement(list_responses)
        
        if self.refinement_strategy == 'agent': 
            if verbosity > 0: print('refining through agent')

            if self.refiner_agent.name == 'claude': 
                # user message needs to be first with claude calls 
                self.refiner_agent.add_user_instructions(mssg=query) 

            self.refiner_agent.add_sys_instructions(f"Below is the output of {self.num_base_agents} agents to the query: {query}\n\n{responses}\n\nBased on these outputs and the original query, please provide a clear and concise answer to the original query. Make sure your answer is not just a summary of the above outputs, but an actual answer to the original question.") 

            final_answer = self.refiner_agent.generate(f"Given the query **{query}** and above outputs, provide the most helpful response for the user.")

            return final_answer 
        
        return None
