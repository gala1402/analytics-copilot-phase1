from typing import TypedDict, List, Dict, Any

class Task(TypedDict, total=False):
    id: str
    intent: str
    question: str
    supported: bool
    requires: List[str]
    reason: str

class TaskResult(TypedDict, total=False):
    id: str
    intent: str
    output: str
    metadata: Dict[str, Any]
