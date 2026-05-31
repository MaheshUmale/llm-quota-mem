# System Architecture & Design Rules

## 1. Clean Architecture Principles
- **Separation of Concerns:** Keep core business logic independent of external frameworks, UI layers, or databases.
- **Unidirectional Data Flow:** Data must move via predictable paths. Avoid circular dependencies between modules.

## 2. Coding Patterns
- **Explicit over Implicit:** Write clear, descriptive variable and function names. Avoid magical properties or obscure language hacks.
- **Single Responsibility Principle (SRP):** Every module, class, or function must have one clear reason to change.
- **Error Handling:** Catch specific exceptions early. Always log the error details with relevant context before passing a safe message upstream.

## 3. Testing Requirements
- Write companion unit tests for all new logic.
- Ensure mock interfaces are utilized for heavy database operations or external API calls during testing.
