"""
Catalog Repository - Data access layer (UPDATED FOR CONSOLIDATED DATABASE)

Commands  SQLite (zowe_catalog.db - consolidated)
Jobs / Workflows / Datasets  simulation_data folder
"""

import sqlite3
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import csv


BASE_DIR = Path(__file__).resolve().parents[2]

# Database is outside app/ - NOW USING CONSOLIDATED DATABASE
DB_PATH = BASE_DIR / "database" / "zowe_catalog.db"

# simulation_data is inside app/
APP_DIR = BASE_DIR / "app"
SIMULATION_DIR = APP_DIR / "simulation_data"

JOBS_DIR = SIMULATION_DIR / "jobs"
WORKFLOWS_DIR = SIMULATION_DIR / "workflows"
DATASETS_DIR = SIMULATION_DIR / "datasets"


class CatalogRepository:

    def __init__(self, db_path: str | None = None):
        self.db_path = Path(db_path) if db_path else DB_PATH

    # =========================================================
    # DATABASE CONNECTION
    # =========================================================

    def get_connection(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================
    # COMMANDS (From SQLite - CONSOLIDATED SCHEMA)
    # =========================================================

    def get_all_commands(self) -> List[Dict[str, Any]]:
        """Load commands from zowe_capability table (46 original catalog entries)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    zowe_command,
                    category,
                    command_family,
                    subsystem,
                    ibm_artifact,
                    operation,
                    access_pattern,
                    response_format,
                    intended_agent,
                    constraints,
                    execution_cost,
                    confidence_level
                FROM zowe_capability
                ORDER BY command_family, zowe_command
            """)

            rows = cursor.fetchall()
            commands = []
            
            for idx, row in enumerate(rows):
                command = {
                    "id": f"cmd-{idx+1:03d}",
                    "zowe_command": row["zowe_command"],
                    "category": row["category"],
                    "command_family": row["command_family"],
                    "subsystem": row["subsystem"],
                    "ibm_artifact": row["ibm_artifact"],
                    "operation": row["operation"],
                    "access_pattern": row["access_pattern"],
                    "response_format": row["response_format"],
                    "intended_agent": row["intended_agent"],
                    "constraints": row["constraints"] or "",
                    "execution_cost": row["execution_cost"],
                    "confidence_level": row["confidence_level"],
                }
                commands.append(command)

            return commands

    def get_commands_by_family(self, families: List[str]) -> List[Dict[str, Any]]:
        """Load commands filtered by command_family."""
        if not families:
            return []

        placeholders = ", ".join("?" for _ in families)
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT
                    zowe_command,
                    category,
                    command_family,
                    subsystem,
                    ibm_artifact,
                    artifact_granularity,
                    data_scope,
                    operation,
                    access_pattern,
                    response_format,
                    intended_agent,
                    constraints,
                    execution_cost,
                    confidence_level,
                    description,
                    output_file
                FROM zowe_capability
                WHERE command_family IN ({placeholders})
                ORDER BY command_family, zowe_command
                """,
                families,
            )

            return [dict(row) for row in cursor.fetchall()]

    # =========================================================
    # JOBS (From simulation_data/jobs)
    # =========================================================

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        return self._scan_directory(JOBS_DIR, "JCL")

    # =========================================================
    # WORKFLOWS (From simulation_data/workflows)
    # =========================================================

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        items = self._scan_directory(WORKFLOWS_DIR, "WORKFLOW")
        # Add workflow-specific fields
        for idx, item in enumerate(items):
            item["id"] = f"wf-{idx+1:03d}"
            item["steps"] = 3  # Default steps
            item["dependencies"] = []  # No dependencies
            item["status"] = "active"
            item["lastRun"] = datetime.now().isoformat()
        return items

    # =========================================================
    # DATASETS (From simulation_data/datasets)
    # =========================================================

    def get_all_datasets(self) -> List[Dict[str, Any]]:
        items = []
        if not DATASETS_DIR.exists():
            return items

        for file in DATASETS_DIR.iterdir():
            if file.is_file():
                # Try to get file size and record count
                size_bytes = file.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb > 0.1 else f"{int(size_bytes)} B"
                
                # Count records if it's a CSV
                record_count = 0
                if file.suffix == ".csv":
                    try:
                        with open(file, "r") as f:
                            record_count = sum(1 for _ in f) - 1  # -1 for header
                    except:
                        record_count = 0
                
                item = {
                    "id": f"ds-{file.stem}",
                    "name": file.stem,
                    "scope": "simulation",
                    "mainframe": "SIMULATED",
                    "type": "DATASET",
                    "accessLevel": "restricted",
                    "size": size_str,
                    "records": record_count,
                    "downloadUrl": f"/simulation_data/datasets/{file.name}"
                }
                items.append(item)

        return items

    # =========================================================
    # DIRECTORY SCANNER
    # =========================================================

    def _scan_directory(self, path: Path, artifact_type: str) -> List[Dict[str, Any]]:
        if not path.exists():
            return []

        items = []

        for file in path.iterdir():
            if file.is_file():
                items.append({
                    "name": file.stem,
                    "scope": "simulation",
                    "mainframe": "SIMULATED",
                    "type": artifact_type,
                    "accessLevel": "restricted",
                    "downloadUrl": f"/simulation_data/{path.name}/{file.name}"
                })

        return items

    # =========================================================
    # STATS
    # =========================================================

    def get_catalog_stats(self) -> Dict[str, Any]:
        return {
            "totalCommands": len(self.get_all_commands()),
            "totalJobs": len(self.get_all_jobs()),
            "totalWorkflows": len(self.get_all_workflows()),
            "totalDatasets": len(self.get_all_datasets()),
            "lastUpdated": datetime.now().isoformat()
        }

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def check_connection(self) -> Dict[str, Any]:
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")

            return {
                "status": "connected",
                "db_path": str(self.db_path),
                "database": "zowe_catalog.db (consolidated)"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "db_path": str(self.db_path)
            }
