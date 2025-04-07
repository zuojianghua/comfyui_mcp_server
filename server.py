from mcp.server.fastmcp import FastMCP, Image, Context
import json
import time
import os
import requests
from pathlib import Path
import random

mcp = FastMCP("Comfy MCP Server", log_1evel='ERROR')
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
    print(f"开始轮询请求: {prompt_id}")
    while True:
        try:
            response = requests.get(
                f"{host}/history/{prompt_id}",
                timeout=600
            )
            result = response.json()
            if prompt_id in result and result[prompt_id].get('outputs'):
                outputs = result[prompt_id]['outputs']
                print(f"ComfyUI返回结果: {outputs}")
                
                if outputs and output_id in outputs:
                    # 获取输出路径
                    output_info = outputs[output_id].get(output_type)
                    if isinstance(output_info, list) and len(output_info) > 0:
                        # 如果返回的是列表，取第一个元素
                        output_data = output_info[0]
                    # 构建完整的输出路径
                    output_path = str(Path(output_data["subfolder"]) / output_data["filename"])
                    
                    image_url = f"{host.rstrip('/')}/view?filename={output_data.get('filename')}&subfolder={output_data.get('subfolder')}&type=output"
                    print(f"生成的文件路径: {output_path}")
                    print(f"在线访问路径: {image_url}")
                    if callback:
                        callback(prompt_id, output_path, image_url)
                    return output_path, image_url
                else:
                    print("未找到输出")
                    if callback:
                        callback(prompt_id, None)
                    return None
                    
            print(f"正在等待生成: {prompt_id}")
            time.sleep(3)
        except Exception as e:
            print(f"轮询请求失败: {e}")
            time.sleep(2)

@mcp.tool()
def generate_image(prompt: str, width: int, height: int, ctx: Context):
    """generate image using ComfyUI text_to_image workflows"""
    
    # 读取工作流文件: workflows/text_to_image.json
    import os
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
