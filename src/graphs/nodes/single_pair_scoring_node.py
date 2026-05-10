"""
单对表征评分节点
评估两个表征之间的相关性，使用5点量表（-2到+2）
"""

import os
import json
import re
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from langchain_core.messages import HumanMessage, SystemMessage
from coze_coding_dev_sdk import LLMClient
from graphs.state import SinglePairScoringInput, SinglePairScoringOutput


def single_pair_scoring_node(
    state: SinglePairScoringInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SinglePairScoringOutput:
    """
    title: 表征相关性评分
    desc: 评估两个表征之间的相关性，采用5点量表（-2非常有害到+2非常有帮助）
    integrations: 大语言模型
    """
    ctx = runtime.context

    # 读取模型配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)

    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")

    # 使用jinja2模板渲染用户提示词
    up_tpl = Template(up)
    user_prompt_content = up_tpl.render({
        "rep1": state.rep1,
        "rep2": state.rep2,
        "pair_text": state.pair_text
    })

    # 调用大模型
    client = LLMClient(ctx=ctx)

    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt_content)
    ]

    resp = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-pro-32k"),
        temperature=llm_config.get("temperature", 0.3),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 500),
        thinking=llm_config.get("thinking", "disabled")
    )

    # 安全提取响应内容
    if isinstance(resp.content, str):
        response_text = resp.content
    elif isinstance(resp.content, list):
        # 如果是列表，尝试提取文本
        text_parts = []
        for item in resp.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        response_text = " ".join(text_parts)
    else:
        response_text = str(resp.content)

    # 解析大模型返回的评分
    # 假设大模型返回JSON格式：{"correlation_score": -2}
    try:
        result = json.loads(response_text)
        correlation_score = result.get("correlation_score", 0)
    except Exception as e:
        # 如果解析失败，尝试提取数字
        correlation_score = 0
        match = re.search(r'-?\d+', response_text)
        if match:
            correlation_score = int(match.group())

        # 确保评分在有效范围内
        correlation_score = max(-2, min(2, correlation_score))

    return SinglePairScoringOutput(
        rep1=state.rep1,
        rep2=state.rep2,
        correlation_score=correlation_score
    )
