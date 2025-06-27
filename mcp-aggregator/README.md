# MCP Aggregator

A standalone service for aggregating and exposing tools from multiple MCP (Model Context Protocol) servers through a unified interface.

## Overview

The MCP Aggregator provides a clean separation between Staffer (the AI coding assistant) and external tool providers. It aggregates tools from multiple MCP servers, handles schema conversion, and provides graceful fallback when servers are unavailable.

### Key Features

- **Environment-driven configuration** - Deploy across dev/staging/production without code changes
- **Concurrent processing** - 3x faster tool discovery via parallel server processing  
- **ADK translation** - Automatic conversion of ADK tools to GenAI format
- **Conflict resolution** - Priority-based handling when multiple servers provide the same tool
- **Graceful degradation** - Continue operating when individual servers fail
- **Zero hardcoding** - All paths and settings configurable via environment variables

## Architecture

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Excel MCP       │  │ Analytics MCP   │  │ Future MCP...   │
│ Server          │  │ Server          │  │ Servers         │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                     │
         └────────────────────┴─────────────────────┘
                              │
               ┌──────────────▼──────────────┐
               │   MCP Aggregator Service    │
               │   • Tool Discovery          │
               │   • Schema Conversion       │
               │   • Priority Resolution     │
               │   • Concurrent Processing   │
               └──────────────┬──────────────┘
                              │ Clean MCP Protocol
               ┌──────────────▼──────────────┐
               │         Staffer CLI         │
               │    (or other MCP clients)   │
               └─────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.10+
- Go 1.21+ (for Excel MCP server)
- Access to MCP servers (Excel, Analytics, etc.)

### Setup

1. **Clone and navigate to the aggregator:**
   ```bash
   cd staffer/mcp-aggregator
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual paths
   ```

## Configuration

The aggregator uses YAML configuration files with environment variable substitution.

### Configuration Files

- **`aggregation.yaml`** - Default development configuration
- **`production.yaml`** - Production-ready configuration with environment variables
- **`test_config.yaml`** - Test configuration for integration testing

### Environment Variable Substitution

Configuration supports `${VAR:-default}` syntax:

```yaml
server:
  host: "${MCP_AGGREGATOR_HOST:-localhost}"
  port: ${MCP_AGGREGATOR_PORT:-8080}

source_servers:
  - name: "excel"
    cwd_env: "EXCEL_MCP_PATH"
    enabled: ${EXCEL_ENABLED:-true}
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `EXCEL_MCP_PATH` | Path to Excel MCP server | `/opt/excel-mcp-server` |
| `ANALYTICS_MCP_PATH` | Path to Analytics MCP server | `/opt/analytics-mcp-server` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_AGGREGATOR_HOST` | `localhost` | Server bind address |
| `MCP_AGGREGATOR_PORT` | `8080` | Server port |
| `EXCEL_ENABLED` | `true` | Enable/disable Excel server |
| `ANALYTICS_ENABLED` | `true` | Enable/disable Analytics server |
| `MAX_TOOLS_PER_SERVER` | `25` | Maximum tools per server |

## Deployment

### Development

```bash
# Set environment variables
export EXCEL_MCP_PATH="/Users/username/project/staffer/excel-mcp-server"
export ANALYTICS_MCP_PATH="/Users/username/project/staffer/quick-data-mcp-main/quick-data-mcp"

# Run with development config
python3 server.py --config aggregation.yaml
```

### Production

```bash
# Set production environment variables
export MCP_AGGREGATOR_HOST="prod.company.com"
export MCP_AGGREGATOR_PORT="9000"
export EXCEL_MCP_PATH="/opt/mcp-servers/excel-mcp-server"
export ANALYTICS_MCP_PATH="/opt/mcp-servers/analytics-mcp-server"

# Run with production config
python3 server.py --config production.yaml
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Environment variables set at runtime
CMD ["python3", "server.py", "--config", "production.yaml"]
```

```bash
# Build and run
docker build -t mcp-aggregator .
docker run -e EXCEL_MCP_PATH="/opt/excel" \
           -e ANALYTICS_MCP_PATH="/opt/analytics" \
           -p 8080:8080 \
           mcp-aggregator
```

### Feature Toggles

Enable/disable individual servers without redeployment:

```bash
# Disable Excel, keep Analytics
export EXCEL_ENABLED=false
export ANALYTICS_ENABLED=true
python3 server.py --config production.yaml
```

## API Reference

### Server Endpoints

The aggregator exposes MCP protocol endpoints:

- **Tool Discovery** - List available tools from all servers
- **Tool Execution** - Execute tools with parameter validation
- **Health Check** - Server status and available servers

### Configuration API

```python
from config import load_config

# Load with environment substitution
config = load_config("production.yaml")

# Check available servers
available = config.available_servers
print(f"Available: {[s.name for s in available]}")
```

### Server Management

```python
from server import MCPAggregatorServer

# Create server instance
server = MCPAggregatorServer(config_path="production.yaml")

# Get aggregated tools
tools = await server.get_tools()
print(f"Aggregated {len(tools)} tools")

# Start server
server.start()
```

## Troubleshooting

### Common Issues

#### "Configuration validation failed: No MCP servers are available"

**Cause:** Required environment variables not set.

**Solution:**
```bash
# Check environment variables are set
echo $EXCEL_MCP_PATH
echo $ANALYTICS_MCP_PATH

# Set missing variables
export EXCEL_MCP_PATH="/path/to/excel-mcp-server"
export ANALYTICS_MCP_PATH="/path/to/analytics-mcp-server"
```

#### "Failed to discover tools from server: Connection refused"

**Cause:** MCP server not running or incorrect path.

**Solution:**
```bash
# Check server path exists
ls -la $EXCEL_MCP_PATH

# Test server manually
cd $EXCEL_MCP_PATH
go run cmd/excel-mcp-server/main.go
```

#### "FileNotFoundError: Configuration file not found"

**Cause:** Config file not found in expected location.

**Solution:**
```bash
# Use absolute path
python3 server.py --config /full/path/to/production.yaml

# Or run from correct directory
cd mcp-aggregator
python3 server.py --config production.yaml
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
python3 server.py --config production.yaml
```

### Health Checks

Verify server is working:

```bash
# Check server starts successfully
python3 server.py --config production.yaml

# Expected output:
# INFO:__main__:MCP Aggregator Server starting on localhost:8080
# INFO:__main__:Available servers: 2
# INFO:__main__:  - excel: enabled (available)
# INFO:__main__:  - analytics: enabled (available)
```

### Testing Configuration

Validate configuration without starting server:

```bash
python3 -c "
from config import load_config, validate_config
config = load_config('production.yaml')
issues = validate_config(config)
print('Issues:', issues if issues else 'None')
print('Available servers:', len(config.available_servers))
"
```

## Development

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test categories
python3 -m pytest tests/test_adk_integration_validation.py -v  # ADK integration
python3 -m pytest tests/test_production_configs.py -v         # Production config
python3 -m pytest tests/test_server.py -v                     # Server functionality
```

### Adding New MCP Servers

1. **Update configuration:**
   ```yaml
   source_servers:
     - name: "new_server"
       command: "python"
       args: ["-m", "new_server.main"]
       cwd_env: "NEW_SERVER_PATH"
       tool_filter: ["tool1", "tool2"]
       priority: 3
       enabled: ${NEW_SERVER_ENABLED:-true}
   ```

2. **Set environment variable:**
   ```bash
   export NEW_SERVER_PATH="/path/to/new-server"
   export NEW_SERVER_ENABLED=true
   ```

3. **Test integration:**
   ```bash
   python3 server.py --config production.yaml
   ```

### Architecture Decisions

- **ADR-001**: MCP Aggregator Pattern - Separation of concerns
- **ADR-002**: ADK Translation Layer - Schema conversion in aggregator  
- **ADR-003**: YAML Configuration - Environment-driven deployment
- **ADR-004**: Hybrid Tool Support - Both schema and schema-less tools
- **ADR-005**: Concurrent Processing - Performance optimization

## License

See main Staffer project license.