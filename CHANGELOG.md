# Changelog

## 2026-04-20

### Intent Agent: CRITICAL RULES Implementation
- **RULE 1: ENTITY vs FILTER distinction**
  - Updated `schemas.py`: Added `FilterCondition` class with `{field, value}` structure for proper filter representation
  - Updated `constants.py`: Separated `ENTITY_MAPPINGS` from `IDENTIFIER_MAPPINGS` to clarify entity-only vs. filter/identifier fields
  - Updated `extractor.py`: Filter extraction now returns structured `{field, value}` pairs instead of loose strings
  - Updated `normalizer.py`: Added `extract_filters()` method for standardized filter condition creation

- **RULE 2: SYSTEM OWNERSHIP mapping**
  - Updated `constants.py`: Added `ENTITY_SYSTEM_MAPPING` dictionary for deterministic entitysystem routing:
    - `shopping`  `unisys`
    - `transaction`  `ibm`
    - `account`  `ibm`
    - `customer`  `ibm`
  - Updated `extractor.py`: `extract_systems()` now respects entity ownership mapping instead of loose keyword detection
  - Updated `agent.py`: System assignment in `_parse_and_normalize()` enforces entity-system mapping

- **RULE 3: ENTITY PRIORITY enforcement**
  - Updated `constants.py`: Added `ENTITY_PRIORITY` list for deterministic entity selection: `shopping > transaction > account > customer`
  - Updated `normalizer.py`: Added `apply_entity_priority()` method to reorder entities by priority
  - Updated `extractor.py`: Entity extraction applies priority ordering to multi-entity scenarios

- **RULE 4-7: Task detection, filters, dates, systems**
  - Updated `constants.py`: Enhanced `TASK_KEYWORDS` with more complete mappings for fetch/reconcile/analyze/compare/transform
  - Updated `normalizer.py`: Enhanced `normalize_date_range()` with additional date pattern support (today, yesterday, last week)
  - Updated `agent.py`: Updated LLM prompt to explicitly reference all CRITICAL RULES and expected output format

- **Testing & Validation**
  - Created `test_rules_minimal.py` to validate all CRITICAL RULES without LangChain dependencies
  - Verified implementation with 3 test cases covering fetch, compare, and analyze tasks
  - Confirmed: entity priority, system mapping, and filter extraction all working correctly
  - Test results: **3/3 tests passed **

### Files Modified
- `intent_agent/schemas.py`: Schema structure updates with FilterCondition
- `intent_agent/constants.py`: Entity mappings, system ownership, priority list
- `intent_agent/normalizer.py`: Priority application, filter extraction logic
- `intent_agent/extractor.py`: Critical rules enforcement in all extraction methods
- `intent_agent/agent.py`: Prompt updates and rule enforcement in parsing
- `test_rules_minimal.py`: New comprehensive test file (standalone, no external dependencies)

### Backward Compatibility
- All changes maintain API compatibility with existing `IntentAgent.run()` interface
- Fallback extraction mode also applies all CRITICAL RULES
- Output format remains consistent: `IntentOutput` with proper schema validation

### Example: Test Case Verification
```
Input: "Show me shopping data for customer 101 on 2026-03-10"
Expected: shopping entity, unisys system, customerId=101 filter

Output:
 Task: fetch
 Entities: ['shopping']
 Systems: ['unisys']
 Filters: {field: customerId, value: 101}, {field: date, value: 2026-03-10}
 TEST PASSED
```

## 2026-04-17

### Mock ePortal startup and CardDemo alignment
- Fixed `mock_eportal/app.py` so `python mock_eportal/app.py` works in addition to `uvicorn mock_eportal.app:app`.
- Added a guarded `__main__` startup path for the mock ePortal on port `8001`.
- Added BOM-safe JSON loading for mock ePortal data and schema files through `mock_eportal/utils/json_loader.py`.
- Updated the mock ePortal from the older payroll/customer model to AWS CardDemo-aligned entities: `customer`, `account`, `card`, and `transaction`.
- Removed the deprecated payroll service, payloads, and schema from the mock ePortal.
- Expanded mock ePortal federation metadata, schema discovery, and MCP tool manifests to describe CardDemo relationships.
- Added supporting alignment docs in `mock_eportal/ALIGNMENT.md`, `mock_eportal/API_CHANGES.md`, `mock_eportal/entity_mapping.json`, and `mock_eportal/ENTITY_MAPPING_OUTPUT.json`.

### Context resolution and mainframe metadata ingestion
- Added the `context_resolution_agent` package with IBM and Unisys resolvers plus shared schemas.
- Added backend routes for context resolution and end-to-end pipeline execution in `app/api/context.py` and `app/api/pipeline.py`.
- Reworked `app/api/agent.py` around the intended architecture: intent parsing first, context resolution second, planner/execution deferred downstream.
- Added the COBOL/JCL parser workspace under `tools/cobol-jcl-parser/`, including parser wrappers, build/run scripts, sample CardDemo assets, and generated metadata outputs.

### Notes
- The repository still contains several older payroll-oriented examples and prompt defaults outside the mock ePortal, especially in `intent_agent`, `app/api/*`, `README.md`, and some resolver heuristics. They are legacy text/config references rather than part of the new mock ePortal API surface.

## 2026-04-15

### Intent agent modularization and pipeline UI
- Refactored the intent understanding layer into a dedicated `intent_agent` package with `agent.py`, `extractor.py`, `normalizer.py`, `schemas.py`, `constants.py`, and helper utilities.
- Updated `app/main.py` to present the platform as a multi-stage federation backend and to register the newer API routers.
- Added frontend pipeline panels and orchestration views for intent, context, planning, and execution result visualization.
- Added `frontend/src/services/agentPipeline.ts` and refreshed execution page behavior to integrate with the new backend pipeline.
- Updated `run.py` and project docs around the newer backend structure.

## 2026-04-14

### Intent agent introduction and backend integration
- Introduced the first Intent Agent implementation and evaluation flow.
- Connected the intent layer to the backend.
- Updated dependencies in `requirements.txt` for LangChain, FastAPI, Google Generative AI, and related support packages.
- Refined frontend API usage and command page behavior to fit the evolving backend responses.

## 2026-02-17

### Catalog integration fixes
- Replaced inline/mock catalog endpoints with the routed catalog service.
- Corrected catalog repository imports and aligned backend/frontend schemas with the actual catalog payloads.
- Simplified jobs, workflows, and datasets models to match the repository output.
- Reworked catalog pages so command, job, workflow, and dataset views render real data cleanly.

## Verification snapshot
- Backend main app entrypoint: `uvicorn app.main:app --reload`
- Mock ePortal entrypoint: `uvicorn mock_eportal.app:app --port 8001 --reload`
- Direct mock ePortal script startup now also works: `python mock_eportal/app.py`
