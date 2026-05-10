"""
卡通形象提示词分析节点
基于用户基础信息和未来自我表征，分析生成卡通形象的专业提示词描述
"""

import os
import json
import re
from typing import Dict, Any
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import HumanMessage, SystemMessage
from graphs.state import CartoonPromptAnalysisInput, CartoonPromptAnalysisOutput


def cartoon_prompt_analysis_node(
    state: CartoonPromptAnalysisInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> CartoonPromptAnalysisOutput:
    """
    title: 卡通形象提示词分析
    desc: 基于用户基础信息和未来自我表征，分析生成卡通形象的详细提示词描述
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 步骤1: 读取大模型配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)

    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")

    # 步骤2: 使用大模型分析用户信息，推断职业形象特征
    
    # 构建用户信息描述
    user_info = f"""
    用户姓名: {state.user_name}
    性别: {state.user_gender}
    学历: {state.user_education}
    专业: {state.user_major}
    未来职业目标: {state.personal_question_1}
    未来自我表征: {', '.join(state.selected_representations)}
    """

    # 使用jinja2模板渲染提示词
    up_tpl = Template(up)
    user_prompt_content = up_tpl.render({"user_info": user_info})

    # 调用大模型分析
    llm_client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt_content)
    ]

    llm_response = llm_client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 1500),
        thinking=llm_config.get("thinking", "disabled")
    )

    # 安全提取响应内容
    if isinstance(llm_response.content, str):
        analysis_result = llm_response.content
    elif isinstance(llm_response.content, list):
        # 如果是列表，尝试提取文本
        text_parts = []
        for item in llm_response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        analysis_result = " ".join(text_parts)
    else:
        analysis_result = str(llm_response.content)

    analysis_result = analysis_result.strip()

    # 步骤3: 解析大模型返回的JSON，提取图像生成提示词
    try:
        # 尝试提取JSON部分
        json_match = re.search(r'\{[\s\S]*\}', analysis_result)
        if json_match:
            analysis_data = json.loads(json_match.group())
            career_identity = analysis_data.get("career_identity", "")
            image_prompt = analysis_data.get("image_prompt", "")
        else:
            # 如果没有JSON，直接使用返回的文本作为提示词
            career_identity = ""
            image_prompt = analysis_result
    except Exception as e:
        # 解析失败时，构建基础提示词
        career_identity = f"{state.user_gender}，{state.user_major}专业背景的专业形象"
        image_prompt = f"A professional cartoon avatar of a {state.user_gender} with {state.user_major} background, wearing appropriate business attire, confident and smiling expression, standing in a modern office environment, clean and vibrant cartoon style, simple background"

    return CartoonPromptAnalysisOutput(
        portrait_prompt=analysis_result,
        career_identity=career_identity,
        image_prompt_en=image_prompt
    )
