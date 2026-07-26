"""Tests for LatexEditorTool."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from nanobot.agent.tools.latex_editor import LatexEditorTool


async def test_tool_basics():
    """Test basic tool properties."""
    tool = LatexEditorTool()

    print("=== Test 1: Tool Properties ===")
    print(f"Name: {tool.name}")
    print(f"Description: {tool.description[:50]}...")
    print(f"Parameters: {json.dumps(tool.parameters, indent=2)[:200]}...")
    print("[OK] Properties OK\n")


async def test_no_connection():
    """Test tool behavior without WebSocket connection."""
    tool = LatexEditorTool()

    print("=== Test 2: No Connection ===")
    result = await tool.execute(action="get")
    result_data = json.loads(result)
    print(f"Result: {result_data}")
    assert result_data["status"] == "error"
    assert "No WebSocket connection" in result_data["message"]
    print("[OK] No connection error OK\n")


async def test_with_mock_connection():
    """Test tool with mocked WebSocket connection."""
    tool = LatexEditorTool()

    # Mock WebSocket channel and connection
    mock_channel = MagicMock()
    mock_channel._send_event = AsyncMock()
    mock_connection = MagicMock()

    # Set context
    tool.set_context(mock_channel, mock_connection)

    print("=== Test 3: Set Action ===")
    result = await tool.execute(action="set", content="\\documentclass{article}")
    result_data = json.loads(result)
    print(f"Result: {result_data}")
    assert result_data["status"] == "sent"
    assert result_data["action"] == "set"
    # Verify _send_event was called
    mock_channel._send_event.assert_called_once()
    call_args = mock_channel._send_event.call_args
    print(f"Sent event: {call_args}")
    print("[OK] Set action OK\n")

    # Reset mock
    mock_channel._send_event.reset_mock()

    print("=== Test 4: Replace Action ===")
    result = await tool.execute(action="replace", search="old", replace="new")
    result_data = json.loads(result)
    print(f"Result: {result_data}")
    assert result_data["status"] == "sent"
    assert result_data["action"] == "replace"
    print("[OK] Replace action OK\n")

    # Reset mock
    mock_channel._send_event.reset_mock()

    print("=== Test 5: Append Action ===")
    result = await tool.execute(action="append", content="\\section{New}")
    result_data = json.loads(result)
    print(f"Result: {result_data}")
    assert result_data["status"] == "sent"
    assert result_data["action"] == "append"
    print("[OK] Append action OK\n")

    # Reset mock
    mock_channel._send_event.reset_mock()

    print("=== Test 6: Insert Line Action ===")
    result = await tool.execute(action="insert_line", line=5, content="\\subsection{Test}")
    result_data = json.loads(result)
    print(f"Result: {result_data}")
    assert result_data["status"] == "sent"
    assert result_data["action"] == "insert_line"
    print("[OK] Insert line action OK\n")

    # Reset mock
    mock_channel._send_event.reset_mock()

    print("=== Test 7: Delete Line Action ===")
    result = await tool.execute(action="delete_line", line=3)
    result_data = json.loads(result)
    print(f"Result: {result_data}")
    assert result_data["status"] == "sent"
    assert result_data["action"] == "delete_line"
    print("[OK] Delete line action OK\n")

    # Reset mock
    mock_channel._send_event.reset_mock()

    print("=== Test 8: Structure Action ===")
    result = await tool.execute(action="structure")
    print(f"Result: {result}")
    assert "structure" in result.lower() or "sent" in result.lower()
    print("[OK] Structure action OK\n")


async def test_validation():
    """Test parameter validation."""
    tool = LatexEditorTool()
    mock_channel = MagicMock()
    mock_channel._send_event = AsyncMock()
    tool.set_context(mock_channel, MagicMock())

    print("=== Test 9: Validation - Missing Action ===")
    result = await tool.execute()
    print(f"Result: {result}")
    assert "required" in result.lower()
    print("[OK] Missing action validation OK\n")

    print("=== Test 10: Validation - Set Without Content ===")
    result = await tool.execute(action="set")
    print(f"Result: {result}")
    assert "required" in result.lower()
    print("[OK] Set without content validation OK\n")

    print("=== Test 11: Validation - Replace Without Search ===")
    result = await tool.execute(action="replace")
    print(f"Result: {result}")
    assert "required" in result.lower()
    print("[OK] Replace without search validation OK\n")

    print("=== Test 12: Validation - Insert Without Line ===")
    result = await tool.execute(action="insert_line", content="test")
    print(f"Result: {result}")
    assert "required" in result.lower()
    print("[OK] Insert without line validation OK\n")

    print("=== Test 13: Validation - Unknown Action ===")
    result = await tool.execute(action="unknown_action")
    print(f"Result: {result}")
    assert "unknown" in result.lower()
    print("[OK] Unknown action validation OK\n")


async def main():
    print("=" * 50)
    print("LatexEditorTool Tests")
    print("=" * 50)
    print()

    await test_tool_basics()
    await test_no_connection()
    await test_with_mock_connection()
    await test_validation()

    print("=" * 50)
    print("All tests passed! [OK]")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
