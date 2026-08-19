"""Tests for tool registration."""

import asyncio

from miro_mcp import create_mcp


def test_create_mcp_registers_all_tools():
    mcp = create_mcp()
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    expected = {
        "list_boards",
        "get_board",
        "list_items",
        "get_item",
        "create_item",
        "update_item",
        "delete_item",
        "set_text",
        "set_color",
        "resize_item",
        "move_item",
        "add_to_frame",
        "create_sticky_note",
        "create_card",
        "create_text",
        "create_shape",
        "create_frame",
        "create_image",
        "create_document",
        "create_embed",
        "create_connector",
        "list_tags",
        "create_tag",
        "assign_tag",
    }
    assert expected <= names, expected - names
    assert len(tools) == 24
