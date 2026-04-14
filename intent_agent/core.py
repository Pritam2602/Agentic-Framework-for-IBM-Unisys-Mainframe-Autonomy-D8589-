"""
core.py - Test runner and demo
"""

import json
from .agent import IntentAgent


def run_demo():
    """Demo runner for Intent Agent"""
    
    test_prompts = [
        "Show me payroll data for March 2026",
        "Compare employee salaries between IBM and Unisys",
        "Fetch customer accounts from Unisys ePortal",
        "Analyze transaction patterns for last 30 days",
        "Reconcile payroll records across systems",
    ]
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        print("="*80)
        print("PRODUCTION INTENT AGENT - PURE UNDERSTANDING LAYER")
        print("="*80)
        
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0
        )
        
        agent = IntentAgent(model=model)
        
        for prompt in test_prompts:
            print(f"\nUser: {prompt}")
            try:
                intent = agent.run(prompt)
                print(f"Intent Output:")
                print(json.dumps(intent.model_dump(), indent=2))
            except Exception as e:
                print(f"Error: {e}")
    
    except Exception as e:
        print(f"SETUP ERROR: {e}")
        print("Ensure GOOGLE_API_KEY is set in .env")


if __name__ == "__main__":
    run_demo()
