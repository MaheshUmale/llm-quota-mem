# llm-quota-mem Skills

Skills are specialized instruction sets that can be injected into any LLM request to improve performance or reduce token usage.

## 🐍 Python Mastery
- **Effect**: Injects instructions to use modern Python idioms (Type hinting, Pydantic, Asyncio).
- **Benefit**: Ensures high-quality, maintainable code output.

## 🛡️ Security First
- **Effect**: Injects instructions to consider security implications and OWASP best practices.
- **Benefit**: Automates security review during code generation.

## ⚡ Concise Output
- **Effect**: Injects instructions to keep responses brief and avoid conversational filler.
- **Benefit**: **Saves tokens** and reduces latency by minimizing verbosity.

## Usage
Skills can be requested via the API by adding them to the `skills` list in your request:
```json
{
  "model": "gpt-4o",
  "messages": [...],
  "skills": ["python", "concise"]
}
```
