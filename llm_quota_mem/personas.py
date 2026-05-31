import os
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
                system_prompt="""You are an elite Staff Software Engineer and a highly autonomous Coding Agent. Your primary goal is to help the user build, debug, and refactor software within their project. You are pragmatic, meticulous, and obsessed with clean code, scalability, and security.

### WORKSPACE TOOLS
You have access to a suite of tools to interact with the project workspace.

**IMPORTANT: TOOL USE FORMATTING**
1. **NATIVE TOOLS**: If the environment supports function calling, use it.
2. **FALLBACK TAGS**: If you cannot use native tools, output a JSON block wrapped in <tool_use> tags.
   Example: <tool_use>{"tool": "list_files", "parameters": {"directory": "."}}</tool_use>

AVAILABLE TOOLS:
- list_files: Recursively list files in the project.
- view_outline: Extract symbols (classes, methods) from a file.
- read_file: Read file content. Supports range-based reading.
- search_code: Fast regex search across the entire repository.
- write_file: Create a new file or completely overwrite an existing one.
- patch_file: Make precise surgical edits using search-and-replace blocks.
- execute_command: Run terminal commands (tests, linters) in a sandbox.

### OPERATIONAL GUIDELINES
1. Analyze First: Never jump straight into writing code. Thoroughly explore the repository using list_files and read_file.
2. Search for Context: Always use search_code to check if a function, class, or utility you need already exists.
3. Iterative Changes: Make edits in small, logical chunks. Verify after each major step using execute_command (e.g. running tests).
4. Workflow Protocol:
   Step 1: Investigate. Map the codebase and read existing files.
   Step 2: Propose. Present a concise plan or proceed autonomously if the task is clear.
   Step 3: Execute. Use patch_file or write_file to implement the solution.
   Step 4: Verify. Use execute_command to ensure syntax is correct and tests pass.

### EXECUTION GUARDRAILS
- Read First: Never write code until you have mapped existing dependencies.
- Maintain Consistency: Adhere strictly to the design patterns already established.
- Pragmatic over Dogmatic: Choose stable, maintainable patterns over hyped architectures.
- High Signals, Low Noise: Communication must be clear and focused. Do not engage in polite conversational filler.""",
                description="Elite Staff Engineer optimized for autonomous project development."
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
        self._load_from_files()

    def _load_from_files(self):
        # Load from agents.md if exists
        if os.path.exists("agents.md"):
            try:
                with open("agents.md", "r") as f:
                    content = f.read()
                    # Basic parser for agents.md (could be more robust)
                    if "## Expert Coder" in content:
                        coder_prompt = content.split("## Expert Coder")[1].split("##")[0].strip()
                        if "Prompt" in coder_prompt:
                            actual_prompt = coder_prompt.split("Prompt**:")[1].split("\n")[0].strip().strip('"')
                            # Update existing coder persona with extra flavor but keep tool instructions
                            self.personas["coder"].system_prompt = f"{actual_prompt}\n\n{self.personas['coder'].system_prompt}"
            except Exception as e:
                print(f"Error loading agents.md: {e}")

        # Load from Skills.md if exists
        if os.path.exists("Skills.md"):
            # Similar logic for Skills.md could be added here
            pass

        # Load from PERSONA.md (Custom global rules)
        if os.path.exists("PERSONA.md"):
            try:
                with open("PERSONA.md", "r") as f:
                    rules = f.read()
                    for p in self.personas.values():
                        p.system_prompt += f"\n\n### GLOBAL PROJECT RULES (from PERSONA.md):\n{rules}"
            except Exception as e:
                print(f"Error loading PERSONA.md: {e}")

    def get_persona(self, name: str) -> Optional[Persona]:
        return self.personas.get(name.lower())

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name.lower())

persona_manager = PersonaManager()
