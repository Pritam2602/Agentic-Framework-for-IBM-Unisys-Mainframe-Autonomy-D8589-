"""
Catalog Repository - Data access layer

Commands  SQLite (zowe_capability_catalog.db)
Jobs / Workflows / Datasets  simulation_data folder
"""

import sqlite3
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import csv


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
            # Get commands with their preconditions
            cursor = conn.execute("""
                SELECT 
                    id,
                    zowe_command,
                    category,
                    command_family,
                    description,
                    response_format,
                    output_file
                FROM zowe_capability
                ORDER BY id
            """)

            rows = cursor.fetchall()
            
            # Get preconditions map
            precond_cursor = conn.execute("""
                SELECT capability_id, precondition
                FROM zowe_capability_precondition
            """)
            
            preconditions_map: Dict[int, List[str]] = {}
            for precond_row in precond_cursor.fetchall():
                capability_id = precond_row["capability_id"]
                if capability_id not in preconditions_map:
                    preconditions_map[capability_id] = []
                preconditions_map[capability_id].append(precond_row["precondition"])

            commands = []
            now = datetime.now()
            
            for row in rows:
                capability_id = row["id"]
                zowe_command = row["zowe_command"]
                category = row["category"]
                command_family = row["command_family"]
                description = row["description"]
                response_format = row["response_format"]
                output_file = row["output_file"]
                
                # Map response_format to outputType
                output_type = "JSON" if response_format == "JSON" else "TEXT"
                
                # Get preconditions for this command
                preconditions = preconditions_map.get(capability_id, [])
                
                # Map category to type
                type_mapping = {
                    "batch": "batch",
                    "workflow": "workflow",
                    "metadata": "metadata",
                    "database": "query",
                    "query": "query",
                    "system": "system",
                    "data": "system",
                    "tso": "system",
                    "zosmf": "system",
                    "ssh": "system",
                    "console": "system",
                    "files": "system"
                }
                command_type = type_mapping.get(category.lower(), "system")
                
                # Create command dict (matching CommandModel schema)
                command = {
                    "id": str(capability_id),
                    "name": zowe_command,
                    "type": command_type,
                    "family": command_family,
                    "preconditions": preconditions,
                    "outputType": output_type,
                    "outputFile": output_file if output_file else None,
                    "description": description or "",
                    "createdAt": now.isoformat(),
                    "updatedAt": now.isoformat()
                }
                
                commands.append(command)

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
                "db_path": str(self.db_path)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "db_path": str(self.db_path)
            }
