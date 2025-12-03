![Python >=3.10](https://img.shields.io/badge/python-%3E=3.10-blue)

# Reasoning Agent for General Purpose Problem Solving

This project explores and implements three different inference-time reasoning algorithms designed to enhance the problem-solving capabilities of language models

- [**Self-Refine** ](https://arxiv.org/pdf/2303.17651): An approach that allows the model to review and refine its own answers, iteratively correcting mistakes and enhancing output quality.

- [**ReAct (Reason + Act)**](https://arxiv.org/pdf/2210.03629) : A hybrid of reasoning and action framework where the model can not only think through a problem but also take external actions such as searching Wikipedia or browsing the web to gather additional context or evidence.

- [**Iterative Chain of Thought (CoT)**]([url](https://arxiv.org/pdf/2201.11903)) : A method where the model generates intermediate reasoning steps iteratively, improving accuracy by breaking complex problems into smaller, manageable steps.

The purpose of this project is to understand the strengths, limitations, and practical applications of these algorithms, providing insights into how different reasoning strategies can impact the accuracy, reliability, and versatility of 
language models.

## 📚 Contents

- [Getting Started](#-Getting-Started)

- [Example](#-Example)

- [Implementation Explanation](#-Implementation-Explanation)

  - [Project Structure](#Project-Structure)
  - [Self-Refine](#Self-Refine)
  - [ReAct](#ReAct)
  - [Iterative Chain of Thought (CoT)](#Iterative-Chain-of-Thought-(CoT))

- [Evaluation](#-Evaluation)


## 🚀 Getting Started

#### Installing with UV

> DO NOT activate your virtual environment , uv will create and manage one automatically
```
git clone https://github.com/LV6LASERLOTUS/Reasoning-Agent-for-General-Purpose-Problem-Solving.git

# Set up python environment
pip install uv
uv sync
```
#### Installing with Pip
```
git clone https://github.com/LV6LASERLOTUS/Reasoning-Agent-for-General-Purpose-Problem-Solving.git
cd Reasoning-Agent-for-General-Purpose-Problem-Solving
# Setup Python evironment

python -m venv .venv
pip install requirements.txt

```

## 🔍 Example

To use a inference time algorithm 

1) instantiate a Agent class with `api_key (str, api_base (str) , model_name(str),  temperature (float)` .

<img width="617" height="153" alt="Screenshot 2025-12-02 at 11 07 09 PM" src="https://github.com/user-attachments/assets/9e116f40-1a9b-49f5-9cf1-9ac41dd1dad8" />

2) Using the instantiated agent , call the algorithm you want to use by providing `question (str)  , max_call (int) : set to 20 by default`

<img width="983" height="395" alt="Screenshot 2025-12-02 at 11 23 29 PM" src="https://github.com/user-attachments/assets/625159ea-5198-4709-b729-9690c05d2640" />

## 🧩 Implementation Explanation

### Project Structure

- `src/agents.py` : Contains all the different algorithms alongside methods related to the agent
- `src/agent_tools.py` : Contains the implementation of wikipedia search alongside the browser search
- `src/utils.py` : Contains all around tools such as read_file
- `prompts/` : Contains all the system prompt used by the agent divided into each folder
- `dataset/`: Contains the zip file of the training and test question dataset

### Self-Refine

Inspired by [[Madaan et al., 2023](https://arxiv.org/pdf/2303.17651)], the Self-Refine loop works like this:

1) Generate an initial response (string) from the model.

2) Send that response back to the same model to request feedback (string), where the model also grades the response on a 0–10 scale.

3) Provide the model with both the original response and the feedback to produce a refined response.

4) Repeat steps 2–3 until the model's grade meets 8/10, or until a `max_call` is reached.

This approach helps the agent iteratively improve output quality by using the model's own feedback as guidance.

<img width="853" height="320" alt="Screenshot 2025-12-02 at 11 22 58 PM" src="https://github.com/user-attachments/assets/70c47d30-1f4d-4935-94c1-e30741f940f1" />

### ReAct

Inspired by [[Yao et al., 2022](https://arxiv.org/pdf/2210.03629)], the ReAct-style controller uses few-shot prompting to decide whether the model should take an external action.

1) The model chooses between:

    - Taking an action (search_browser(query), search_wiki(query))

    - Continuing to reason internally.

2) When an action is taken, the result is summarized and appended as an `Observation:` for the next reasoning step.
3) If no action is taken, the model's current reasoning is summarized and provided as context for the next iteration.

This pattern lets the agent combine thinking and acting, using external knowledge only when needed to improve its own response's factual correctness.

<img width="790" height="666" alt="Screenshot 2025-12-03 at 12 19 11 AM" src="https://github.com/user-attachments/assets/0c263c85-d34a-453f-8d8b-5c69dfc20364" />

### Iterative Chain of Thought (CoT)

Inspired by [[Wei et al., 2022]([url](https://arxiv.org/pdf/2201.11903))], the Iterative CoT prompts the model to produce step-by-step reasoning for a question. 

To preserve reasoning:

- Each response from the model is summarized and stored in a chat_log (a list of concise step summaries and recommended next actions).

- On each loop iteration, the agent passes the original question plus the chat_log back to the model so it can continue from the last step.

The loop continues until either:

- A response containing Answer: is produced, or

- A configurable max_calls iteration limit is reached.

This design preserves context across iterations while keeping prompts short and focused on the next reasoning step.

<img width="858" height="429" alt="Screenshot 2025-12-02 at 11 41 40 PM" src="https://github.com/user-attachments/assets/e3a12fde-9879-47ca-8ce2-3991f0cb83e8" />

## 📊 Evaluation
The evaluation was done mainly through scripts and model grading.
