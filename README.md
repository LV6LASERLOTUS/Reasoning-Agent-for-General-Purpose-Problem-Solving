
# Reasoning Agent for General Purpose Problem Solving

This project explores and implements three different inference-time reasoning algorithms designed to enhance the problem-solving capabilities of language models

- **Iterative Chain of Thought (CoT)** : A method where the model generates intermediate reasoning steps iteratively, improving accuracy by breaking complex problems into smaller, manageable steps.

- [**Self-Refine** ]([url](https://arxiv.org/pdf/2303.17651)): An approach that allows the model to review and refine its own answers, iteratively correcting mistakes and enhancing output quality.

- **ReAct (Reason + Act)** : A hybrid of reasoning and action framework where the model can not only think through a problem but also take external actions such as searching Wikipedia or browsing the web to gather additional context or evidence.

The purpose of this project is to understand the strengths, limitations, and practical applications of these algorithms, providing insights into how different reasoning strategies can impact the accuracy, reliability, and versatility of 
language models.

## 📚 Contents

- [Getting Started](#-Getting-Started)

- [Example](#-Example)

- [Evaluation](#-Evaluation)


## 🚀 Getting Started
### Prerequisites
- Python>=3.14
- git
- pip/uv 

#### Installing with UV

> DO NOT activate your virtual environment or else uv will create and manage one automatically
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

Below is a simple example using the Chain of thought algorithm with a Qwen Model.

<img width="1049" height="417" alt="Screenshot 2025-12-02 at 1 22 23 AM" src="https://github.com/user-attachments/assets/036f4a60-c2ac-404e-bb12-7877ef801cf6" />


## 📊 Evaluation
The evaluation was done mainly through scripts and model grading.
