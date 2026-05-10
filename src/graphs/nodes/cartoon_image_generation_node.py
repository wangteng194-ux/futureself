"""
卡通形象生成节点
基于提示词描述，调用豆包生图大模型生成卡通风格的未来自我画像
"""

import logging
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import ImageGenerationClient
from graphs.state import CartoonImageGenerationInput, CartoonImageGenerationOutput
from utils.file.file import File

# 配置日志
logger = logging.getLogger(__name__)


def cartoon_image_generation_node(
    state: CartoonImageGenerationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> CartoonImageGenerationOutput:
    """
    title: 卡通形象生成
    desc: 基于职业身份定位和英文提示词描述，调用豆包生图大模型生成卡通风格的未来自我画像
    integrations: 生图大模型
    """
    ctx = runtime.context
    
    # 使用职业身份定位和英文提示词
    career_identity = state.career_identity if state.career_identity else "professional"
    image_prompt = state.image_prompt_en if state.image_prompt_en and state.image_prompt_en.strip() else ""
    
    # 检查提示词是否为空
    if not image_prompt or not image_prompt.strip():
        logger.error("图像生成提示词为空，无法生成图像")
        return CartoonImageGenerationOutput(
            cartoon_portrait=File(url="", file_type="image")
        )
    
    logger.info(f"开始生成卡通形象，职业身份: {career_identity}，提示词长度: {len(image_prompt)} 字符")
    
    # 调用豆包生图大模型生成图像
    image_gen_client = ImageGenerationClient(ctx=ctx)
    
    # 生成卡通风格图像
    try:
        logger.info("调用豆包生图大模型...")
        image_response = image_gen_client.generate(
            prompt=image_prompt,
            size="2K",
            watermark=False
        )
        
        # 检查响应状态
        if not image_response.success:
            error_messages = image_response.error_messages if image_response.error_messages else ["未知错误"]
            logger.error(f"图像生成失败: {error_messages}")
            return CartoonImageGenerationOutput(
                cartoon_portrait=File(url="", file_type="image")
            )
        
        # 处理图像结果
        if len(image_response.image_urls) > 0:
            image_url = image_response.image_urls[0]
            logger.info(f"图像生成成功，URL: {image_url}")
            cartoon_portrait = File(url=image_url, file_type="image")
        else:
            logger.error("图像生成成功，但未返回图片URL")
            cartoon_portrait = File(url="", file_type="image")
            
    except ValueError as ve:
        logger.error(f"图像生成参数错误: {str(ve)}")
        cartoon_portrait = File(url="", file_type="image")
    except ConnectionError as ce:
        logger.error(f"图像生成网络连接错误: {str(ce)}")
        cartoon_portrait = File(url="", file_type="image")
    except TimeoutError as te:
        logger.error(f"图像生成超时: {str(te)}")
        cartoon_portrait = File(url="", file_type="image")
    except Exception as e:
        logger.error(f"图像生成异常: {type(e).__name__}: {str(e)}", exc_info=True)
        cartoon_portrait = File(url="", file_type="image")

    return CartoonImageGenerationOutput(
        cartoon_portrait=cartoon_portrait
    )
