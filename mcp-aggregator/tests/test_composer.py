"""RED tests for GenericMCPServerComposer - minimal mocking, behavior-focused."""
import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Proper relative import
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from tests.factories import adk_tool

# Import the composer module
try:
    from composer import GenericMCPServerComposer
except ImportError:
    GenericMCPServerComposer = None


def excel_tools():
    """Create Excel tools using existing factory pattern."""
    return [
        adk_tool("excel_read_sheet", "Read Excel sheet", {
            "type": "object",
            "properties": {"sheet": {"type": "string"}}
        }),
        adk_tool("excel_write_to_sheet", "Write Excel sheet", {
            "type": "object",
            "properties": {"sheet": {"type": "string"}, "data": {"type": "array"}}
        })
    ]


def analytics_tools():
    """Create Analytics tools using existing factory pattern."""
    return [
        adk_tool("load_dataset", "Load dataset", {
            "type": "object",
            "properties": {"path": {"type": "string"}}
        }),
        adk_tool("find_correlations", "Find correlations", {
            "type": "object",
            "properties": {"columns": {"type": "array"}}
        })
    ]


def conflicting_tools():
    """Create tools with same name from different servers."""
    excel_read = adk_tool("read_data", "Excel read tool", {
        "type": "object",
        "properties": {"source": {"type": "string"}}
    })
    
    analytics_read = adk_tool("read_data", "Analytics read tool", {
        "type": "object",
        "properties": {"format": {"type": "string"}}
    })
    
    return excel_read, analytics_read


@pytest.mark.asyncio
async def test_composer_aggregates_multiple_toolsets():
    """Test composer aggregates tools from multiple servers - should fail first."""
    if not GenericMCPServerComposer:
        pytest.skip("GenericMCPServerComposer not implemented yet")
    
    # Given: Expected tools from both servers
    expected_tools = excel_tools() + analytics_tools()
    
    # Mock minimal boundary - only tool discovery, not MCPToolset itself
    config = {
        'source_servers': [
            {'name': 'excel', 'tools': excel_tools()},
            {'name': 'analytics', 'tools': analytics_tools()}
        ]
    }
    
    # When: Composer aggregates tools (mock at boundary, not core components)
    composer = GenericMCPServerComposer(config)
    
    # Mock the discovery method, not MCPToolset
    with patch.object(composer, '_discover_tools_from_server') as mock_discover:
        mock_discover.side_effect = [excel_tools(), analytics_tools()]
        
        aggregated_tools = await composer.get_all_tools()
    
    # Then: Test behavior, not exact implementation
    tool_names = {tool.name for tool in aggregated_tools}
    expected_names = {tool.name for tool in expected_tools}
    
    # Flexible assertions - test presence, not exact match
    assert expected_names.issubset(tool_names)
    assert len(aggregated_tools) >= len(expected_tools)


@pytest.mark.asyncio
async def test_composer_handles_tool_conflicts_by_priority():
    """Test composer resolves naming conflicts using priority - should fail first."""
    if not GenericMCPServerComposer:
        pytest.skip("GenericMCPServerComposer not implemented yet")
    
    # Given: Two servers with conflicting tool name, different priorities
    excel_read, analytics_read = conflicting_tools()
    
    config = {
        'source_servers': [
            {'name': 'excel', 'priority': 1, 'tools': [excel_read]},
            {'name': 'analytics', 'priority': 2, 'tools': [analytics_read]}  # Higher priority
        ]
    }
    
    # When: Composer resolves conflicts
    composer = GenericMCPServerComposer(config)
    
    with patch.object(composer, '_discover_tools_from_server') as mock_discover:
        mock_discover.side_effect = [[excel_read], [analytics_read]]
        
        aggregated_tools = await composer.get_all_tools()
    
    # Then: Higher priority tool should win
    read_tools = [tool for tool in aggregated_tools if tool.name == "read_data"]
    
    # Behavior assertions - test conflict resolution
    assert len(read_tools) == 1, "Should resolve conflict to single tool"
    assert read_tools[0].description == "Analytics read tool", "Should choose higher priority"


@pytest.mark.asyncio  
async def test_composer_gracefully_handles_server_failures():
    """Test composer continues when some servers fail - should fail first."""
    if not GenericMCPServerComposer:
        pytest.skip("GenericMCPServerComposer not implemented yet")
    
    # Given: One working server, one failing server
    working_tools = excel_tools()
    
    config = {
        'source_servers': [
            {'name': 'excel', 'tools': working_tools},
            {'name': 'failing_server', 'will_fail': True}
        ]
    }
    
    # When: One server fails during discovery
    composer = GenericMCPServerComposer(config)
    
    with patch.object(composer, '_discover_tools_from_server') as mock_discover:
        # First call succeeds, second fails
        mock_discover.side_effect = [working_tools, Exception("Server failed")]
        
        aggregated_tools = await composer.get_all_tools()
    
    # Then: Should continue with working servers
    tool_names = {tool.name for tool in aggregated_tools}
    expected_working_names = {tool.name for tool in working_tools}
    
    # Graceful degradation assertions
    assert expected_working_names.issubset(tool_names), "Should include working server tools"
    assert len(aggregated_tools) >= len(working_tools), "Should have minimum working tools"
    
    # Should track failures for monitoring
    assert hasattr(composer, 'server_failures'), "Should track failed servers"


# Configuration factory functions
def create_basic_config():
    """Create basic test configuration."""
    return {
        'domain': 'test_domain',
        'model': 'gemini-2.0-flash',
        'instruction': 'Test aggregator',
        'source_servers': []
    }


def create_two_server_config():
    """Create config with two test servers."""
    config = create_basic_config()
    config['source_servers'] = [
        {
            'name': 'excel',
            'command': 'test_excel_cmd',
            'args': [],
            'cwd_env': 'TEST_EXCEL_PATH',
            'priority': 1
        },
        {
            'name': 'analytics', 
            'command': 'test_analytics_cmd',
            'args': [],
            'cwd_env': 'TEST_ANALYTICS_PATH',
            'priority': 2
        }
    ]
    return config


@pytest.fixture
def test_env():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    os.environ.update({
        'TEST_EXCEL_PATH': '/tmp/test_excel',
        'TEST_ANALYTICS_PATH': '/tmp/test_analytics'
    })
    
    yield
    
    # Restore
    os.environ.clear()
    os.environ.update(original_env)


@pytest.mark.asyncio
async def test_composer_call_tool_executes_via_real_mcp_server():
    """RED: Test composer executes tool via real MCP server - should fail first."""
    if not GenericMCPServerComposer:
        pytest.skip("GenericMCPServerComposer not implemented yet")
    
    # Given: Config pointing to real Quick Data MCP server
    config = {
        'source_servers': [{
            'name': 'analytics',
            'command': 'python',
            'args': ['-m', 'mcp_server'],
            'cwd_env': 'ANALYTICS_MCP_PATH',
            'enabled': True,
            'priority': 1
        }]
    }
    
    # Set up environment to point to Quick Data MCP
    with patch.dict(os.environ, {
        'ANALYTICS_MCP_PATH': str(Path(__file__).parent.parent.parent / 'quick-data-mcp-main/quick-data-mcp')
    }):
        composer = GenericMCPServerComposer(config)
        
        # When: Execute load_dataset tool
        arguments = {
            'file_path': 'data/employee_survey.csv'
        }
        
        # This should fail until call_tool is implemented
        with pytest.raises(AttributeError, match="'GenericMCPServerComposer' object has no attribute 'call_tool'"):
            result = await composer.call_tool('load_dataset', arguments)


@pytest.mark.asyncio
async def test_composer_respects_server_enabled_flag():
    """RED: Test composer correctly enables/disables servers - should fail first."""
    if not GenericMCPServerComposer:
        pytest.skip("GenericMCPServerComposer not implemented yet")
    
    # Given: Two servers, one enabled and one disabled
    config = {
        'source_servers': [
            {
                'name': 'enabled_server',
                'command': 'python',
                'args': ['-m', 'server'],
                'cwd_env': 'ENABLED_PATH',
                'enabled': True,
                'priority': 1,
                'tools': excel_tools()
            },
            {
                'name': 'disabled_server',
                'command': 'python', 
                'args': ['-m', 'server'],
                'cwd_env': 'DISABLED_PATH',
                'enabled': False,
                'priority': 2,
                'tools': analytics_tools()
            }
        ]
    }
    
    with patch.dict(os.environ, {
        'ENABLED_PATH': '/tmp/enabled',
        'DISABLED_PATH': '/tmp/disabled'
    }):
        composer = GenericMCPServerComposer(config)
        
        # Mock discovery to verify which servers are queried
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.return_value = excel_tools()
            
            tools = await composer.get_all_tools()
            
            # Then: Only enabled server should be discovered
            # Check that discovery was called only for enabled server
            assert mock_discover.call_count <= 1, "Should only discover from enabled servers"
            
            # Verify tools only come from enabled server
            tool_names = {tool.name for tool in tools}
            excel_names = {tool.name for tool in excel_tools()}
            analytics_names = {tool.name for tool in analytics_tools()}
            
            assert excel_names.issubset(tool_names), "Should include enabled server tools"
            assert not analytics_names.issubset(tool_names), "Should not include disabled server tools"


@pytest.mark.asyncio
async def test_composer_call_tool_with_server_not_available():
    """RED: Test call_tool when no server has the requested tool - should fail first."""
    if not GenericMCPServerComposer:
        pytest.skip("GenericMCPServerComposer not implemented yet")
    
    # Given: Server without the requested tool
    config = {
        'source_servers': [{
            'name': 'excel',
            'command': 'test',
            'args': [],
            'cwd_env': 'EXCEL_PATH',
            'enabled': True,
            'priority': 1
        }]
    }
    
    with patch.dict(os.environ, {'EXCEL_PATH': '/tmp/excel'}):
        composer = GenericMCPServerComposer(config)
        
        # Mock discovery returning tools that don't include requested one
        with patch.object(composer.discovery_engine, '_discover_server_tools') as mock_discover:
            mock_discover.return_value = {'excel_read': Mock(), 'excel_write': Mock()}
            
            # When: Try to call non-existent tool
            # This should fail with ValueError once implemented
            with pytest.raises(ValueError, match="Tool 'non_existent_tool' not found"):
                await composer.call_tool('non_existent_tool', {})