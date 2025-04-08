# ComfyUI MCP Server

A Model Context Protocol (MCP) server for ComfyUI that provides image generation and prompt optimization services.

## Features

- **Image Generation**: Generate images using ComfyUI text_to_image workflows
- **Prompt Optimization**: Optimize image generation prompts for better results

## Server Architecture

1. **Core Components**:
   - FastMCP framework implementation
   - ComfyUI API integration
   - Polling mechanism for result retrieval

2. **Key Functions**:
   - `generate_image`: Creates images from text prompts
   - `optimize_image_prompt`: Enhances input prompts for better generation results

3. **Technical Specifications**:
   - Automatic image dimension adjustment (multiples of 8)
   - Random seed generation for diverse outputs
   - Returns both local file paths and online accessible URLs

## Configuration

```json
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

## Requirements

- Python 3.7+
- ComfyUI instance running
- FastMCP library installed