
# IntentAgent

IntentAgent is an LLM-powered system that converts natural language prompts into structured **Zowe CLI commands** using a capability catalog.

The goal of this project is to evaluate how well Large Language Models (LLMs) can understand enterprise-style prompts and map them to valid structured commands.

---

## Architecture

The system follows this pipeline:

User Prompt  
↓  
IntentAgent  
↓  
Capability Catalog (JSON)  
↓  
Prompt Grounding  
↓  
LLM (Gemini / OpenAI)  
↓  
Structured JSON Output  
↓  
Evaluation Metrics

The capability catalog provides the list of supported commands and parameters that the LLM must choose from.

---

## Features

- Natural language → Zowe CLI command mapping
- Structured JSON output using **Pydantic**
- Capability catalog grounding
- LLM benchmarking support
- Evaluation metrics including:
  - Intent match accuracy
  - JSON validity
  - Hallucinated command detection
  - Latency measurement

---

## Project Structure

intent_agent/

core.py  
Main implementation of the IntentAgent

eval.py  
Evaluation utilities for benchmarking agent performance

capability_catalog.json  
Capability catalog containing supported intents and Zowe commands

requirements.txt  
Python dependencies

README.md  
Project documentation

---

## Capability Catalog

The capability catalog defines all valid commands the agent can map to.

Example entry:

{
  "intent_name": "list_datasets",
  "zowe_command": "zowe files list data-set",
  "required_parameters": ["dataset_pattern"],
  "optional_parameters": []
}

The agent uses this catalog to ensure that the generated commands are valid and not hallucinated.

---

## Installation

Clone the repository and install dependencies.

git clone <repository_url>
cd intent_agent

Create a virtual environment:

python -m venv venv

Activate it:

Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

---

## Environment Setup

Create a `.env` file in the project root.

Example:

OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key

The agent will automatically load these keys using `python-dotenv`.

---

## Running the Agent

From the project root:

python -m intent_agent.core

The script will:
1. Initialize supported LLM providers
2. Run evaluation prompts
3. Print evaluation metrics
4. Show a sample prediction

---

## Example Prompt

Show me all datasets starting with SYS

Example Output:

{
  "intent": "list_datasets",
  "zowe_command": "zowe files list data-set",
  "parameters": {
    "dataset_pattern": "SYS*"
  },
  "missing_fields": [],
  "confidence": 1.0
}

---

## Evaluation Metrics

The evaluation system measures:

intent_match  
Whether predicted intent matches ground truth

json_valid  
Whether the model returned valid structured JSON

hallucinated_command  
Whether the command exists in the catalog

latency  
Time taken for model response

Example output:

model   prompt                         intent_match json_valid hallucinated latency
gemini  Show me all datasets...        True        True       False        0.82s
gemini  Submit a job with job card...  True        True       False        0.91s

---

## Supported Models

The system currently supports:

- Google Gemini
- OpenAI GPT models

Additional local models can be integrated.

---

## Future Improvements

Possible enhancements include:

- Retrieval-based command selection using embeddings
- Vector search over capability catalog
- SQL-backed capability catalog
- Multi-agent intent validation
- Advanced benchmarking across multiple LLMs

---

## License

This project is intended for research and educational purposes.
