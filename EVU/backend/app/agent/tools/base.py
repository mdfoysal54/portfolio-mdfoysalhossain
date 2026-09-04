from dataclasses import dataclass


@dataclass
class ToolExecution:
    name: str
    input: str
    output: str
    success: bool = True