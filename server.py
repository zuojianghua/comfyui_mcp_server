from fastmcp import FastMCP, Image, Context
from fastmcp.prompts.base import UserMessage, AssistantMessage
import json
import time
import os
import requests
from pathlib import Path
import random
import logging
from pydantic import Field
from typing import Annotated


logger = logging.getLogger("mcp")

mcp = FastMCP("Comfy MCP Server", log_level='ERROR')
host = os.environ.get("COMFY_URL")

def poll_request(prompt_id, output_id, output_type, callback=None):
    """
    轮询获取ComfyUI任务结果
    
    参数:
    - prompt_id: 任务ID
    - callback: 回调函数，用于通知任务完成
    
    返回:
    - 任务输出结果
    """
    logger.info(f"开始轮询请求: {prompt_id}")
    while True:
        try:
            response = requests.get(
                f"{host}/history/{prompt_id}",
                timeout=600
            )
            result = response.json()
            if prompt_id in result and result[prompt_id].get('outputs'):
                outputs = result[prompt_id]['outputs']
                logger.info(f"ComfyUI返回结果: {outputs}")
                
                if outputs and output_id in outputs:
                    # 获取输出路径
                    output_info = outputs[output_id].get(output_type)
                    if isinstance(output_info, list) and len(output_info) > 0:
                        # 如果返回的是列表，取第一个元素
                        output_data = output_info[0]
                    # 构建完整的输出路径
                    output_path = str(Path(output_data["subfolder"]) / output_data["filename"])
                    
                    image_url = f"{host.rstrip('/')}/view?filename={output_data.get('filename')}&subfolder={output_data.get('subfolder')}&type=output"
                    logger.info(f"生成的文件路径: {output_path}")
                    logger.info(f"在线访问路径: {image_url}")
                    if callback:
                        callback(prompt_id, output_path, image_url)
                    return output_path, image_url
                else:
                    logger.info("未找到输出")
                    if callback:
                        callback(prompt_id, None)
                    return None
                    
            logger.info(f"正在等待生成: {prompt_id}")
            time.sleep(3)
        except Exception as e:
            logger.error(f"轮询请求失败: {e}")
            time.sleep(2)

@mcp.tool(name="Generate Image", description="Generate image using ComfyUI text_to_image workflows. the prompt must in english language. ")
def generate_image(
    prompt: Annotated[str, Field(description="The text prompt to generate the image. prompt must in english language. e.g. 'A beautiful sunset over the mountains'")], 
    width: Annotated[int, Field(description="The width of the generated image. Must be a multiple of 8.")], 
    height: Annotated[int, Field(description="The height of the generated image. Must be a multiple of 8.")], 
    ctx: Context):
    """generate image using ComfyUI text_to_image workflows. the prompt must in english language. 

    Returns:
        - dict: A dictionary containing the URL of the generated image with the key 'image_url'.
    """
    
    # 读取工作流文件: workflows/text_to_image.json
    workflow_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows", "text_to_image.json")
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # 更新工作流参数
    workflow["3"]["inputs"]["text"] = prompt
    workflow["6"]["inputs"]["width"] = int(width/8) * 8
    workflow["6"]["inputs"]["height"] = int(height/8) * 8
    # 生成12位随机整数作为seed
    workflow["1"]["inputs"]["seed"] = random.randint(100000000000, 999999999999)

    # 发送请求
    response = requests.post(
        f"{host}/prompt",
        json={"prompt": workflow},
        headers={'Content-Type': 'application/json'},
        timeout=600
    )
    ctx.info("Submitted prompt")
    response.raise_for_status()
    prompt_id = response.json()['prompt_id']
    
    ctx.info("Checking status...")
    image_path, image_url = poll_request(prompt_id, "10", "images")
    ctx.info("Image generated")

    return {"image_url": image_url}

@mcp.prompt(name="Optimize prompt", description="Optimize the image generation prompt for better results")
def optimize_image_prompt(
    user_prompt: Annotated[str, Field(description="The text prompt to optimize. e.g. 'A beautiful sunset over the mountains'")],
    ):
    """Optimize the image generation prompt for better results"""

    system_prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts", "optimize_prompt.txt")
    with open(system_prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    return[
        UserMessage(system_prompt),
        UserMessage(user_prompt)
    ]

def run_server():
    errors = []
    if host is None:
        errors.append("- COMFY_URL environment variable not set")

    if len(errors) > 0:
        errors = ["Failed to start Comfy MCP Server:"] + errors
        return "\n".join(errors)
    else:
        mcp.run()


if __name__ == "__main__":
    run_server()
