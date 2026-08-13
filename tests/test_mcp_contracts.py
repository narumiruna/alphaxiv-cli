import pytest
from pydantic import ValidationError

from alphaxiv.clients.mcp import McpClient
from alphaxiv.contracts.mcp import MCP_TOOLS
from alphaxiv.contracts.mcp import McpAccess
from alphaxiv.contracts.mcp import McpQuota
from alphaxiv.contracts.mcp import McpToolName
from alphaxiv.models.mcp import DiscoverPapersArguments


def test_static_mcp_contracts_cover_exact_official_tool_surface() -> None:
    assert set(MCP_TOOLS) == set(McpToolName)
    assert len(MCP_TOOLS) == 11
    assert sum(contract.access is McpAccess.WRITE for contract in MCP_TOOLS.values()) == 6
    assert sum(contract.quota is McpQuota.ASSISTANT for contract in MCP_TOOLS.values()) == 4
    assert all(contract.model_config.get("frozen") for contract in MCP_TOOLS.values())


def test_contracts_bind_fixed_argument_models_and_required_fields() -> None:
    discover = MCP_TOOLS[McpToolName.DISCOVER_PAPERS]

    assert discover.arguments_model is DiscoverPapersArguments
    assert discover.required_arguments == ("keywords", "question", "difficulty")
    with pytest.raises(ValidationError):
        discover.arguments_model.model_validate({"question": "missing required fields"})


def test_public_client_has_no_arbitrary_tool_or_endpoint_entrypoint() -> None:
    assert not hasattr(McpClient, "call_tool")
    assert not hasattr(McpClient, "request")
    assert not hasattr(McpClient, "base_url")
