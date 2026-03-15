import pytest
from unittest.mock import MagicMock, patch
from core.agents.autonomous_agent import AutonomousAgent
from core.tools.system_integrator import ToolFactory

@pytest.fixture
def mock_agent():
    """Fixture for an agent with mocked LLM and tools."""
    with patch("core.agents.autonomous_agent.ChatOpenAI") as mock_llm:
        agent = AutonomousAgent(model_name="mock-model")
        return agent

def test_agent_initialization(mock_agent):
    """Verifies the agent initializes correctly."""
    assert mock_agent.llm is not None
    assert len(mock_agent.tools) > 0
    assert mock_agent.agent_executor is not None

@patch("core.agents.autonomous_agent.AgentExecutor.invoke")
def test_agent_run_success(mock_invoke, mock_agent):
    """Verifies the agent run method returns output correctly."""
    mock_invoke.return_value = {"output": "Task completed successfully."}
    result = mock_agent.run("Perform a simple task")
    assert result == "Task completed successfully."
    mock_invoke.assert_called_once()

@patch("core.agents.autonomous_agent.AgentExecutor.invoke")
def test_agent_run_error_handling(mock_invoke, mock_agent):
    """Verifies the agent handles executor exceptions gracefully."""
    mock_invoke.side_effect = Exception("LLM connection failed")
    result = mock_agent.run("Perform a task")
    assert "Error executing task" in result
    assert "LLM connection failed" in result

def test_tool_factory_sql():
    """Verifies the tool factory creates SQL tools correctly."""
    sql_tool = ToolFactory.get_tool("sql", connection_string="sqlite:///:memory:")
    assert sql_tool.__class__.__name__ == "SQLDatabaseTool"

def test_tool_factory_fs():
    """Verifies the tool factory creates FileSystem tools correctly."""
    fs_tool = ToolFactory.get_tool("fs", base_path="/tmp")
    assert fs_tool.__class__.__name__ == "FileSystemTool"
    assert fs_tool.base_path == "/tmp"

@patch("core.tools.system_integrator.create_engine")
def test_sql_tool_execution(mock_create_engine):
    """Verifies the SQL tool executes queries correctly (mocked)."""
    mock_conn = MagicMock()
    mock_create_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
    
    mock_result = MagicMock()
    mock_result.returns_rows = True
    mock_result._mapping = {"id": 1, "name": "test"}
    mock_conn.execute.return_value = [mock_result]
    
    from core.tools.system_integrator import SQLDatabaseTool
    tool = SQLDatabaseTool("sqlite:///:memory:")
    results = tool.execute("SELECT * FROM users")
    
    assert len(results) == 1
    assert results[0]["id"] == 1
    mock_conn.execute.assert_called_once()

# Integration style test (skipping actual LLM calls)
def test_agent_tool_mapping(mock_agent):
    """Verifies all required tools are mapped correctly."""
    tool_names = [t.name for t in mock_agent.tools]
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "query_database" in tool_names
    assert "fetch_api" in tool_names
