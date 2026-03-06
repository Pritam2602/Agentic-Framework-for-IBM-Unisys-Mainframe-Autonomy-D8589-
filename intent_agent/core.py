"""
Core implementation of the IntentAgent package.
"""

import json
import re
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class IntentOutput(BaseModel):
    intent: str
    zowe_command: str
    parameters: Dict[str, Any]
    missing_fields: List[str]
    confidence: float


# ---------------------------------------------------------------------------
# Catalog loader
# ---------------------------------------------------------------------------


def load_catalog(path: str) -> List[Dict[str, Any]]:
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")

    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Model initialization
# ---------------------------------------------------------------------------


def init_model(provider: str = "openai"):

    provider = provider.lower()

    if provider == "openai":

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )

    elif provider == "gemini":

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            temperature=0
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


# ---------------------------------------------------------------------------
# Intent Agent
# ---------------------------------------------------------------------------


class IntentAgent:

    def __init__(
        self,
        catalog_path: str,
        model: Any
    ):

        self.catalog = load_catalog(catalog_path)
        self.model = model

        self.parser = PydanticOutputParser(
            pydantic_object=IntentOutput
        )

        self.prompt = self._build_prompt()

    # -----------------------------------------------------------------------

    def _build_prompt(self):

        catalog_lines = []

        for entry in self.catalog:

            catalog_lines.append(
                f"- {entry['intent_name']} -> {entry['zowe_command']} "
                f"(required={entry.get('required_parameters', [])}, "
                f"optional={entry.get('optional_parameters', [])})"
            )

        catalog_text = "\n".join(catalog_lines)

        system_prompt = f"""
You are an enterprise intent-to-command mapping assistant.

You must map user requests to Zowe CLI commands.

Rules:
- Use ONLY the commands listed below
- NEVER invent commands
- Output STRICT JSON only.

Return a JSON object with these fields:
intent
zowe_command
parameters
missing_fields
confidence

Example structure (do not include explanation):
intent: string
zowe_command: string
parameters: object
missing_fields: list
confidence: float

Available commands:
{catalog_text}
"""

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", "{user_input}")
            ]
        )

    # -----------------------------------------------------------------------

    def run(self, user_prompt: str) -> IntentOutput:

        chain = self.prompt | self.model

        result = chain.invoke(
            {
                "user_input": user_prompt
            }
        )

        return self._parse(result.content)

    # -----------------------------------------------------------------------

    def _parse(self, text: str) -> IntentOutput:

        try:
            # extract first JSON object
            json_match = re.search(r"\{[\s\S]*\}", text)

            if not json_match:
                raise ValueError("No JSON found")

            json_text = json_match.group()

            return self.parser.parse(json_text)

        except Exception:
            raise RuntimeError(
                f"Invalid JSON returned by model:\n{text}"
            )
# ---------------------------------------------------------------------------
# Script Runner
# ---------------------------------------------------------------------------


if __name__ == "__main__":

    from .eval import evaluate_agent, print_evaluation_table

    catalog_file = Path(__file__).parent / "capability_catalog.json"

    test_prompts = [

        {
            "prompt": "Show me all datasets starting with SYS",
            "ground_truth": {"intent": "list_datasets"}
        },

        {
            "prompt": "Submit a job with job card //MYJOB and jcl path /u/my.jcl",
            "ground_truth": {"intent": "submit_job"}
        },

        {
            "prompt": "Give me a list of jobs with status OUTPUT",
            "ground_truth": {"intent": "list_jobs"}
        }

    ]

    providers = [ "gemini"]

    eval_results = {}

    for provider in providers:

        try:

            print(f"\nInitializing model: {provider}")

            model = init_model(provider)

            agent = IntentAgent(
                catalog_path=str(catalog_file),
                model=model
            )

            results = evaluate_agent(agent, test_prompts)

            eval_results[provider] = results

        except Exception as e:

            print(f"Skipping provider {provider}: {e}")

    if eval_results:

        print("\nEvaluation Results:\n")

        print_evaluation_table(eval_results)

        print("\nSample Prediction:\n")

        first_provider = list(eval_results.keys())[0]

        model = init_model(first_provider)

        agent = IntentAgent(
            str(catalog_file),
            model
        )

        sample = agent.run(
            test_prompts[0]["prompt"]
        )

        print(sample)

    else:

        print("\nNo models ran successfully.")