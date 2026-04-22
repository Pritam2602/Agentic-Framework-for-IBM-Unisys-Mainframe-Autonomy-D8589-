# Changelog

## 2026-04-22

### Gemini fallback, grounded context resolution, and control-center fixes
- Added centralized Gemini model construction in `intent_agent/config.py` with ordered model fallback support and shared configuration reuse across backend entrypoints.
- Updated intent and pipeline LLM initialization paths to fail fast into fallback behavior instead of stalling on repeated Gemini retries.
- Fixed pipeline degradation behavior so Gemini quota/model failures fall back cleanly instead of surfacing `500` errors.
- Corrected `/api/context/health` to use the current resolver/catalog layout instead of the removed `ibm_parsers` import.
- Reworked the context resolution flow so:
  - IBM resolution is grounded in parsed COBOL/JCL outputs under `tools/cobol-jcl-parser/`
  - Unisys resolution stays grounded in the mock ePortal MCP/schema endpoints
  - the LLM is limited to optional explanation rather than overriding source-of-truth context
- Improved IBM transaction/shopping resolution to prefer transaction-bearing JCL jobs and datasets, producing IBM transaction context such as `CBTRN03C` and `AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS` for federation-style spend queries.
- Restored architectural separation by removing Zowe command catalog details from Context output after a temporary regression; planner-facing “how to access data” remains downstream.
- Enhanced Context output for planner handoff with:
  - system-specific resolved entities such as `ibm:transactions` and `unisys:shopping`
  - `entity_mapping` for cross-system federation
  - `is_federation`
  - `reasoning_summary`
  - normalized confidence capping and better parameter typing for Unisys `customerId`
- Fixed Unisys schema/parameter normalization bugs that caused fallback resolution to crash on string-shaped schema payloads.
- Updated the frontend control-center pipeline panels to expose raw Intent and Context JSON directly in the UI for inspection.
- Improved frontend context rendering so partial/empty IBM or Unisys sections are no longer mislabeled as fully resolved.
- Updated planner preview copy to reflect the intended architecture: Context identifies where data lives, Planner decides how to access it.

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
