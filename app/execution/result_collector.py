"""
Result Collector - Collects and aggregates execution results
"""
from typing import List, Dict, Any
from datetime import datetime
from app.models.schemas import TraceEvent, CanonicalOutput


class ResultCollector:
    """Collects results from executors and formats for agent response"""
    
    def collect(
        self,
        execution_results: List[Dict[str, Any]],
        reasoning_trace: List[TraceEvent]
    ) -> Dict[str, Any]:
        """
        Collect and aggregate execution results
        
        Args:
            execution_results: List of results from executors
            reasoning_trace: Trace from reasoning engine
            
        Returns:
            Aggregated result with trace
        """
        aggregated_data = self._aggregate_results(execution_results)
        
        canonical_output = CanonicalOutput(
            type="json",
            data=aggregated_data
        )
        
        # Add execution trace events
        full_trace = reasoning_trace.copy()
        for result in execution_results:
            trace_event = TraceEvent(
                timestamp=datetime.now(),
                stage="execution",
                message=f"Executed command: {result.get('command', 'unknown')}",
                metadata=result
            )
            full_trace.append(trace_event)
        
        collection_trace = TraceEvent(
            timestamp=datetime.now(),
            stage="result_collection",
            message=f"Collected results from {len(execution_results)} execution(s)",
            metadata={"result_count": len(execution_results)}
        )
        full_trace.append(collection_trace)
        
        return {
            "canonical_output": canonical_output,
            "execution_trace": full_trace,
            "summary": self._create_summary(execution_results)
        }
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple execution results"""
        if len(results) == 1:
            return results[0]
        
        return {
            "results": results,
            "total_executions": len(results),
            "successful": sum(1 for r in results if r.get("status") == "completed"),
            "failed": sum(1 for r in results if r.get("status") == "failed")
        }
    
    def _create_summary(self, results: List[Dict[str, Any]]) -> str:
        """Create human-readable summary"""
        successful = sum(1 for r in results if r.get("status") == "completed")
        total = len(results)
        return f"Executed {total} command(s). {successful} successful."
