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
        

    def chain_of_thought(self,question):

        sub_answers=self.get_sub_answers(question)

        system='''
        You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

        You are generating the final answer to the original problem.
        
        You must:
        - Think step-by-step internally, but DO NOT reveal chain-of-thought.
        - Use only the original question and the list of sub-answers.
        - Integrate the sub-answers into a unified, correct final answer.
        - Output only the final answer, concise and complete (<150 tokens).
        - Do NOT show your reasoning.
        - Keep your final answer atomic and exact.
        '''

        prompt=f'''
        Original question:
        {question}

        Here are the answers to all sub-questions:
        {sub_answers}

        Using these, synthesize the final answer. 
        Think step-by-step internally but DO NOT reveal your reasoning.
        Return only the final answer concisely (<150 tokens).
        Keep your final answer atomic and exact.
        '''

        answer=self.call_model(prompt=prompt,system=system)

        if answer['status'] != 200:
            return print(answer)
        
        return answer['text']

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

        sub_questions:list[str] = self.get_sub_questions(question)
        sub_answers:list[dict[Any]]=[]

        toolbox={
            'search_wiki':ToolBox().search_wiki,
            'search_browser':ToolBox().search_browser,
            'execute_python':ToolBox().execute_python
        }

        system=f'''
        You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

        You are selecting a tool and an input for answering a sub-question of a larger problem.

        Available tools:

        1. search_wiki
        - Use ONLY for direct fact checking lookups typically found on Wikipedia.
        - Input should be a short entity name or phrase.

        2. search_browser
        - Use ONLY for general web searches beyond Wikipedia.

        When calling a tool, use EXACTLY the format:

        Action: <one of [search_wiki, search_browser]>
        Action Input: <minimal string>

        Rules:
        - DO NOT reveal chain-of-thought; only give the final action + input.
        - Use the original question, the sub-question, and previous sub-answers as context.
        - Keep Action Input atomic and precise.
        - Choose search_wiki() ONLY when the needed information is expected to exist on Wikipedia.
        - Choose search_browser() ONLY when the information is unlikely to be on Wikipedia or requires broader search.
        - NEVER mix the behaviors of tools or treat them as interchangeable.
        - If no tool is needed, answer normally without the Action format.

        Your job is to output the correct tool and correct input for each sub-question.
        '''

        for i,sub_question in enumerate(sub_questions):


            prompt = f'''
            Original question:
            {question}

            Current sub-question:
            {sub_question}

            Previous answers (if any):
            {sub_answers}

            Think step-by-step internally but DO NOT reveal your reasoning.
            Return only a short answer (<80 tokens).
            '''
            
            # Call model to solve sub problems
            sub_answer=self.call_model(prompt,system)

            if sub_answer['status']!=200:
                print(sub_answer)
                return
            
            # Determine Action



            # input=re.findall(r'Action Input:(.*)',sub_answer['text'])
            # if input:
            #     input=input[0].strip()
            
            # key=re.findall(r'Action:(.*)',sub_answer['text'])
            # if key:
            #     key=key[0].strip()
            #     print(key)
            #     sub_answer['text']+=f'\nSearch result: {toolbox[key](input)}' 
            
            sub_answers.append({'id':i,'subq':sub_question,'ans':sub_answer["text"]})
        
        return sub_answers
     
    def detect_tool_call(self):
        pass
    def get_sub_questions(self,question)->list[str]:
    
        system='''
        You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

        Your job is to break a complex problem into a minimal set of sub-questions.

        You must:
        - Think step-by-step internally, but DO NOT reveal chain-of-thought.
        - Produce 3–7 sub-questions.
        - Ensure each sub-question can be answered concisely (<200 tokens).
        - Do NOT solve them yet.
        - Output only a numbered list of sub-questions with short descriptions.


        '''
        prompt=f'{question}'

        pattern=r'\d\..*'

        try:
            response:str = self.call_model(prompt,system)['text']

            # Split string starting from a number to the new line character
            sub_questions:list[str] = re.findall(pattern,response)

            return sub_questions
        
        except Exception as e:
            print(e)

    def get_sub_answers(self,question)->list[dict[Any]]:

        sub_questions:list[str] = self.get_sub_questions(question)
        sub_answers:list[dict[Any]]=[]

        system=f'''
        You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

        You are solving one sub-question of a larger problem.

        You must:
        - Reason step-by-step internally, but DO NOT reveal chain-of-thought.
        - Use the original question, the current sub-question, 
        and any previous sub-answers as context.
        - Output only a short, direct answer (<80 tokens).
        - Never output your reasoning steps.
        - Keep your final answer atomic and exact.
        You have access to the following tools:
        '''

        for i,sub_question in enumerate(sub_questions):

            prompt = f'''
            Original question:
            {question}

            Current sub-question:
            {sub_question}

            Previous answers (if any):
            {sub_answers}

            Think step-by-step internally but DO NOT reveal your reasoning.
            Return only a short answer (<80 tokens).
            '''
            
            # Call model to solve sub problems
            sub_answer=self.call_model(prompt,system)
            
            if sub_answer['status']!=200:
                print(sub_answer)
                return           

            sub_answers.append({'id':i,'subq':sub_question,'ans':sub_answer['text']})
        
        return sub_answers


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
