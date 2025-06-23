#!/usr/bin/env python3
"""Simple MCP echo server for testing basic communication."""
import sys
import json


def main():
    """Echo server that reflects back messages in MCP JSON-RPC format."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line.strip())
            
            # Basic JSON-RPC echo response
            if request.get("method") == "echo":
                response = {
                    "jsonrpc": "2.0",
                    "result": request.get("params", {}).get("message", ""),
                    "id": request.get("id")
                }
            else:
                # Return error for unknown methods
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
            # Return parse error
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