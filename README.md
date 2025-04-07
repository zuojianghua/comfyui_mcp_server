# comfyui_mcp_server
generate_image and other workflows

**mcp server config**

```
{
  "mcpServers": {
    "ComfyUI_MCP_Server": {
      "disabled": false,
      "timeout": 600,
      "command": "python",
      "args": [
        "D:\\code\\comfyui_mcp_server\\server.py"
      ],
      "env": {
        "COMFY_URL": "http://127.0.0.1:8188/"
      },
      "transportType": "stdio"
    }
  }
}
```