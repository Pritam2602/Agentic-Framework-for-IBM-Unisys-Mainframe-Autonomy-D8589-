# Intent Agent - Production Grade Pure Understanding Layer

## Architecture Overview

The Intent Agent is responsible for understanding **WHAT** the user wants, not **HOW** to execute it.

This is pure intent extraction - no Zowe commands, no API calls, no planning.

## Modular Structure

`
intent_agent/
 __init__.py          # Package exports
 schemas.py           # Pydantic data models
 constants.py         # Mappings and configuration
 normalizer.py        # Data normalization logic
 utils.py             # Helper functions (priority, confidence)
 extractor.py         # Rule-based fallback extraction
 agent.py             # Main IntentAgent class
 core.py              # Test runner and demo
 eval.py              # Evaluation utilities
 README.md            # This file
`

## Module Responsibilities

### schemas.py
Data models for intent output:
- FilterCriteria: Time ranges and conditions
- IntentOutput: Complete structured intent

### constants.py
Configuration mappings:
- ENTITY_MAPPINGS: Entity synonyms
- ATTRIBUTE_MAPPINGS: Attribute synonyms
- DEFAULT_ENTITY_ATTRIBUTES: Default fields per entity
- TASK_KEYWORDS: Task type keywords
- SYSTEM_KEYWORDS: System identifiers

### normalizer.py
Intent normalization:
- Entity name normalization
- Attribute name normalization
- Date range parsing and normalization

### utils.py
Utility functions:
- infer_priority(): Task-based priority inference
- compute_confidence(): Confidence score computation

### extractor.py
Fallback extraction when LLM fails:
- RuleBasedExtractor: Keyword-based intent extraction
- Task detection from text
- Entity and attribute extraction
- System detection with smart fallback logic

### agent.py
Core intent agent:
- IntentAgent: Main class
- LLM integration
- JSON parsing and validation
- Normalization and validation
- Fallback handling

### eval.py
Evaluation framework:
- Agent evaluation against test cases
- Metrics collection
- Results visualization

## Usage

`python
from intent_agent import IntentAgent
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize model
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Create agent
agent = IntentAgent(model=model)

# Process user input
intent = agent.run("Show me payroll data for March 2026")

# Access structured output
print(intent.task)        # "fetch"
print(intent.entities)    # ["payroll"]
print(intent.attributes)  # ["employeeId", "netSalary", "employeeName"]
print(intent.systems)     # ["ibm", "unisys"]
print(intent.priority)    # "medium"
print(intent.confidence_score)  # 0.85
`

## Expected Output Format

`json
{
  "task": "fetch",
  "entities": ["payroll"],
  "attributes": ["employeeId", "netSalary", "employeeName"],
  "filters": {
    "time_range": {
      "start": "2026-03-01",
      "end": "2026-03-31"
    },
    "conditions": []
  },
  "systems": ["ibm", "unisys"],
  "priority": "medium",
  "confidence_score": 0.85
}
`

## Key Features

### Fix 1: Entity Default Attributes
If user doesn't specify attributes, they're populated from entity defaults:
- payroll -> [employeeId, netSalary, employeeName]
- customer -> [customerId, customerName, accountId]
- transaction -> [transactionId, transactionAmount, transactionDate]

### Fix 2: Smart System Detection
Instead of defaulting to both systems:
- If mentions API/REST/HTTP -> Unisys
- If mentions datasets/JCL/Zowe -> IBM
- Default -> IBM (mainframe-first)

### Fix 3: Priority Logic
Based on task type:
- compare/analyze -> high
- fetch/reconcile/transform -> medium
- others -> low

### Fix 4: Strict Schema Enforcement
Required fields validation:
- task (non-empty)
- entities (non-empty list)
- systems (non-empty list)
- attributes enforced as list

### Fix 5: Confidence Scoring
Based on:
- Presence of entities (+0.15)
- Presence of attributes (+0.15)
- Presence of filters (+0.1)
- Presence of systems (+0.1)
- Task clarity (adjustment -0.2 if ambiguous)
- Fallback penalty (x0.8)

## Integration Points

### Input from Users
Natural language queries about data

### Output to Context Resolution Agent
Structured intent JSON containing:
- What task to perform
- What entities are involved
- What attributes are needed
- What systems might have the data

The Context Resolution Agent uses this to determine WHERE to find the data.

## Testing

Run demo:
`ash
python -m intent_agent.core
`

Run evaluation:
`ash
python eval_demo.py
`

## Design Principles

1. Separation of Concerns: Each module has a single responsibility
2. Modularity: Easy to test and extend
3. Production-Ready: Proper error handling and fallbacks
4. Normalized Output: All data standardized before output
5. No Side Effects: Pure functions where possible
