"""
core.py - Test runner and demo
"""

import json
from .agent import IntentAgent
from .extractor import RuleBasedExtractor
from .normalizer import IntentNormalizer
from .config import MODEL_CANDIDATES, build_llm_model


def run_demo_with_llm():
    """Demo with LLM (requires Google API key and quota)"""
    try:
        print("="*80)
        print("PRODUCTION INTENT AGENT - LLM MODE")
        print(f"Model chain: {', '.join(MODEL_CANDIDATES)}")
        print("="*80)

        model = build_llm_model()
        if model is None:
            raise RuntimeError("No Gemini models could be initialized")
        
        agent = IntentAgent(model=model)
        
        test_prompts = [
            "Show me shopping data for customer 101 on 2026-03-10",
            "Compare IBM transaction spend and Unisys shopping behavior",
            "Fetch shopping behavior from Unisys ePortal",
            "Analyze category-wise card spend for last 30 days",
            "Reconcile shopping records against IBM transaction dates",
        ]
        
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


def run_demo_fallback_only():
    """Demo using rule-based fallback (no LLM, no API quota needed)"""
    print("="*80)
    print("INTENT AGENT - FALLBACK MODE (Rule-Based, No API)")
    print("="*80)
    
    extractor = RuleBasedExtractor()
    normalizer = IntentNormalizer()
    
    test_prompts = [
        "Show me shopping data for customer 101 on 2026-03-10",
        "Compare IBM transaction spend and Unisys shopping behavior",
        "Fetch shopping behavior from Unisys ePortal",
        "Analyze category-wise card spend for last 30 days",
        "Reconcile shopping records against IBM transaction dates",
    ]
    
    for prompt in test_prompts:
        print(f"\nUser: {prompt}")
        print("-" * 80)
        
        # Extract components using fallback
        task = extractor.extract_task(prompt)
        entities = extractor.extract_entities(prompt)
        attributes = extractor.extract_attributes(prompt)
        systems = extractor.extract_systems(prompt, entities)
        filters = extractor.extract_filters(prompt)
        time_range = normalizer.normalize_date_range(prompt)
        
        print(f"Task: {task}")
        print(f"Entities: {entities}")
        print(f"Attributes: {attributes}")
        print(f"Systems: {systems}")
        print(f"Filters: {json.dumps(filters, indent=2)}")
        if time_range:
            print(f"Time Range: {time_range}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fallback":
        run_demo_fallback_only()
    else:
        try:
            run_demo_with_llm()
        except Exception as e:
            print(f"\nLLM mode failed. Falling back to rule-based extraction...")
            run_demo_fallback_only()
