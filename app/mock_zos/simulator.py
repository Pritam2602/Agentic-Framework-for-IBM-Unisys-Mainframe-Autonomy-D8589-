"""Local mock z/OS simulator for safe Zowe command execution demos."""

from __future__ import annotations

import fnmatch
import json
import shlex
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
IBM_DATA_DIR = ROOT / "data" / "ibm"


class MockZOSSimulator:
    """Executes a safe subset of Zowe CLI commands against local mock data."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or IBM_DATA_DIR
        self.datasets = {
            "AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS": {
                "entity": "transaction",
                "path": self.data_dir / "transactions.json",
                "record_id": "transactionId",
            },
            "AWS.M2.CARDDEMO.ACCOUNT.VSAM.KSDS": {
                "entity": "account",
                "path": self.data_dir / "accounts.json",
                "record_id": "accountId",
            },
            "AWS.M2.CARDDEMO.CUSTOMER.VSAM.KSDS": {
                "entity": "customer",
                "path": self.data_dir / "customers.json",
                "record_id": "customerId",
            },
        }

    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a mock Zowe command."""
        parameters = parameters or {}
        tokens = self._tokenize(command)
        if not tokens or tokens[0].lower() != "zowe":
            return self._error(command, "Only zowe commands are supported by mock z/OS")

        normalized = " ".join(token.lower() for token in tokens[:4])
        if normalized.startswith("zowe files view ds"):
            dataset = self._last_arg(tokens)
            return self._view_dataset(command, dataset, parameters)
        if normalized.startswith("zowe files list ds"):
            pattern = self._last_arg(tokens)
            return self._list_datasets(command, pattern)
        if normalized.startswith("zowe zos-jobs submit"):
            return self._submit_job(command, tokens, parameters)
        if normalized.startswith("zowe zos-jobs list"):
            return self._list_jobs(command)
        if normalized.startswith("zowe zos-jobs view"):
            return self._view_job(command, tokens)
        if normalized.startswith("zowe zos-workflows list"):
            return self._list_workflows(command)
        if normalized.startswith("zowe zos-workflows view"):
            return self._view_workflow(command, tokens)
        if normalized.startswith("zowe zosmf info"):
            return self._zosmf_info(command)

        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OS",
            "command": command,
            "message": "Command accepted by mock z/OS simulator; no state change performed.",
            "data": {},
        }

    @staticmethod
    def _tokenize(command: str) -> List[str]:
        try:
            return shlex.split(command)
        except ValueError:
            return command.split()

    @staticmethod
    def _last_arg(tokens: List[str]) -> str:
        return tokens[-1] if tokens else ""

    def _view_dataset(
        self,
        command: str,
        dataset: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        dataset = dataset.strip("\"'")
        dataset_info = self._resolve_dataset(dataset)
        if not dataset_info:
            return self._error(command, f"Dataset not found in mock catalog: {dataset}")

        records = self._load_records(dataset_info["path"])
        filtered = self._filter_records(records, parameters)
        entity = dataset_info["entity"]

        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OS",
            "source": "ibm",
            "entity": entity,
            "command": command,
            "dataset": dataset,
            "record_format": "JSON",
            "count": len(filtered),
            "data": filtered,
            "spool": {
                "ddName": "SYSOUT",
                "content": f"MOCK Z/OS READ {len(filtered)} {entity.upper()} RECORD(S)",
            },
            "note": "Mock z/OS dataset read; IBM transaction amounts remain financial source of truth.",
        }

    def _list_datasets(self, command: str, pattern: str) -> Dict[str, Any]:
        raw_pattern = pattern.strip("\"'") or "*"
        glob_pattern = raw_pattern.replace("%", "*")
        datasets = [
            {
                "name": name,
                "entity": info["entity"],
                "volume": "M2VOL1",
                "organization": "VSAM.KSDS",
            }
            for name, info in self.datasets.items()
            if fnmatch.fnmatch(name, glob_pattern)
            or fnmatch.fnmatch(name, f"{glob_pattern}*")
            or raw_pattern in name
        ]
        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OS",
            "source": "ibm",
            "command": command,
            "datasets": datasets,
            "total_count": len(datasets),
        }

    def _submit_job(
        self,
        command: str,
        tokens: List[str],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        target = self._last_arg(tokens).strip("\"'")
        job_name = parameters.get("job_name") or Path(target).stem[:8].upper() or "MOCKJOB"
        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OS",
            "source": "ibm",
            "command": command,
            "job_id": "JOB12345",
            "job_name": job_name,
            "return_code": "CC 0000",
            "submitted_at": datetime.now().isoformat(),
            "message": "Mock JES job submitted and completed.",
        }

    @staticmethod
    def _list_jobs(command: str) -> Dict[str, Any]:
        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OS",
            "source": "ibm",
            "command": command,
            "jobs": [
                {"jobId": "JOB12345", "jobName": "MOCKJOB", "status": "OUTPUT", "retcode": "CC 0000"},
                {"jobId": "JOB12346", "jobName": "CARDRPT", "status": "ACTIVE", "retcode": None},
            ],
        }

    @staticmethod
    def _view_job(command: str, tokens: List[str]) -> Dict[str, Any]:
        job_id = tokens[-1] if len(tokens) > 4 else "JOB12345"
        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OS",
            "source": "ibm",
            "command": command,
            "job_id": job_id,
            "job_status": "OUTPUT",
            "return_code": "CC 0000",
            "log": "IEF142I MOCKJOB STEP1 - STEP WAS EXECUTED - COND CODE 0000",
        }

    @staticmethod
    def _list_workflows(command: str) -> Dict[str, Any]:
        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OSMF",
            "source": "ibm",
            "command": command,
            "workflows": [
                {"workflowId": "WF1001", "name": "account_lifecycle", "status": "CREATED"},
                {"workflowId": "WF1002", "name": "statement_generation", "status": "COMPLETE"},
            ],
        }

    @staticmethod
    def _view_workflow(command: str, tokens: List[str]) -> Dict[str, Any]:
        workflow_id = tokens[-1] if len(tokens) > 4 else "WF1001"
        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OSMF",
            "source": "ibm",
            "command": command,
            "workflowId": workflow_id,
            "workflow_status": "COMPLETE",
            "steps": 3,
        }

    @staticmethod
    def _zosmf_info(command: str) -> Dict[str, Any]:
        return {
            "status": "completed",
            "mode": "safe_mock",
            "platform": "IBM z/OSMF",
            "source": "ibm",
            "command": command,
            "zosmf": {
                "version": "2.5.0-mock",
                "services": ["files", "jobs", "workflows", "console"],
            },
        }

    def _resolve_dataset(self, dataset: str) -> Optional[Dict[str, Any]]:
        if dataset in self.datasets:
            return self.datasets[dataset]
        upper = dataset.upper()
        if "TRAN" in upper:
            return self.datasets["AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS"]
        if "ACCT" in upper or "ACCOUNT" in upper:
            return self.datasets["AWS.M2.CARDDEMO.ACCOUNT.VSAM.KSDS"]
        if "CUST" in upper or "CUSTOMER" in upper:
            return self.datasets["AWS.M2.CARDDEMO.CUSTOMER.VSAM.KSDS"]
        return None

    @staticmethod
    def _load_records(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig") as file:
            payload = json.load(file)
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _filter_records(
        records: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        customer_id = parameters.get("customerId") or parameters.get("customer_id")
        date = parameters.get("date")
        filtered = records
        if customer_id is not None:
            filtered = [
                record for record in filtered
                if str(record.get("customerId") or record.get("customer_id")) == str(customer_id)
            ]
        if date is not None:
            filtered = [
                record for record in filtered
                if str(record.get("transactionDate") or record.get("date")) == str(date)
            ]
        return filtered

    @staticmethod
    def _error(command: str, message: str) -> Dict[str, Any]:
        return {
            "status": "failed",
            "mode": "safe_mock",
            "platform": "IBM z/OS",
            "command": command,
            "error": message,
        }
