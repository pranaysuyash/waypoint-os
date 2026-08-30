"""
src/agents/visualizer.py — Agent execution DAG and subagent communication visualizer.

Grounding doctrine:
- PER-0700 (Agentic Systems Architect): Visual clarity into multi-agent execution graphs and step dependencies.
"""

from __future__ import annotations

from typing import List
from src.agents.checkpoints import ExecutionCheckpoint


class AgentExecutionVisualizer:
    """Generates Mermaid diagrams representing agent step executions and checkpoints."""

    @staticmethod
    def generate_mermaid_flow(
        run_id: str,
        checkpoints: List[ExecutionCheckpoint],
        current_status: str = "COMPLETED",
    ) -> str:
        """
        Generate a Mermaid flowchart diagram showing step progression and tool execution outputs.
        """
        lines = [
            "```mermaid",
            "flowchart TD",
            f"    Start([Run ID: {run_id}]) --> Step_0",
        ]

        if not checkpoints:
            lines.append(f"    Step_0[No Checkpoints Recorded] --> Finish([{current_status}])")
            lines.append("```")
            return "\n".join(lines)

        for i, cp in enumerate(checkpoints):
            step_id = f"Step_{cp.step_index}"
            step_label = f"Step {cp.step_index}: {cp.step_name}"
            tool_names = list(cp.tool_outputs.keys())
            if tool_names:
                step_label += f"<br/>Tools: {', '.join(tool_names)}"

            lines.append(f'    {step_id}["{step_label}"]')

            if i > 0:
                prev_id = f"Step_{checkpoints[i-1].step_index}"
                lines.append(f"    {prev_id} --> {step_id}")

        last_id = f"Step_{checkpoints[-1].step_index}"
        lines.append(f"    {last_id} --> Finish([{current_status}])")
        lines.append("```")
        return "\n".join(lines)
