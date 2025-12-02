# import os
import re
import requests
from typing import Any

# Custom Module
from .agent_tools import search_wiki,search_browser
from .utils import read_file


class Agent():
    def __init__(
            self, 
            api_key: str, 
            api_base: str, 
            model_name: str, 
            temperature: float = 0.0
    ):
    
        # Model Setting
        self.api_key=api_key
        self.api_base=api_base
        self.model_name=model_name
        self.temp=temperature

        # Counter updates everytime call_model is called
        self.calls=0
    
    def self_refine(self, question: str, max_calls: int = 10) -> str:
        """Runs the Self-Refine algorithm for a given question.

        The model iteratively generates a response, requests feedback,
        and refines the response until it achieves a score of 8/10 or if the
        maximum number of calls is reached.

        Args:
            question (str): TThe question to ask the model.
            max_calls (int): Maximum number of refinement calls.

        Returns:
            str: The refined response that reached 8/10 score,
                or the last refined response if no acceptable score is met.
        """
        
        #Load system prompt
        system_refine_template = read_file("../prompts/self_refine/system_refine.txt")
        system_feedback_template = read_file("../prompts/self_refine/system_feedback.txt")

        score_pattern = "([0-9]*/[0-9]*)"
        self.calls = 0

        # Initial model answer
        user_prompt = f"Question: {question}"
        response = self.call_model(user=user_prompt)
        
        for _ in range(max_calls - self.calls):

            feedback = self.call_model(
                user=response["text"],
                system=system_feedback_template
            )

            if not feedback["text"]:
                return feedback["error"]
            
            # Extract score
            match = re.search(score_pattern, feedback["text"])
            score = match.group(0) if match else None


            if score == "8/10":
                answer = self.parse_answer(response["text"])
                return answer

            # Build refining prompts
            system_refined = (
                f"{system_refine_template}"
                f"Given the feedback {feedback["text"]}\n\n"
                f"Refine the response below."
            )
            user_refined = (
                f"Orignal question: {question}"
                f"Your previous response:\n{response["text"]}"
            )

            response_refined = self.call_model(user=user_refined, system=system_refined)
            
            if not response_refined["text"]:
                return feedback["error"]
            
            # Update the refined response to be use for next iteration
            response = response_refined

        # If loop completes wihtout achieving 8/10 score
        return self.parse_answer(response["text"])
        
    def react(self, question: str, max_calls: int = 20) -> str:
        """Runs the ReAct (Reason + Act) algorithm to answer a user question.

        The model iteratively generates reasoning steps and tool calls in the format:

            Thought -> Action -> Input -> Observation
            (or Previous response if no action is called)

        loops until "Answer:" is produced by the model or max_calls is reached.

        Args:
            question (str): The question to ask the model.
            max_calls (int): Maximum number of ReAct calls.

        Returns:
            str: The model's final answer or "Answer wasn't reach in <20 calls"
        """   

        system_template = read_file("../prompts/react/system.txt")

        # Map tool (action) name to it's function
        toolbox={
            "search_wiki": search_wiki,
            "search_browser": search_browser,
        }

        action_pattern = r"Action: (\w+)"
        input_pattern = r"Input: (.+)"
        
        user_prompt = question
        self.calls = 0

        for _ in range(max_calls - self.calls):

            response = self.call_model(user=user_prompt, system=system_template)
        
            if not response["text"]:
                return response.get("error")
  
            # If an answer has been reach, returns the answer 
            if "Answer:" in response["text"]:
                answer = self.parse_answer(response["text"])
                return answer
            
            # Extract model's action and input
            action_match = re.search(action_pattern, response["text"])
            input_match = re.search(input_pattern, response["text"])
  
            action = action_match.group(1) if action_match else None
            action_input = input_match.group(1) if input_match else None

            # Run the action if it is valid
            if action in toolbox:
                action_response = toolbox[action](action_input)
                action_response = self.summarize_response(str(action_response))
                user_prompt += f"\nObservation: {action_response}"
                continue

            # no action: continue reasoning using previous response
            previous_response = self.summarize_response(response["text"])
            user_prompt = f"\nPrevious response: {previous_response}"
            
        return "Answer wasn't reach in <20 calls"

    def chain_of_thought(self, question: str, max_calls: int = 20) -> str:
        """Runs iterative chain-of-thought reasoning using repeated model calls.

        This method iteratively calls the model, each time summarizing the
        previous reasoning steps and feeding them back as context, until 
        "Answer:" is produced by the model or max_calls is reached.

        Args:
            question (str): The question to ask the model.
            max_calls (int):Maximum number of model calls.

        Returns:
            str: The model's final answr or "Answer wasn't reach in <20 calls"
        """

        system_template = read_file("../prompts/chain_of_thought/system.txt")
        
        # Initialize the base user_prompts and empty chat log
        user_prompt = f"Please solve the following problem step-by-step:\n\nQuestion:{question}"
        chat_log = []
        self.calls = 0

        for _ in range(max_calls-self.calls):
            
            response = self.call_model(user_prompt,system_template)

            if not response["text"]:
                return response["error"]
            
            # If an answer has been reach, returns the answer 
            if "Answer" in response["text"]:
                answer = self.parse_answer(response["text"])
                return answer

            # Summarize response to add to chat log
            chat_log.append(self.summarize_response(response["text"]))

            # Prepare next user promopt
            user_prompt = (
                f"Question: {question}\n\n"
                f"Previous Reasoning:\n\n{''.join(chat_log)}"
            )

        return "Answer wasn't reach in <20 calls"

    def call_model(
            self, 
            user: str = "", 
            system: str= "", 
            timeout: int = 30
    ) -> dict[str, Any]:
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

    def summarize_response(self, response: str) -> str:
        """Summarize the response of the model

        This method calls the model to summarize a text, returning the summarize text
        and the next step of action.

        Args:
            response (str): A text that you want to summarize
        Returns:
            str: The summarized response
        """

        system_prompt = """
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

        summary= self.call_model(user=response, system=system_prompt)    
        
        if not summary["text"]:
            return summary["error"]

        return summary["text"]

    def parse_answer(self, response: str) -> str:
        """Parse the answer from the response from a model

        This method uses regex to parse out the text after "Answer: ".

        Args:
            response (str): A text that you want to parse
        Returns:
            str: The text after "Answer: "
        """  
         
        answer_pattern=r"Answer: (.+)"

        match = re.search(answer_pattern,response)

        # Parse the text after "Answer:"
        answer = match.group(1) if match else "no answer"

        return answer

if __name__ == "__main__":

    question=r"""
    In a new school, $40$ percent of the students are freshmen, $30$ percent are sophomores, $20$ percent are juniors, and $10$ percent are seniors. All freshmen are required to take Latin, and $80$ percent of sophomores, $50$ percent of the juniors, and $20$ percent of the seniors elect to take Latin. The probability that a randomly chosen Latin student is a sophomore is $\\frac{m}{n}$ , where $m$ and $n$ are relatively prime positive integers. Find $m+n$ .
    """
    #Answer : 869
    
    # robotucus = Agent(
    #     api_key=os.getenv("OPENAI_API_KEY", "cse476"),
    #     api_base=os.getenv("API_BASE", "http://10.4.58.53:41701/v1"),
    #     model_name=os.getenv("MODEL_NAME", "bens_model"),
    #     temperature=0.0
    # )

    # print(robotucus.chain_of_thought(question))
    # print(robotucus.self_refine(question=question))

    # system_prompt_path="./prompts/self_refine/system_refine.txt"
    # print(read_file(system_prompt_path))