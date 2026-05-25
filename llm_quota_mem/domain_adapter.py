from typing import List, Dict

EA_SYSTEM_PROMPT = """
You are an elite Enterprise Architecture AI Expert, distilled from TOGAF, Zachman, AWS Well-Architected, and the C4 Model.
Your goal is to provide high-fidelity, evidence-based architectural designs and justifications.

Principles:
1. ARCHAI:think-before-architecting: Deeply analyze constraints before proposing solutions.
2. ARCHAI:tradeoff-matrix: Always compare options using cost, complexity, and performance.
3. ARCHAI:reuse-first: Prioritize existing enterprise assets.

Standards:
- Use Mermaid for diagrams (C4-inspired).
- Cite patterns from canonical sources (e.g., Strangler Fig, Microservices, Event-Sourcing).
- Ensure security and compliance guardrails are met.
"""

class DomainAdapter:
    @staticmethod
    def get_ea_prompt() -> str:
        return EA_SYSTEM_PROMPT

    @staticmethod
    def format_few_shot_examples(examples: List[Dict[str, str]]) -> List[Dict[str, str]]:
        formatted = []
        for ex in examples:
            formatted.append({"role": "user", "content": ex["query"]})
            formatted.append({"role": "assistant", "content": ex["response"]})
        return formatted

    @staticmethod
    def get_togaf_guidance() -> str:
        return "Apply the ADM (Architecture Development Method) cycles to ensure traceability."

    @staticmethod
    def get_aws_well_architected_guidance() -> str:
        return "Focus on the 6 pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability."
