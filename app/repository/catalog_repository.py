"""
Catalog Repository - Data access layer

Commands → SQLite (zowe_capability_catalog.db)
Jobs / Workflows / Datasets → simulation_data folder
"""

import sqlite3
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[2]

# Database is outside app/
DB_PATH = BASE_DIR / "database" / "zowe_capability_catalog.db"

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
    # COMMANDS (From SQLite)
    # =========================================================

    def get_all_commands(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    zowe_command,
                    category,
                    command_family,
                    description,
                    data_scope,
                    mutability,
                    idempotent,
                    execution_cost,
                    ibm_artifact,
                    data_returned,
                    intended_agent,
                    constraints,
                    output_file
                FROM zowe_capability
            """)

            rows = cursor.fetchall()

            commands = []
            for row in rows:
                commands.append({
                    "zowe_command": row["zowe_command"],
                    "category": row["category"],
                    "command_family": row["command_family"],
                    "description": row["description"],
                    "data_scope": row["data_scope"],
                    "mutability": row["mutability"],
                    "idempotent": bool(row["idempotent"]),
                    "cost": row["execution_cost"],
                    "ibm_artifact": row["ibm_artifact"],
                    "data_returned": row["data_returned"],
                    "intended_agent": row["intended_agent"],
                    "constraints": row["constraints"],
                    "output_file": row["output_file"]
                })

            return commands

    # =========================================================
    # JOBS (From simulation_data/jobs)
    # =========================================================

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        return self._scan_directory(JOBS_DIR, "JCL")

    # =========================================================
    # WORKFLOWS (From simulation_data/workflows)
    # =========================================================

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        return self._scan_directory(WORKFLOWS_DIR, "WORKFLOW")

    # =========================================================
    # DATASETS (From simulation_data/datasets)
    # =========================================================

    def get_all_datasets(self) -> List[Dict[str, Any]]:
        return self._scan_directory(DATASETS_DIR, "DATASET")

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
                "db_path": str(self.db_path)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "db_path": str(self.db_path)
            }
