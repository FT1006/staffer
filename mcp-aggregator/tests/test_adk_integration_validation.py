"""
ADK Integration Validation Tests - Real Component Testing.

Tests actual ADK components and validation patterns as specified 
in the handover document requirements.
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, patch
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.factories import create_mock_adk_tool, create_test_server_config, create_mock_mcp_tool
from config import load_config, ServerConfig
from composer import GenericMCPServerComposer
from discovery import ToolDiscoveryEngine
from adk_to_genai import convert_adk_tool_to_genai


class TestRealADKToolDiscovery:
    """Test real ADK MCPToolset discovery behavior with proper mocking boundaries."""
    
    def test_discovery_engine_stats_interface(self):
        """Test that discovery engine provides stats interface."""
        discovery_engine = ToolDiscoveryEngine()
        
        # Test initial stats
        stats = discovery_engine.get_discovery_stats()
        assert isinstance(stats, dict)
        assert "total_conflicts" in stats
        assert "conflicts" in stats
        assert "cache_size" in stats
        assert "cached_servers" in stats
        
        # Initially should have no conflicts and empty cache
        assert stats["total_conflicts"] == 0
        assert stats["cache_size"] == 0


class TestDirectADKToolConversion:
    """Test direct ADK tool conversion methods."""
    
    def test_convert_adk_tool_to_genai_function(self):
        """Test direct convert_adk_tool_to_genai function."""
        adk_tool = create_mock_adk_tool("direct_test_tool", with_schema=True)
        
        genai_format = convert_adk_tool_to_genai(adk_tool)
        
        # Test that we get a FunctionDeclaration object
        assert hasattr(genai_format, 'name')
        assert genai_format.name == "direct_test_tool"
        assert hasattr(genai_format, 'description')
        assert genai_format.description == "Mock ADK tool: direct_test_tool"
        assert hasattr(genai_format, 'parameters')
        assert hasattr(genai_format.parameters, 'type')
    
    def test_convert_adk_tools_to_genai_method(self):
        """Test _convert_adk_tools_to_genai method directly."""
        composer = GenericMCPServerComposer({})
        
        # Use factory pattern for consistent test data
        adk_tools = [
            create_mock_adk_tool("excel_read", with_schema=True),
            create_mock_mcp_tool("mcp_tool")  # Changed to use create_mock_mcp_tool
        ]
        
        # Test the actual conversion method
        genai_tools = composer._convert_adk_tools_to_genai(adk_tools)
        
        assert len(genai_tools) == 2
        
        # Verify both schema and schema-less tools are handled
        tool_names = [tool.name for tool in genai_tools]
        assert "excel_read" in tool_names
        assert "mcp_tool" in tool_names
    
    def test_hybrid_tool_conversion_paths(self):
        """Test both FunctionTool and MCPTool conversion paths."""
        composer = GenericMCPServerComposer({})
        
        # Mix of ADK tools (with schema) and MCP tools (without schema)
        mixed_tools = [
            create_mock_adk_tool("function_tool", with_schema=True),
            create_mock_mcp_tool("mcp_tool_no_schema")
        ]
        
        genai_tools = composer._convert_adk_tools_to_genai(mixed_tools)
        
        assert len(genai_tools) == 2
        
        # Check that both conversion paths work
        for tool in genai_tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            # Parameters should exist (either from schema or flexible declaration)
            assert hasattr(tool, 'parameters')
    
    def test_flexible_declaration_for_schema_less_tools(self):
        """Test _create_flexible_declaration for schema-less tools."""
        composer = GenericMCPServerComposer({})
        
        # Create schema-less tool
        mcp_tool = create_mock_mcp_tool("flexible_tool")
        
        # Test flexible declaration creation
        flexible_decl = composer._create_flexible_declaration(mcp_tool)
        
        assert flexible_decl.name == "flexible_tool"
        assert hasattr(flexible_decl, 'description')
        assert hasattr(flexible_decl, 'parameters')
        # Should have flexible input parameter
        assert hasattr(flexible_decl.parameters, 'properties')


class TestConfigurationServerExtraction:
    """Test configuration and server extraction methods."""
    
    def test_extract_server_configs_method(self):
        """Test _extract_server_configs method directly."""
        test_config = {
            "source_servers": [
                {
                    "name": "test_server1",
                    "enabled": True,
                    "priority": 1,
                    "command": "python",
                    "args": ["-m", "server1"],
                    "cwd_env": "PWD"
                },
                {
                    "name": "test_server2", 
                    "enabled": False,
                    "priority": 2,
                    "command": "python",
                    "args": ["-m", "server2"],
                    "cwd_env": "PWD"
                }
            ]
        }
        
        composer = GenericMCPServerComposer(test_config)
        
        # Test server config extraction
        server_configs = composer._extract_server_configs()
        
        assert len(server_configs) == 2
        # _extract_server_configs returns dicts, not ServerConfig objects
        assert all(isinstance(config, dict) for config in server_configs)
        
        # Check enabled/disabled filtering
        enabled_configs = [c for c in server_configs if c.get("enabled", True)]
        disabled_configs = [c for c in server_configs if not c.get("enabled", True)]
        
        assert len(enabled_configs) == 1
        assert len(disabled_configs) == 1
        assert enabled_configs[0]["name"] == "test_server1"
        assert disabled_configs[0]["name"] == "test_server2"
    
    def test_server_config_environment_resolution(self):
        """Test that ServerConfig resolves environment variables correctly."""
        server_config = create_test_server_config()
        
        # Test without environment variable - PWD should be None by default  
        with patch('os.getenv', return_value=None):
            assert server_config.cwd is None
            assert not server_config.is_available
        
        # Test with environment variable
        with patch('os.getenv', return_value="/test/env/path"):
            assert server_config.cwd == "/test/env/path"
            assert server_config.is_available


class TestRealConfigurationIntegration:
    """Test integration with real configuration files."""
    
    def test_real_test_config_loading(self):
        """Test loading real test_config.yaml file."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        config = load_config(str(config_path))
        
        # Verify real config structure
        assert config.domain == "test_staffer_tools"
        assert len(config.source_servers) == 3
        
        # Check specific servers from test config
        server_names = [s.name for s in config.source_servers]
        assert "mock_excel" in server_names
        assert "mock_analytics" in server_names
        assert "disabled_server" in server_names
        
        # Verify enabled/disabled states
        enabled_servers = [s for s in config.source_servers if s.enabled]
        disabled_servers = [s for s in config.source_servers if not s.enabled]
        
        assert len(enabled_servers) == 2
        assert len(disabled_servers) == 1
        assert disabled_servers[0].name == "disabled_server"
    
    def test_config_to_composer_integration(self):
        """Test real config → composer integration."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        config = load_config(str(config_path))
        
        # Convert AggregatorConfig to dict for composer
        config_dict = {
            "domain": config.domain,
            "source_servers": [
                {
                    "name": server.name,
                    "command": server.command,
                    "args": server.args,
                    "cwd_env": server.cwd_env,
                    "enabled": server.enabled,
                    "priority": server.priority,
                    "tool_filter": server.tool_filter
                }
                for server in config.source_servers
            ],
            "tool_selection": config.tool_selection
        }
        
        composer = GenericMCPServerComposer(config_dict)
        
        # Test that composer extracts configs correctly
        server_configs = composer._extract_server_configs()
        
        assert len(server_configs) == 3
        enabled_configs = [c for c in server_configs if c.get('enabled', True)]
        assert len(enabled_configs) == 2


class TestEndToEndADKValidation:
    """End-to-end ADK validation testing."""
    
    @pytest.mark.asyncio
    async def test_complete_adk_pipeline_validation(self):
        """Test complete pipeline: Config → Discovery → Conversion → GenAI format."""
        # Create simplified config with enabled servers
        config_dict = {
            "domain": "test_domain",
            "source_servers": [
                {
                    "name": "test_server",
                    "command": "python",
                    "args": ["-m", "test"],
                    "cwd_env": "PWD",
                    "enabled": True,
                    "priority": 1,
                    "tool_filter": ["excel_read_sheet", "load_dataset"]
                }
            ],
            "tool_selection": {"strategy": "curated"}
        }
        
        composer = GenericMCPServerComposer(config_dict)
        
        # Mock the discovery engine to return ADK tools directly
        mock_adk_tools = [
            create_mock_adk_tool("excel_read_sheet", with_schema=True),
            create_mock_mcp_tool("load_dataset")  # Schema-less MCP tool
        ]
        
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.return_value = mock_adk_tools
            
            with patch('os.getenv', return_value="/test/path"):
                # Test complete pipeline 
                genai_tools = await composer.get_all_tools()
                
                # Validate ADK conversion worked
                assert len(genai_tools) == 2
                
                # Check both conversion paths (ADK with schema, MCP without schema)
                tool_names = [tool.name for tool in genai_tools]
                assert "excel_read_sheet" in tool_names
                assert "load_dataset" in tool_names
                
                # Validate GenAI format structure
                for tool in genai_tools:
                    assert hasattr(tool, 'name')
                    assert hasattr(tool, 'description')
                    assert hasattr(tool, 'parameters')
    
    @pytest.mark.asyncio  
    async def test_adk_hybrid_tool_support_validation(self):
        """Test ADR-004: Hybrid tool support (FunctionTools + MCPTools)."""
        composer = GenericMCPServerComposer({})
        
        # Create hybrid tool set using factories
        hybrid_tools = [
            create_mock_adk_tool("function_tool_with_schema", with_schema=True),
            create_mock_adk_tool("function_tool_no_schema", with_schema=False),
            create_mock_mcp_tool("pure_mcp_tool")
        ]
        
        # Test hybrid conversion
        genai_tools = composer._convert_adk_tools_to_genai(hybrid_tools)
        
        assert len(genai_tools) == 3
        
        # All should convert to GenAI format regardless of schema presence
        tool_names = []
        for tool in genai_tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'parameters')
            tool_names.append(tool.name)
        
        # Verify all tools were converted
        assert "function_tool_with_schema" in tool_names
        assert "function_tool_no_schema" in tool_names
        assert "pure_mcp_tool" in tool_names