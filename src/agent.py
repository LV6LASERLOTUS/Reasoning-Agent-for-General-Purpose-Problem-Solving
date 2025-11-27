import logging
import json
import os
import re
import requests
from typing import Any
from tools import search_wiki,search_browser,execute_python


class Agent():
    def __init__(self, api_key:str, api_base:str, model_name:str,temperature:float):
    
        # Model Setting
        self.api_key=api_key
        self.api_base=api_base
        self.model_name=model_name
        self.temp=temperature

        # Track Model calls updates everytime call_model is called
        self.calls=0
    
    def self_refine(self):
        pass
    def react(self):
        pass

	# Shared Components

    def chain_of_thought(
        self, question:str, user_path:str
    )->str:

        #Load prompt
        system_path='../prompts/chain_of_thought/system.txt'

        system_template=self.read_file(system_path)
        user_template = self.read_file(user_path)
        
        #Create 
        user = f"{user_template}\n\nQuestion:{question}"
        result = self.call_model(user,system_template)

        if result['text'] is None:
            print(result)
            raise TimeoutError(result["error"])
        
        return result["text"]
    
    def call_model(self,user: str, system: str,timeout: int = 30) -> dict[str, Any]:
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
        
    def read_file(self,path:str):

        try:
            with open(path, 'r') as file:
                content = file.read()
            return content
        
        except FileNotFoundError:
            logging.error(f'File not found at {path}')
            return None

    def action(self,question:str):
        pass
     
    def detect_tool_call(self):
        pass


if __name__ == '__main__':

    USER_PATH='../prompts/chain_of_thought/user.txt'

    question=r"""
    Let $ABCD$ be a convex quadrilateral with $AB = CD = 10$ , $BC = 14$ , and $AD = 2\\sqrt\{65}$ . Assume that the diagonals of $ABCD$ intersect at point $P$ , and that the sum of the areas of triangles $APB$ and $CPD$ equals the sum of the areas of triangles $BPC$ and $APD$ . Find the area of quadrilateral $ABCD$ .
    """

    robotucus = Agent(
        api_key=os.getenv("OPENAI_API_KEY", "cse476"),
        api_base=os.getenv("API_BASE", "http://10.4.58.53:41701/v1"),
        model_name=os.getenv("MODEL_NAME", "bens_model"),
        temperature=0.0
    )

    print(question) 
    print(robotucus.chain_of_thought(question,USER_PATH))
    # for q in robotucus.get_sub_questions(question):
    #     print(q)

    # for entry in robotucus.action(question):
    #     print('\n============== Sub Questions ===========\n')

    #     print(entry['subq'],end='\n\n')

    #     print(entry['ans'])

    # print('\n============== Final Answer ===========\n')

    # print(robotucus.chain_of_thought(question))
    # print(f'# Models Call: {robotucus.calls}')

