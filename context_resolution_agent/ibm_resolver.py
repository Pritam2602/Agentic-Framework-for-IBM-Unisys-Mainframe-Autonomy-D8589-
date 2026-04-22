"""
ibm_resolver.py - IBM Mainframe Context Resolver

Resolves WHERE data exists on the IBM side by consulting:
1. ProLeap COBOL JSON outputs (tools/cobol-jcl-parser/output-final-cobol/)
2. JCL parsed JSON outputs (tools/cobol-jcl-parser/output-final-jcl/)
3. Combined output (tools/cobol-jcl-parser/combined_output.json)

Uses REAL parsed output from the reference ProLeap COBOL Parser + JCL Parser.
DOES NOT execute anything. Only resolves metadata.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .schemas import IBMContext

logger = logging.getLogger(__name__)

# Paths to real parsed outputs
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "cobol-jcl-parser"
COBOL_OUTPUT_DIR = TOOLS_DIR / "output-final-cobol"
JCL_OUTPUT_DIR = TOOLS_DIR / "output-final-jcl"
COMBINED_OUTPUT = TOOLS_DIR / "combined_output.json"


class IBMContextResolver:
    """
    Resolves IBM mainframe context using actual ProLeap + JCL parser outputs.

    Loads the pre-parsed COBOL and JCL JSON files from the CardDemo dataset
    and resolves entity → program → JCL job → datasets.
    """

    def __init__(self):
        self._cobol_cache: Dict[str, Dict[str, Any]] = {}
        self._jcl_cache: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _load_catalogs(self):
        """Load all parsed COBOL and JCL JSON files"""
        if self._loaded:
            return

        # Load COBOL outputs
        if COBOL_OUTPUT_DIR.exists():
            for json_file in COBOL_OUTPUT_DIR.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    program_id = data.get("program_id", json_file.stem)
                    self._cobol_cache[program_id] = data
                except Exception as e:
                    logger.error(f"Failed to load COBOL output {json_file}: {e}")

        # Load JCL outputs
        if JCL_OUTPUT_DIR.exists():
            for json_file in JCL_OUTPUT_DIR.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    job_name = data.get("job_name", json_file.stem)
                    self._jcl_cache[job_name] = data
                except Exception as e:
                    logger.error(f"Failed to load JCL output {json_file}: {e}")

        self._loaded = True
        logger.info(
            f"[IBM Resolver] Loaded {len(self._cobol_cache)} COBOL programs, "
            f"{len(self._jcl_cache)} JCL jobs"
        )

    def resolve(self, entity: str, attributes: list = None) -> Optional[IBMContext]:
        """
        Resolve IBM context for an entity.

        Args:
            entity: Entity name (e.g., "transaction", "account", "customer", "shopping")
            attributes: Optional list of specific attributes needed

        Returns:
            IBMContext with resolved metadata, or None if not found
        """
        self._load_catalogs()
        logger.info(f"[IBM Resolver] Resolving context for entity: {entity}")

        # Step 1: Find relevant COBOL programs by matching entity to programs
        programs = self._find_programs_for_entity(entity)
        if not programs:
            logger.warning(f"[IBM Resolver] No COBOL programs found for entity: {entity}")
            return None

        primary = programs[0]
        program_id = primary.get("program_id", "")
        job_hint = self._find_jobs_for_entity(entity)

        # Step 2: Find JCL jobs that execute this program
        jcl_jobs = self._find_jobs_for_program(program_id)
        jcl_job_name = None
        jcl_steps = []

        if jcl_jobs:
            job = jcl_jobs[0]
            jcl_job_name = job.get("job_name", "")
            jcl_steps = job.get("steps", [])

        if job_hint and self._is_transaction_like(entity):
            hinted_program = self._extract_program_from_job(job_hint)
            if hinted_program:
                summary = primary.get("summary", {})
                primary = {
                    **primary,
                    "program_id": hinted_program,
                    "summary": {
                        **summary,
                        "type": "batch/JCL-resolved",
                        "purpose": "Resolved from JCL transaction datasets and steps",
                    },
                }
                program_id = hinted_program
            jcl_job_name = job_hint.get("job_name", "")
            jcl_steps = job_hint.get("steps", [])

        # Step 3: Collect all datasets
        all_datasets = []
        # From JCL steps
        for step in jcl_steps:
            for ds in step.get("datasets", []):
                dsn = ds.get("dsn", "")
                if dsn and dsn not in all_datasets:
                    all_datasets.append(dsn)

        # From COBOL file definitions
        for f in primary.get("files", []):
            fname = f.get("file_name", "")
            if fname and fname not in all_datasets:
                all_datasets.append(fname)

        primary_dataset = self._select_primary_dataset(entity, all_datasets)

        # Step 4: Extract variables
        variables = primary.get("variables", [])

        # Step 5: I/O operations
        io_operations = primary.get("io_operations", {})

        # Step 6: Build summary info  
        summary = primary.get("summary", {})
        program_name = f"{program_id} ({summary.get('type', 'unknown')} - {summary.get('purpose', '')})"

        # Step 7: Get copybooks and calls
        copybooks = primary.get("copybooks", [])
        calls = primary.get("calls", [])

        return IBMContext(
            program=program_id,
            program_name=program_name,
            dataset=primary_dataset,
            all_datasets=all_datasets,
            jcl_job=jcl_job_name,
            jcl_steps=jcl_steps,
            zowe_commands=[],
            variables=variables[:20],  # Limit to first 20 for readability
            io_operations=io_operations,
        )

    def _find_programs_for_entity(self, entity: str) -> List[Dict[str, Any]]:
        """
        Find COBOL programs matching an entity domain.

        Uses keyword matching on program variables, files, and IO operations:
        - "transaction" → programs with TRANSACT/TRAN in files/variables
        - "account" → programs with ACCT/ACCOUNT in files/variables
        - "customer" → programs with CUST in files/variables
        """
        entity_lower = entity.lower()

        # Direct mapping for known CardDemo entities
        ENTITY_KEYWORDS = {
            "transaction": ["TRANSACT", "TRAN", "TRX", "TRXFL"],
            "shopping": ["TRANSACT", "TRAN", "TRX", "TRXFL"],
            "shopping_data": ["TRANSACT", "TRAN", "TRX", "TRXFL"],
            "account": ["ACCT", "ACCOUNT", "ACCTDATA", "ACCTFILE"],
            "customer": ["CUST", "CUSTDATA", "CUSTFILE"],
            "card": ["CARD", "CARDXREF", "CARDFILE"],
        }

        keywords = ENTITY_KEYWORDS.get(entity_lower, [entity_lower.upper()])
        matches = []

        for program_id, data in self._cobol_cache.items():
            score = 0

            # Check file names
            for f in data.get("files", []):
                fname = f.get("file_name", "").upper()
                if any(kw in fname for kw in keywords):
                    score += 3

            # Check IO operations
            for read in data.get("io_operations", {}).get("reads", []):
                if any(kw in read.upper() for kw in keywords):
                    score += 2
            for write in data.get("io_operations", {}).get("writes", []):
                if any(kw in write.upper() for kw in keywords):
                    score += 2

            # Check variable names (top-level only)
            for var in data.get("variables", [])[:30]:
                vname = var.get("name", "").upper()
                if any(kw in vname for kw in keywords):
                    score += 1
                    break  # One match is enough

            # Check summary
            summary = data.get("summary", {})
            summary_type = str(summary.get("type", "")).lower()
            for inp in summary.get("inputs", []):
                if any(kw in inp.upper() for kw in keywords):
                    score += 2
            for out in summary.get("outputs", []):
                if any(kw in out.upper() for kw in keywords):
                    score += 2

            # Prefer programs that actually touch datasets over generic online screens
            if summary_type.startswith("batch"):
                score += 3
            if data.get("files"):
                score += 2
            if data.get("io_operations", {}).get("reads"):
                score += 2
            if data.get("io_operations", {}).get("writes"):
                score += 1

            if score > 0:
                matches.append((score, data))

        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches]

    def _find_jobs_for_program(self, program_id: str) -> List[Dict[str, Any]]:
        """Find JCL jobs that execute a given COBOL program"""
        jobs = []
        for job_name, job_data in self._jcl_cache.items():
            for step in job_data.get("steps", []):
                if step.get("program", "").upper() == program_id.upper():
                    jobs.append(job_data)
                    break
        return jobs

    def _find_jobs_for_entity(self, entity: str) -> Optional[Dict[str, Any]]:
        """Find the best JCL job for an entity based on datasets and step programs."""
        entity_lower = entity.lower()
        keywords = {
            "transaction": ["TRANSACT", "TRX", "DALYTRAN", "SYSTRAN", "TRANREPT", "POSTTRAN"],
            "shopping": ["TRANSACT", "TRX", "DALYTRAN", "SYSTRAN", "TRANREPT", "POSTTRAN"],
            "shopping_data": ["TRANSACT", "TRX", "DALYTRAN", "SYSTRAN", "TRANREPT", "POSTTRAN"],
            "account": ["ACCTDATA", "ACCT", "READACCT"],
            "customer": ["CUSTDATA", "CUST"],
        }.get(entity_lower, [entity_lower.upper()])

        best_match = None
        best_score = 0

        for job_data in self._jcl_cache.values():
            score = 0
            job_name = str(job_data.get("job_name", "")).upper()

            if any(keyword in job_name for keyword in keywords):
                score += 4

            for step in job_data.get("steps", []):
                program = str(step.get("program", "")).upper()
                if any(keyword in program for keyword in keywords):
                    score += 5

                for dataset in step.get("datasets", []):
                    dsn = str(dataset.get("dsn", "")).upper()
                    if any(keyword in dsn for keyword in keywords):
                        score += 6
                    if self._is_transaction_like(entity) and "TRANSACT.VSAM.KSDS" in dsn:
                        score += 8

            if score > best_score:
                best_score = score
                best_match = job_data

        return best_match

    @staticmethod
    def _extract_program_from_job(job_data: Dict[str, Any]) -> Optional[str]:
        """Pick the first non-utility step program from a JCL job."""
        utility_programs = {"IDCAMS", "IEFBR14", "SORT", "REPROC", "SDSF", "IEBGENER"}
        for step in job_data.get("steps", []):
            program = str(step.get("program", "")).upper()
            if program and program not in utility_programs:
                return program
        for step in job_data.get("steps", []):
            program = str(step.get("program", "")).upper()
            if program:
                return program
        return None

    @staticmethod
    def _is_transaction_like(entity: str) -> bool:
        return entity.lower() in {"transaction", "shopping", "shopping_data"}

    def _select_primary_dataset(self, entity: str, datasets: List[str]) -> Optional[str]:
        """Prefer the most semantically relevant dataset for the resolved entity."""
        if not datasets:
            return None

        if self._is_transaction_like(entity):
            for dataset in datasets:
                if "TRANSACT" in dataset.upper():
                    return dataset

        for dataset in datasets:
            if "VSAM.KSDS" in dataset.upper():
                return dataset

        return datasets[0]

    def get_all_programs(self) -> List[str]:
        """Get all loaded COBOL program IDs"""
        self._load_catalogs()
        return list(self._cobol_cache.keys())

    def get_all_jobs(self) -> List[str]:
        """Get all loaded JCL job names"""
        self._load_catalogs()
        return list(self._jcl_cache.keys())

    def get_program_details(self, program_id: str) -> Optional[Dict[str, Any]]:
        """Get full details for a specific COBOL program"""
        self._load_catalogs()
        return self._cobol_cache.get(program_id)

    def get_job_details(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Get full details for a specific JCL job"""
        self._load_catalogs()
        return self._jcl_cache.get(job_name)
