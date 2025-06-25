# MCP Aggregator Test Organization

This directory organizes tests by protocol compliance to facilitate the transition from HTTP to STDIO protocol.

## Subfolders

### `http_free/` ✅
**Safe to run and maintain**

Tests in this folder are protocol-agnostic or already use correct patterns:
- `test_adk_translator.py` - Pure schema translation logic
- `test_composer.py` - Tool aggregation logic (protocol-agnostic)
- `test_graceful_fallback.py` - Error handling patterns
- `test_server.py` - Server interface tests
- `test_composer_pipeline_validation.py` - Pipeline validation
- `test_composer_translator_integration.py` - Integration tests
- `test_adk_integration_validation.py` - ADK integration validation
- `test_server_config_path.py` - File path configuration
- `test_yaml_config.py` - ✅ **FIXED** - YAML config without server section

### `http_polluted/` ⚠️  
**Require rewriting for STDIO protocol**

Tests in this folder contain HTTP protocol violations and must be updated:
- `test_mcp_client.py` - Uses host/port configuration (should use MCPToolset)
- `test_config_env_substitution.py` - Tests HTTP config environment substitution
- `test_production_configs.py` - Production configs with HTTP settings
- `test_adk_schema_validation.py` - May contain HTTP config validation

## Protocol Fix Priority

1. **Keep http_free/ tests running** - These validate the 90% of code that's correct
2. **Rewrite http_polluted/ tests** - Convert to test STDIO protocol instead of HTTP
3. **Focus on real MCP patterns** - Use MCPToolset with StdioConnectionParams

## Expected Changes

After protocol fix:
- All `host`/`port` references should be removed
- Tests should use `MCPToolset(StdioConnectionParams(...))`
- Server tests should validate FastMCP or mcp.Server usage
- Configuration tests should validate STDIO server parameters only

## Running Tests

```bash
# Run only clean tests during development
pytest http_free/

# Run all tests after protocol fix
pytest http_free/ http_polluted/
```