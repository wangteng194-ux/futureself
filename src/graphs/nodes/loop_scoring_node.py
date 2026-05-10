"""
循环评分节点
批次处理每对表征的评分（每15组调用一次大模型）
"""

import os
import json
import re
from typing import Dict, List, Any
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from langchain_core.messages import HumanMessage, SystemMessage
from coze_coding_dev_sdk import LLMClient
from graphs.state import LoopScoringInput, LoopScoringOutput


def loop_scoring_node(
    state: LoopScoringInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> LoopScoringOutput:
    """
    title: 循环评分（批次优化）
    desc: 批次处理每对表征的评分，每15组调用一次大模型，大幅提升效率
    integrations: 大语言模型
    """
    ctx = runtime.context

    # 批次大小：每15组表征对调用一次大模型
    BATCH_SIZE = 15

    correlation_scores = []
    total_pairs = len(state.representation_pairs)
    num_batches = (total_pairs + BATCH_SIZE - 1) // BATCH_SIZE

    # 读取模型配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), "config/scoring_llm_cfg.json")
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)

    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")

    # 初始化大模型客户端
    llm_client = LLMClient(ctx=ctx)

    # 分批次处理
    for batch_idx in range(num_batches):
        start_idx = batch_idx * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_pairs)

        # 获取当前批次的数据
        batch_pairs = state.representation_pairs[start_idx:end_idx]
        batch_texts = state.representation_pairs_texts[start_idx:end_idx]

        # 构建批次输入
        batch_input = _build_batch_input(batch_pairs, batch_texts)

        # 渲染提示词模板
        up_tpl = Template(up)
        user_prompt_content = up_tpl.render({
            "batch_pairs": batch_input,
            "batch_number": batch_idx + 1,
            "total_batches": num_batches
        })

        # 调用大模型
        messages = [
            SystemMessage(content=sp),
            HumanMessage(content=user_prompt_content)
        ]

        try:
            llm_response = llm_client.invoke(
                messages=messages,
                model=llm_config.get("model", "doubao-seed-1-8-251228"),
                temperature=llm_config.get("temperature", 0.3),
                top_p=llm_config.get("top_p", 0.9),
                max_completion_tokens=llm_config.get("max_completion_tokens", 2000),
                thinking=llm_config.get("thinking", "disabled")
            )

            # 解析批次结果
            batch_results = _parse_batch_response(llm_response)
            correlation_scores.extend(batch_results)
        except Exception as e:
            # 如果批次处理失败，使用默认评分
            print(f"批次 {batch_idx + 1} 处理失败，使用默认评分: {str(e)}")
            for pair in batch_pairs:
                correlation_scores.append({
                    "rep1": pair["rep1"],
                    "rep2": pair["rep2"],
                    "correlation_score": 0  # 默认中性评分
                })

    return LoopScoringOutput(
        correlation_scores=correlation_scores
    )


def _build_batch_input(pairs: List[Dict[str, str]], texts: List[str]) -> str:
    """构建批次输入字符串"""
    batch_input = ""
    for i, (pair, text) in enumerate(zip(pairs, texts)):
        batch_input += f"\n## 表征对 {i+1}\n"
        batch_input += f"表征1：{pair['rep1']}\n"
        batch_input += f"表征2：{pair['rep2']}\n"
        batch_input += f"说明：{text}\n"
    return batch_input


def _parse_batch_response(llm_response) -> List[Dict[str, Any]]:
    """解析大模型返回的批次结果"""
    # 提取响应内容
    if isinstance(llm_response.content, str):
        response_content = llm_response.content
    elif isinstance(llm_response.content, list):
        text_parts = []
        for item in llm_response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        response_content = " ".join(text_parts)
    else:
        response_content = str(llm_response.content)

    results = []

    # 尝试解析 JSON 数组
    try:
        # 查找 JSON 数组
        json_match = re.search(r'\[[\s\S]*\]', response_content)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        results.append({
                            "rep1": item.get("rep1", ""),
                            "rep2": item.get("rep2", ""),
                            "correlation_score": int(item.get("correlation_score", 0))
                        })
    except Exception as e:
        print(f"JSON 解析失败: {str(e)}")

    return results

