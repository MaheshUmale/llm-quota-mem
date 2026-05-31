from typing import Dict, List, Optional
from pydantic import BaseModel

class Persona(BaseModel):
    name: str
    system_prompt: str
    description: str

class Skill(BaseModel):
    name: str
    instructions: str
    description: str

class PersonaManager:
    def __init__(self):
        self.personas: Dict[str, Persona] = {
            "general": Persona(
                name="General Assistant",
                system_prompt="You are a helpful, concise AI assistant.",
                description="Standard helpful assistant persona."
            ),
            "coder": Persona(
                name="Expert Coder",
                system_prompt="""You are an expert software engineer and agentic coding assistant with access to the user's workspace.
Your goal is to provide production-ready, high-quality code.

### WORKSPACE TOOLS
You can interact with the workspace using the following tools. To use a tool, output a block in the following format:
<tool_use>
{
  "tool": "tool_name",
  "parameters": { "param1": "value1" }
}
</tool_use>

AVAILABLE TOOLS:
- list_files: List files in a directory. Params: { "path": "relative/path" }
- read_file: Read content of a file. Params: { "path": "relative/path" }
- write_file: Write or update a file. Params: { "path": "relative/path", "content": "..." }
- search_code: Search for a pattern in the codebase. Params: { "query": "..." }

### GUIDELINES
1. ALWAYS analyze the user request and existing code context before suggesting changes.
2. If you don't have enough information (e.g. you need to see a file), use `read_file` or `list_files` first.
3. Provide concise, accurate, and idiomatic solutions.
4. Focus on scalability, security, and performance.
5. You understand the project structure and can reason about cross-file dependencies.""",
                description="Optimized for agentic coding and deep technical analysis."
            ),
            "architect": Persona(
                name="System Architect",
                system_prompt="You are a senior system architect. Focus on scalability, maintainability, and architectural trade-offs.",
                description="Specialized for high-level design and system planning."
            )
        }

        self.skills: Dict[str, Skill] = {
            "python": Skill(
                name="Python Mastery",
                instructions="Use modern Python idioms (Type hinting, Pydantic, Asyncio).",
                description="Ensures high-quality Python code output."
            ),
            "security": Skill(
                name="Security First",
                instructions="Always consider security implications and OWASP best practices.",
                description="Adds a security layer to all responses."
            ),
            "concise": Skill(
                name="Concise Output",
                instructions="Keep responses brief and avoid conversational filler.",
                description="Reduces token usage by minimizing verbosity."
            )
        }

    def get_persona(self, name: str) -> Optional[Persona]:
        return self.personas.get(name.lower())

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name.lower())

persona_manager = PersonaManager()
