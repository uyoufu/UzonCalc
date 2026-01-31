import asyncio
from typing import Dict, Any, Optional
from .runner import SandboxRunner
from .models import ExecutionResult

class SandboxManager:
    _instances: Dict[str, SandboxRunner] = {}

    @classmethod
    def execute_script(cls, script_path: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Start execution of a script.
        Returns the execution_id.
        """
        runner = SandboxRunner(script_path, params)
        execution_id = runner.start()
        cls._instances[execution_id] = runner
        
        # Cleanup routine could be scheduled here (e.g. remove after 1 hour)
        return execution_id

    @classmethod
    def get_status(cls, execution_id: str) -> ExecutionResult:
        """Get status of an execution."""
        runner = cls._instances.get(execution_id)
        if not runner:
            raise ValueError(f"Execution {execution_id} not found")
        return runner.get_state()

    @classmethod
    def submit_input(cls, execution_id: str, data: Dict[str, Any]) -> ExecutionResult:
        """Submit user input to a paused execution."""
        runner = cls._instances.get(execution_id)
        if not runner:
            raise ValueError(f"Execution {execution_id} not found")
        
        runner.submit_input(data)
        return runner.get_state()
        
    @classmethod
    def terminate(cls, execution_id: str):
        """Force terminate an execution."""
        if execution_id in cls._instances:
             cls._instances[execution_id].cancel()
             del cls._instances[execution_id]

    @classmethod
    def cleanup_finished(cls):
        """Remove finished executions from memory."""
        to_remove = []
        for eid, runner in cls._instances.items():
            state = runner.get_state()
            if state.status in ["completed", "failed"]:
                to_remove.append(eid)
        
        for eid in to_remove:
            del cls._instances[eid]
