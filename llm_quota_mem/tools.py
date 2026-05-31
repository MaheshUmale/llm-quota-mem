from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

def get_coder_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "Recursively list files in the project workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "The directory to list files from (relative to workspace root)."
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Maximum depth for recursive listing.",
                            "default": 3
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the content of a file from the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file."
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Line number to start reading from (1-indexed)."
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Line number to end reading at."
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create a new file or completely overwrite an existing one.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to create/overwrite."
                        },
                        "content": {
                            "type": "string",
                            "description": "The full content to write to the file."
                        }
                    },
                    "required": ["path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "patch_file",
                "description": "Apply precise surgical edits using search-and-replace blocks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to edit."
                        },
                        "search": {
                            "type": "string",
                            "description": "The exact block of code to search for."
                        },
                        "replace": {
                            "type": "string",
                            "description": "The block of code to replace it with."
                        }
                    },
                    "required": ["path", "search", "replace"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "Search for a pattern across the repository.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "The regex pattern to search for."
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "Glob pattern to limit search to certain files (e.g. *.py)."
                        }
                    },
                    "required": ["pattern"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Run a terminal command in the project sandbox.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute."
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "description": "Maximum execution time in seconds.",
                            "default": 30
                        }
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_outline",
                "description": "Extract symbols (classes, methods) from a source file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file."
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "grep_search",
                "description": "Fast text search using regex across the project (similar to grep).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "The regex pattern to search for."
                        },
                        "include": {
                            "type": "string",
                            "description": "Glob pattern for files to include."
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "default": False
                        }
                    },
                    "required": ["pattern"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_process_info",
                "description": "List running processes related to the project (checks if server/scripts are running).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "Optional string to filter process names."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_file_info",
                "description": "Get detailed file information like size, permissions, and last modified time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file."
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    ]
