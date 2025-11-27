import json
import os
import re
import requests
from typing import Any
from tools import ToolBox


class Agent():
    def __init__(self, api_key:str, api_base:str, model_name:str,temperature:float):
    
        # Model Setting
        self.api_key=api_key
        self.api_base=api_base
        self.model_name=model_name
        self.temp=temperature

        self.calls=0
        

    def chain_of_thought(self, question:str, prompt_path:str, ):

        sub_answers=self.get_sub_answers(question)

        with open(prompt_path) as file:
            data = json.load()
            system = data['system']
            prompt = data['prompt']
            

    def self_refine(self):
        pass
    def react(self):
        pass

	# Shared Components

    def call_model(self,prompt: str, system: str,timeout: int = 60) -> dict[str, Any]:
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
                {"role": "user",   "content": prompt}
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
        

    def action(self,question:str):
        pass
     
    def detect_tool_call(self):
        pass


if __name__ == '__main__':

    question="""
    How many even integers between 4000 and 7000 have four different digits?
    """

    robotucus = Agent(
        api_key=os.getenv("OPENAI_API_KEY", "cse476"),
        api_base=os.getenv("API_BASE", "http://10.4.58.53:41701/v1"),
        model_name=os.getenv("MODEL_NAME", "bens_model"),
        temperature=0.0
    )

    print(question) 

    for q in robotucus.get_sub_questions(question):
        print(q)

    for entry in robotucus.action(question):
        print('\n============== Sub Questions ===========\n')

        print(entry['subq'],end='\n\n')

        print(entry['ans'])

    print('\n============== Final Answer ===========\n')

    print(robotucus.chain_of_thought(question))
    print(f'# Models Call: {robotucus.calls}')
