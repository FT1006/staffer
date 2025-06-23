#!/usr/bin/env python3
"""Test MCP server that supports initialization and tools/list."""
import sys
import json


def main():
    """MCP server that supports basic protocol including tools/list."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line.strip())
            
            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        }
                    },
                    "id": request.get("id")
                }
            elif request.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": [
                            {
                                "name": "test_tool",
                                "description": "A test tool",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "param": {"type": "string"}
                                    }
                                }
                            },
                            {
                                "name": "another_tool", 
                                "description": "Another test tool",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "number"}
                                    }
                                }
                            }
                        ]
                    },
                    "id": request.get("id")
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {request.get('method')}"
                    },
                    "id": request.get("id")
                }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                },
                "id": None
            }
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception:
            break


if __name__ == "__main__":
    main()