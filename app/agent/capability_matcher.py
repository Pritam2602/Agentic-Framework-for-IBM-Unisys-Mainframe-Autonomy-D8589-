"""
Capability Matcher - Maps user intent to available agent capabilities
"""
from typing import List, Dict, Any


class CapabilityMatcher:
    """
    Matches parsed intent to available agent capabilities
    
    TODO: Implement semantic similarity matching
    TODO: Add confidence scoring per capability
    TODO: Handle multi-capability scenarios
    """
    
    def __init__(self, available_capabilities: List[str]):
        """
        Initialize with available capabilities
        
        Args:
            available_capabilities: List of capability names the agent supports
        """
        self.capabilities = available_capabilities
        
        # Intent to capability mapping
        self.intent_capability_map = {
            "list_jobs": ["JCL Execution", "Job Management"],
            "list_datasets": ["Dataset Management"],
            "list_workflows": ["Workflow Orchestration"],
            "list_commands": ["Command Catalog Access"],
            "submit_job": ["JCL Execution", "Job Management"],
            "execute_workflow": ["Workflow Orchestration"],
        }
    
    def match(self, intent: Dict[str, Any]) -> List[str]:
        """
        Match intent to capabilities
        
        Args:
            intent: Parsed intent from IntentParser
            
        Returns:
            List of matched capability names
        """
        intent_type = intent.get("intent", "")
        confidence = intent.get("confidence", 0.0)
        
        # Low confidence - return empty
        if confidence < 0.5:
            return []
        
        # Get capabilities for this intent
        matched_capabilities = self.intent_capability_map.get(intent_type, [])
        
        # Filter to only available capabilities
        available_matches = [
            cap for cap in matched_capabilities 
            if cap in self.capabilities
        ]
        
        return available_matches
    
    def get_all_capabilities(self) -> List[str]:
        """Return all available capabilities"""
        return self.capabilities
