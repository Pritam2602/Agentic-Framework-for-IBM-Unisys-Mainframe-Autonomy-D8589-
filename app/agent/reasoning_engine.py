"""
Reasoning Engine - Orchestrates the agent reasoning pipeline through all stages
"""
from typing import Dict, Any, List
from datetime import datetime
from app.models.schemas import TraceEvent
from app.agent.intent_parser import IntentParser
from app.agent.capability_matcher import CapabilityMatcher
from app.agent.command_selector import CommandSelector
from app.agent.execution_planner import ExecutionPlanner


class ReasoningEngine:
    """
    Core orchestrator for agent reasoning pipeline
    
    Flow:
    1. Parse Intent
    2. Match Capabilities
    3. Select Commands
    4. Plan Execution
    5. Build trace for observability
    """
    
    def __init__(
        self,
        intent_parser: IntentParser,
        capability_matcher: CapabilityMatcher,
        command_selector: CommandSelector,
        execution_planner: ExecutionPlanner
    ):
        self.intent_parser = intent_parser
        self.capability_matcher = capability_matcher
        self.command_selector = command_selector
        self.execution_planner = execution_planner
        self.execution_trace: List[TraceEvent] = []
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user query through complete reasoning pipeline
        
        Args:
            query: User natural language query
            context: Optional context from previous interactions
            
        Returns:
            Dictionary with reasoning results and trace
        """
        self.execution_trace = []
        
        # Stage 1: Intent Parsing
        self._add_trace("intent_parsing", "Analyzing user query to extract intent and entities")
        intent = self.intent_parser.parse(query, context)
        self._add_trace(
            "intent_parsing",
            f"Identified intent: {intent['intent']} (confidence: {intent['confidence']:.2f})",
            metadata=intent
        )
        
        # Stage 2: Capability Matching
        self._add_trace("capability_matching", "Matching intent to available agent capabilities")
        capabilities = self.capability_matcher.match(intent)
        self._add_trace(
            "capability_matching",
            f"Matched capabilities: {', '.join(capabilities) if capabilities else 'None'}",
            metadata={"capabilities": capabilities}
        )
        
        # Stage 3: Command Selection
        self._add_trace("command_selection", "Selecting appropriate commands from catalog")
        commands = self.command_selector.select(capabilities, intent)
        self._add_trace(
            "command_selection",
            f"Selected {len(commands)} command(s) for execution",
            metadata={"command_count": len(commands), "commands": [c.get("name") for c in commands]}
        )
        
        # Stage 4: Execution Planning
        self._add_trace("execution_planning", "Creating execution plan with dependencies and sequencing")
        execution_plan = self.execution_planner.plan(commands, intent)
        self._add_trace(
            "execution_planning",
            f"Execution plan ready. Estimated duration: {execution_plan['estimated_duration_seconds']}s",
            metadata=execution_plan
        )
        
        return {
            "intent": intent,
            "capabilities": capabilities,
            "commands": commands,
            "execution_plan": execution_plan,
            "execution_trace": [trace.model_dump() for trace in self.execution_trace]
        }
    
    def _add_trace(self, stage: str, message: str, metadata: Dict[str, Any] = None):
        """Add trace event to execution trace"""
        trace = TraceEvent(
            timestamp=datetime.now(),
            stage=stage,
            message=message,
            metadata=metadata
        )
        self.execution_trace.append(trace)
    
    def get_trace(self) -> List[TraceEvent]:
        """Return current execution trace"""
        return self.execution_trace
