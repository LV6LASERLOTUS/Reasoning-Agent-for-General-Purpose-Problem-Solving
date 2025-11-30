import logging
import json
import os
import re
import requests
from typing import Any,List
from tools import search_wiki,search_browser


class Agent():
    def __init__(self, api_key:str, api_base:str, model_name:str,temperature:float):
    
        # Model Setting
        self.api_key=api_key
        self.api_base=api_base
        self.model_name=model_name
        self.temp=temperature

        # Track Model calls updates everytime call_model is called
        self.calls=0
    
    def self_refine(self, question:str, max_calls:int = 10)->str:
        
        #Load prompt
        system_refine_template=self.read_file("../prompts/self_refine/system_refine.txt")
        system_feedback_template=self.read_file("../prompts/self_refine/system_feedback.txt")

        score_pattern="([0-9]*/[0-9]*)"

        # Creating initial answer
        user_prompt = f"Question: {question}"
        response = self.call_model(user=user_prompt)

        for _ in range(max_calls-self.calls):

            print("============ Generating Feedback ==============")

            feedback = self.call_model(user=response["text"],system=system_feedback_template)

            if not feedback["text"]:
                return feedback.get("error")
            
            print(feedback["text"])

            # Check the score
            match = re.search(score_pattern, feedback["text"])
            if match and match.group(0)=="10/10":
                return feedback["text"]

            print("==================== Refining Answer =================")

            # Build the prompt fro refining
            system_refined = (
                f"{system_refine_template}"
                f"Given the feedback {feedback["text"]}\n\n"
                f"Refine the response below."
            )

            user_refined = (
                f"Orignal question: {question}"
                f"Your previous response:\n{response["text"]}"
            )

        
            response_refined = self.call_model(user=user_refined,system=system_refined)

            if not response_refined["text"]:
                return feedback.get("error")
            
            print(response_refined["text"])
            response=response_refined

        return feedback["text"]
        

    def react(self, question:str, max_calls:int = 20)->str:
        
        system_template = self.read_file('../prompts/react/system.txt')
        user_template = self.read_file('../prompts/react/user.txt')

        toolbox={
            'search_wiki':search_wiki,
            'search_browser': search_browser,
        }

        action_pattern=r"Action: (\w+)"
        input_pattern=r"Input: (.+)"
        

        user_prompt=question

        for _ in range(max_calls-self.calls):
            response = self.call_model(user_prompt, system=system_template)
            print(response["text"])
            if "Answer:" in response["text"]:
                return response["text"]
            
            action_match = re.search(action_pattern,response["text"])
            input_match = re.search(input_pattern,response["text"])

            if action_match:
                action_response = toolbox[action_match.group(1)](input_match.group(1))
                action_response = self.summarize_reasoning(str(action_response))
                print(f"\nObservation: {action_response}\n")
                user_prompt+=f"\nObservation: {action_response}"
                continue

            previous_response = self.summarize_reasoning(response["text"])
            user_prompt=f"\nPrevious response: {previous_response}"
            
        return "Answer wasn't reach in <20 calls"



            
        # Get action response



    def chain_of_thought(self, question:str, max_calls:int = 20)->str:
        """Utilizes ITerative Chain Reasoning"""

        #Load prompt
        system_template=self.read_file('../prompts/chain_of_thought/system.txt')
        
        #Create initial prompt
        user = f"Please solve the following problem step-by-step:\n\nQuestion:{question}"
        chat_log=[]

        for i in range(max_calls-self.calls):
            
            print(f"=========================== Prompt =====================")
            print(user)
            response = self.call_model(user,system_template)

            if not response['text']:
                return response.get("error")
        
            print(f"=========================== {i} =====================")
            print(response["text"])
            
            if "Answer" in response["text"]:
                return response["text"]

            chat_log.append(self.summarize_reasoning(response["text"]))

            user = f"Question: {question}\n\nPrevious Reasoning:\n\n{''.join(chat_log)}"

        return response["text"]
    
    
    # Shared Components

    def call_model(self, user:str="", system:str="", timeout:int = 30) -> dict[str, Any]:
        """
        Calls an OpenAI-style /v1/chat/completions endpoint and returns:
        { 'ok': bool, 'text': str or None, 'raw': dict or None, 'status': int, 'error': str or None, 'headers': dict }
        """
        
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user}
            ],
            "temperature": self.temp,
            "max_tokens": 1024,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            status = response.status_code
            hdrs   = dict(response.headers)
            if status == 200:
                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                self.calls+=1
                return {"ok": True, "text": text, "raw": data, "status": status, "error": None, "headers": hdrs}
            else:
                # try best-effort to surface error text
                err_text = None
                try:
                    err_text = response.json()
                except Exception:
                    err_text = response.text
                return {"ok": False, "text": None, "raw": None, "status": status, "error": str(err_text), "headers": hdrs}
        except requests.RequestException as e:
            return {"ok": False, "text": None, "raw": None, "status": -1, "error": str(e), "headers": {}}

    def summarize_reasoning(self, chat_log:str)->str:
        """ Summarize the reasoning so far"""
        summary= self.call_model(
            chat_log,
            system="""
            You are Qwen, a highly skilled summarization assistant.

            Your task:
            - Summarize the reasoning provided in the user input into a concise, clear, and information-rich summary.
            - Preserve ALL important facts, intermediate results, and conclusions.
            - Maintain logical consistency so that future reasoning can continue accurately from this summary.
            - Omit redundant explanations, minor details, or repetitions.
            - Keep the summary short and token-efficient (under 150 tokens if possible).
            - Do NOT generate a final answer; only produce a summary of the reasoning steps.
            - Output should be in plain text, suitable for feeding as context to the next iteration of problem-solving.
            - Also include the number and task of the next step e.g. Next step: 10 Analyze the function
            """.strip()
        )    
        
        if not summary["text"]:
            return summary.get("error")

        return summary["text"]

    def read_file(self, path:str)->str:

        """Reads in txt given a path string"""
        try:
            with open(path, 'r') as file:
                content = file.read()
            return content
        
        except FileNotFoundError:
            logging.error(f'File not found at {path}')
            return None


if __name__ == '__main__':

    USER_PATH='../prompts/self_refine/user.txt'

    question=r"""
    In a new school, $40$ percent of the students are freshmen, $30$ percent are sophomores, $20$ percent are juniors, and $10$ percent are seniors. All freshmen are required to take Latin, and $80$ percent of sophomores, $50$ percent of the juniors, and $20$ percent of the seniors elect to take Latin. The probability that a randomly chosen Latin student is a sophomore is $\\frac{m}{n}$ , where $m$ and $n$ are relatively prime positive integers. Find $m+n$ .
    """
    #869
    
    robotucus = Agent(
        api_key=os.getenv("OPENAI_API_KEY", "cse476"),
        api_base=os.getenv("API_BASE", "http://10.4.58.53:41701/v1"),
        model_name=os.getenv("MODEL_NAME", "bens_model"),
        temperature=0.0
    )

    robotucus.react(question=question)
    # print(robotucus.self_refine(question=question))
    # print(robotucus.read_file(USER_PATH))
    # for q in robotucus.get_sub_questions(question):
    #     print(q)

    # for entry in robotucus.action(question):
    #     print('\n============== Sub Questions ===========\n')

    #     print(entry['subq'],end='\n\n')

    #     print(entry['ans'])

    # print('\n============== Final Answer ===========\n')

    # print(robotucus.chain_of_thought(question))
    # print(f'# Models Call: {robotucus.calls}')

