"""
Evaluation utilities for the IntentAgent package.

Contains functions to benchmark and compare agent predictions against
ground-truth cases. Measures latency, JSON validity, intent match,
and hallucinated command detection.
"""

from typing import Any, Dict, List
import time

from .core import IntentOutput, IntentAgent


def evaluate_agent(
    agent: IntentAgent,
    test_cases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run test prompts through the agent and record evaluation metrics.
    """

    # valid commands from catalog
    commands = {entry["zowe_command"] for entry in agent.catalog}

    results: List[Dict[str, Any]] = []

    for case in test_cases:

        prompt = case["prompt"]
        truth_intent = case["ground_truth"]["intent"]

        start_time = time.time()

        try:
            # run agent
            pred = agent.run(prompt)

            json_valid = True

        except Exception as e:

            print("\nAgent error:", e)

            json_valid = False

            pred = IntentOutput(
                intent="",
                zowe_command="",
                parameters={},
                missing_fields=[],
                confidence=0.0,
            )

        latency = time.time() - start_time

        results.append(
            {
                "prompt": prompt,
                "predicted_intent": pred.intent,
                "intent_match": pred.intent == truth_intent,
                "json_valid": json_valid,
                "hallucinated_command": pred.zowe_command not in commands,
                "latency": latency,
            }
        )

    return results


def print_evaluation_table(evals: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Pretty-print a comparison table of evaluation results.
    """

    headers = [
        "model",
        "prompt",
        "intent_match",
        "json_valid",
        "hallucinated",
        "latency",
    ]

    lines = ["\t".join(headers)]

    for model_name, rows in evals.items():

        for r in rows:

            lines.append(
                "\t".join(
                    [
                        model_name,
                        r["prompt"],
                        str(r["intent_match"]),
                        str(r["json_valid"]),
                        str(r["hallucinated_command"]),
                        f"{r['latency']:.3f}s",
                    ]
                )
            )

    print("\n".join(lines))