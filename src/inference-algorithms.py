import os
import re
import requests
from typing import Any

API_KEY  = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")  
MODEL    = os.getenv("MODEL_NAME", "bens_model") 

def call_model(prompt: str,
               system: str = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant. Reply with only the final answer—no explanation.",
               model: str = MODEL,
               temperature: float = 0.0,
               timeout: int = 60) -> dict[str, Any]:
    """
    Calls an OpenAI-style /v1/chat/completions endpoint and returns:
    { 'ok': bool, 'text': str or None, 'raw': dict or None, 'status': int, 'error': str or None, 'headers': dict }
    """
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1024,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        status = response.status_code
        hdrs   = dict(response.headers)
        if status == 200:
            data = response.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
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


def get_sub_questions(question:str,temp:float=0.0)->list[str]:
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
        response:str = call_model(prompt,system,temperature=temp)['text']

        # Split string starting from a number to the new line character
        sub_questions:list[str] = re.findall(pattern,response)

        return sub_questions
    
    except Exception as e:
        print(e)

def get_sub_answers(question:str,temp:float=0.0)->list[dict[Any]]:

    sub_questions:list[str] = get_sub_questions(question)
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
        sub_answer=call_model(prompt,system,temperature=temp)
        
        if sub_answer['status']!=200:
            print(sub_answer)
            return
        
        sub_answers.append({'id':i,'subq':sub_question,'ans':sub_answer['text']})
    
    return sub_answers

def chain_of_thought(question:str,temp:float=0.0)->str:

    sub_answers=get_sub_answers(question,temp=temp)

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

    answer=call_model(prompt=prompt,system=system,temperature=temp)

    if answer['status'] != 200:
        return print(answer)
    
    return answer['text']



if __name__=='__main__':

    # answer 29

    question="""
    Which magazine was started first Arthur's Magazine or First for Women?
    """

    print(question) 
    
    for q in get_sub_questions(question):
        print(q)

    for entry in get_sub_answers(question):
        print('\n============== Sub Questions ===========\n')

        print(entry['subq'])

        print(entry['ans'])

    print('\n============== Final Answer ===========\n')

    print(chain_of_thought(question))



