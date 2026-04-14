"""
eval.py - Evaluation utilities for IntentAgent
"""

from typing import Any, Dict, List
import time

from .agent import IntentAgent
from .schemas import IntentOutput


def evaluate_agent(
    agent: IntentAgent,
    test_cases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run test prompts through the agent and record evaluation metrics.
    """
    
    results: List[Dict[str, Any]] = []
    
    for case in test_cases:
        
        prompt = case["prompt"]
        truth_intent = case["ground_truth"]["intent"]
        
        start_time = time.time()
        
        try:
            pred = agent.run(prompt)
            json_valid = True
            
        except Exception as e:
            print(f"\nAgent error: {e}")
            json_valid = False
            pred = IntentOutput(
                task="",
                entities=[],
                attributes=[],
                systems=[],
                priority="low",
                confidence_score=0.0,
            )
        
        latency = time.time() - start_time
        
        results.append(
            {
                "prompt": prompt,
                "predicted_intent": pred.task,
                "predicted_entities": pred.entities,
                "predicted_attributes": pred.attributes,
                "intent_match": pred.task == truth_intent,
                "json_valid": json_valid,
                "confidence": pred.confidence_score,
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
        "confidence",
        "latency",
    ]
    
    lines = ["\t".join(headers)]
    
    for model_name, rows in evals.items():
        for r in rows:
            lines.append(
                "\t".join(
                    [
                        model_name,
                        r["prompt"][:30],
                        str(r["intent_match"]),
                        str(r["json_valid"]),
                        f"{r['confidence']:.2f}",
                        f"{r['latency']:.3f}s",
                    ]
                )
            )
    
    print("\n".join(lines))
