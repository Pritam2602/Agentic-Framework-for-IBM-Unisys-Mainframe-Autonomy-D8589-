"""LLM-backed Normalization Agent.

Architectural role:
  Execution Agent (RUN) -> Normalization Agent (COMMON SHAPE)

The LLM proposes normalization guidance, but deterministic code performs the
actual mapping so financial domain rules remain grounded.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from app.models.schemas import TraceEvent
from intent_agent.config import build_llm_model

from .schemas import (
    CanonicalRecord,
    NormalizationAgentResponse,
    NormalizationSummary,
)

logger = logging.getLogger(__name__)


NORMALIZATION_SYSTEM_PROMPT = """
You are an enterprise Normalization Agent for a mainframe federation platform.

Your job is to explain how execution outputs should be mapped into a common
intermediate structure. You do NOT execute commands and do NOT change source
data.

Critical domain rule:
- IBM CardDemo transaction amounts are the financial source of truth.
- Unisys ePortal shopping amounts mirror IBM shopping spend and are behavioral
  enrichment only.
- Never add IBM amounts and Unisys amounts together for total_spend.

Return STRICT JSON only:
{{
  "entity": "transaction|shopping|unknown",
  "field_mapping": {{
    "customer_id": ["customerId", "customer_id"],
    "record_id": ["transactionId", "id"],
    "amount": ["transactionAmount", "amount"],
    "date": ["transactionDate", "date"]
  }},
  "warnings": ["string"],
  "reasoning_summary": "string"
}}
"""


class NormalizationAgent:
    """Maps heterogeneous execution results into canonical records."""

    def __init__(self, model: Any = None, enable_llm: bool = True):
        self.model = model if model is not None else (
            build_llm_model(logger=logger) if enable_llm else None
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", NORMALIZATION_SYSTEM_PROMPT), ("user", "{normalization_request}")]
        )

    def run(
        self,
        execution_output: Dict[str, Any],
        intent: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        use_llm: bool = True,
    ) -> NormalizationAgentResponse:
        """Normalize execution output into a common intermediate structure."""
        trace: List[Dict[str, Any]] = []
        warnings: List[str] = []
        self._add_trace(trace, "normalization", "Received execution output")

        guidance = self._get_llm_guidance(execution_output, intent, context, warnings) if use_llm else {}
        if guidance.get("warnings"):
            warnings.extend(str(item) for item in guidance["warnings"])

        records = self._normalize_records(execution_output)
        summary = self._summarize(records, warnings)
        status = "completed" if records else "partial"

        canonical_output = {
            "type": "canonical_records",
            "data": [record.model_dump() for record in records],
            "metadata": {
                "record_count": len(records),
                "sources": sorted({record.source_system for record in records}),
                "normalization_rule": (
                    "IBM amounts are financial source of truth; Unisys amounts are enrichment only."
                ),
                "llm_reasoning": guidance.get("reasoning_summary"),
            },
        }

        self._add_trace(
            trace,
            "normalization",
            f"Normalized {len(records)} record(s)",
            summary.model_dump(),
        )

        return NormalizationAgentResponse(
            status=status,
            natural_response=(
                f"Normalized {len(records)} record(s) into the common intermediate schema."
            ),
            canonical_output=canonical_output,
            records=records,
            summary=summary,
            execution_trace=trace,
            warnings=warnings,
        )

    def _get_llm_guidance(
        self,
        execution_output: Dict[str, Any],
        intent: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        warnings: List[str],
    ) -> Dict[str, Any]:
        if self.model is None:
            warnings.append("LLM unavailable - used deterministic normalization")
            return {}

        request = {
            "execution_output_sample": self._compact_for_llm(execution_output),
            "intent": intent,
            "context": context,
        }
        try:
            chain = self.prompt | self.model
            result = chain.invoke({"normalization_request": json.dumps(request, default=str)})
            json_match = re.search(r"\{[\s\S]*\}", result.content)
            if not json_match:
                raise ValueError("No JSON found in LLM output")
            return json.loads(json_match.group())
        except Exception as exc:
            logger.warning("[Normalization Agent] LLM guidance failed: %s", exc)
            warnings.append("LLM normalization guidance unavailable - used deterministic mapping")
            return {}

    def _normalize_records(self, execution_output: Dict[str, Any]) -> List[CanonicalRecord]:
        records: List[CanonicalRecord] = []
        seen: set[tuple[Any, ...]] = set()
        for source_system, raw_record in self._iter_source_records(execution_output):
            record = self._to_canonical_record(source_system, raw_record)
            key = (
                record.source_system,
                record.entity,
                record.record_id,
                record.customer_id,
                record.date,
                record.amount,
                record.merchant,
                record.category,
            )
            if key in seen:
                continue
            seen.add(key)
            records.append(record)
        return records

    def _iter_source_records(self, payload: Any, source_hint: str = "unknown") -> Iterable[tuple[str, Dict[str, Any]]]:
        if isinstance(payload, list):
            for item in payload:
                yield from self._iter_source_records(item, source_hint)
            return

        if not isinstance(payload, dict):
            return

        source = self._infer_source(payload, source_hint)

        data = payload.get("data")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield source, item

        for key in ("ibm_records", "transactions"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield "ibm", item

        for key in ("unisys_records", "shopping"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield "unisys", item

        nested_keys = ("canonical_output", "output", "result", "results", "step_results", "data_sources")
        for key in nested_keys:
            value = payload.get(key)
            if isinstance(value, (dict, list)):
                yield from self._iter_source_records(value, source)

    @staticmethod
    def _infer_source(payload: Dict[str, Any], source_hint: str) -> str:
        explicit = str(
            payload.get("source")
            or payload.get("source_system")
            or payload.get("system")
            or payload.get("platform")
            or source_hint
            or "unknown"
        ).lower()
        if "unisys" in explicit or "eportal" in explicit:
            return "unisys"
        if "ibm" in explicit or "z/os" in explicit or "zowe" in explicit:
            return "ibm"
        return source_hint if source_hint in {"ibm", "unisys"} else "unknown"

    def _to_canonical_record(self, source_system: str, raw: Dict[str, Any]) -> CanonicalRecord:
        entity = str(raw.get("entity") or ("shopping" if source_system == "unisys" else "transaction"))
        customer_id = self._first(raw, "customerId", "customer_id", "customer")
        record_id = self._first(raw, "transactionId", "transaction_id", "id", "recordId")
        amount = self._float_or_none(self._first(raw, "transactionAmount", "amount"))
        date = self._first(raw, "transactionDate", "date")

        enrichment = {}
        for key in (
            "loyaltyPoints", "browsingSessionMinutes", "cartStatus",
            "merchantCategory", "sku", "productId", "productName",
            "stockQuantity", "reorderLevel", "availabilityStatus",
            "warehouseLocation", "lastUpdated",
        ):
            if key in raw:
                enrichment[key] = raw[key]

        return CanonicalRecord(
            source_system=source_system if source_system in {"ibm", "unisys"} else "unknown",
            entity=entity,
            customer_id=str(customer_id) if customer_id is not None else None,
            record_id=str(record_id) if record_id is not None else None,
            amount=amount,
            date=str(date) if date is not None else None,
            transaction_type=self._string_or_none(self._first(raw, "transactionType", "type")),
            merchant=self._string_or_none(self._first(raw, "merchant")),
            category=self._string_or_none(self._first(raw, "category")),
            enrichment=enrichment,
            raw=raw,
        )

    @staticmethod
    def _first(record: Dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in record and record[key] is not None:
                return record[key]
        return None

    @staticmethod
    def _float_or_none(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _string_or_none(value: Any) -> Optional[str]:
        return str(value) if value is not None else None

    @staticmethod
    def _summarize(records: List[CanonicalRecord], warnings: List[str]) -> NormalizationSummary:
        entities = sorted({record.entity for record in records})
        domain_warning = (
            "Do not add Unisys amount to IBM amount for spend totals; Unisys is enrichment."
        )
        if any(record.source_system == "unisys" for record in records):
            warnings.append(domain_warning)

        unique_warnings = list(dict.fromkeys(warnings))
        return NormalizationSummary(
            total_records=len(records),
            ibm_records=sum(1 for record in records if record.source_system == "ibm"),
            unisys_records=sum(1 for record in records if record.source_system == "unisys"),
            canonical_entities=entities,
            warnings=unique_warnings,
        )

    @staticmethod
    def _compact_for_llm(payload: Any) -> Any:
        if isinstance(payload, dict):
            compact = {}
            for key, value in list(payload.items())[:12]:
                compact[key] = NormalizationAgent._compact_for_llm(value)
            return compact
        if isinstance(payload, list):
            return [NormalizationAgent._compact_for_llm(item) for item in payload[:3]]
        return payload

    @staticmethod
    def _add_trace(
        trace: List[Dict[str, Any]],
        stage: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        trace.append(
            TraceEvent(
                timestamp=datetime.now(),
                stage=stage,
                message=message,
                metadata=metadata,
            ).model_dump(mode="json")
        )
