"""
Execution Planner - Creates execution plan for selected commands
"""
from typing import List, Dict, Any, Optional


class ExecutionPlanner:
    """
    Plans execution sequence and strategy for commands
    
    TODO: Implement dependency resolution
    TODO: Add parallel execution planning
    TODO: Create rollback/recovery plans
    """
    
    def plan(self, commands: List[Dict[str, Any]], intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create execution plan for commands
        
        Args:
            commands: List of selected commands
            intent: Parsed intent with entities
            
        Returns:
            Execution plan dictionary
        """
        if not commands:
            return {
                "execution_sequence": [],
                "parallel_groups": [],
                "estimated_duration_seconds": 0,
                "rollback_plan": None
            }
        
        # Simple sequential plan for now
        execution_sequence = [
            {
                "command_id": cmd.get("id"),
                "command_name": cmd.get("name") or cmd.get("command_id"),
                "command": cmd.get("command") or cmd.get("zowe_command") or cmd.get("command_template"),
                "zowe_command": cmd.get("zowe_command") or cmd.get("command") or cmd.get("command_template"),
                "system": cmd.get("system", "ibm"),
                "category": cmd.get("category"),
                "command_family": cmd.get("command_family"),
                "operation": cmd.get("operation"),
                "risk_level": self._risk_level(cmd),
                "requires_approval": self._risk_level(cmd) == "CRITICAL",
                "order": idx + 1,
                "parameters": self._extract_parameters(cmd, intent),
                "expected_output": cmd.get("data_returned") or cmd.get("response_format")
            }
            for idx, cmd in enumerate(commands)
        ]
        
        return {
            "execution_sequence": execution_sequence,
            "parallel_groups": self._identify_parallel_groups(execution_sequence),
            "estimated_duration_seconds": len(commands) * 2,
            "rollback_plan": self._create_rollback_plan(execution_sequence)
        }
    
    def _extract_parameters(self, command: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Extract command parameters from intent filters and entities."""
        filters = intent.get("filters", {}) if isinstance(intent, dict) else {}
        params: Dict[str, Any] = {}

        for condition in filters.get("conditions", []) or []:
            if isinstance(condition, dict) and condition.get("field"):
                params[condition["field"]] = condition.get("value")

        time_range = filters.get("time_range")
        if isinstance(time_range, dict) and "date" not in params:
            params["date"] = time_range.get("start")

        entities = intent.get("entities", []) if isinstance(intent, dict) else []
        if entities:
            params["entities"] = entities

        return params
    
    def _identify_parallel_groups(self, sequence: List[Dict[str, Any]]) -> List[List[int]]:
        """Identify commands that can run in parallel - TODO: implement"""
        return []
    
    def _create_rollback_plan(self, sequence: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create rollback plan in case of failure."""
        reversible_steps = [
            step for step in sequence
            if step.get("operation") == "EXECUTE" and step.get("risk_level") != "LOW"
        ]
        if not reversible_steps:
            return None
        return {
            "strategy": "manual_review",
            "steps": [
                {
                    "after_step": step.get("order"),
                    "action": "review_and_compensate",
                    "reason": f"Command {step.get('command_name')} may have changed mainframe state",
                }
                for step in reversed(reversible_steps)
            ],
        }

    @staticmethod
    def _risk_level(command: Dict[str, Any]) -> str:
        explicit = command.get("risk_level")
        if explicit in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            return explicit

        text = " ".join(
            str(command.get(key, "")).lower()
            for key in ("zowe_command", "command", "command_template", "operation", "constraints")
        )
        cost = str(command.get("execution_cost", "")).upper()
        if any(word in text for word in ("delete", "purge", "drop", "uncatalog", "destroy")):
            return "CRITICAL"
        if any(word in text for word in ("cancel", "upload", "submit", "create", "start", "stop", "update")):
            return "HIGH" if cost == "HIGH" else "MEDIUM"
        if cost in {"LOW", "MEDIUM", "HIGH"}:
            return cost
        return "LOW"
