"""
评分循环子图
用于循环处理每对表征的评分
"""

from typing import List, Dict, Optional, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from graphs.state import (
    GlobalState,
    SinglePairScoringInput,
    SinglePairScoringOutput
)


# 定义子图的状态类
class LoopState(BaseModel):
    """循环子图的状态定义"""
    representation_pairs_texts: List[str] = Field(default=[], description="表征配对文本列表")
    representation_pairs: List[Dict[str, str]] = Field(default=[], description="表征两两配对列表")
    current_index: int = Field(default=0, description="当前处理的索引")
    correlation_scores: List[Dict[str, Any]] = Field(default=[], description="评分结果列表")


# 定义子图的输入输出
class LoopInput(BaseModel):
    """循环子图的输入"""
    representation_pairs_texts: List[str] = Field(..., description="表征配对文本列表")
    representation_pairs: List[Dict[str, str]] = Field(..., description="表征两两配对列表")


class LoopOutput(BaseModel):
    """循环子图的输出"""
    correlation_scores: List[Dict[str, Any]] = Field(..., description="评分结果列表")


# 条件判断函数：判断是否还有待处理的表征对
def has_more_pairs(state: LoopState) -> str:
    """
    title: 是否还有待处理的表征对
    desc: 判断是否还有待处理的表征对
    """
    if state.current_index < len(state.representation_pairs_texts):
        return "继续评分"
    else:
        return "结束循环"


    # 评分处理节点
def scoring_process(state: LoopState) -> LoopState:
    """
    title: 评分处理
    desc: 对当前表征对进行评分
    integrations: 大语言模型
    """
    from graphs.nodes.single_pair_scoring_node import single_pair_scoring_node
    from langchain_core.runnables import RunnableConfig
    from langgraph.runtime import Runtime
    from coze_coding_utils.runtime_ctx.context import Context, new_context

    # 获取当前表征对
    current_pair = state.representation_pairs[state.current_index]
    pair_text = state.representation_pairs_texts[state.current_index]

    # 创建输入状态
    input_state = SinglePairScoringInput(
        rep1=current_pair["rep1"],
        rep2=current_pair["rep2"],
        pair_text=pair_text
    )

    # 创建临时配置
    temp_config = RunnableConfig(
        metadata={
            "llm_cfg": "config/scoring_llm_cfg.json"
        }
    )

    # 创建临时runtime
    # Runtime不接受构造函数参数，泛型参数是Context
    temp_runtime = Runtime()  # type: ignore

    # 调用评分节点
    result = single_pair_scoring_node(input_state, temp_config, temp_runtime)

    # 将评分结果添加到列表
    new_scores = state.correlation_scores.copy()
    new_scores.append({
        "rep1": result.rep1,
        "rep2": result.rep2,
        "correlation_score": result.correlation_score
    })

    # 更新索引
    new_index = state.current_index + 1

    # 返回更新后的状态
    return LoopState(
        representation_pairs_texts=state.representation_pairs_texts,
        representation_pairs=state.representation_pairs,
        current_index=new_index,
        correlation_scores=new_scores
    )


# 创建子图
def create_scoring_loop_graph():
    """
    创建评分循环子图
    """
    # 创建子图
    builder = StateGraph(LoopState, input_schema=LoopInput, output_schema=LoopOutput)

    # 添加节点
    builder.add_node("scoring_process", scoring_process)

    # 设置入口点
    builder.set_entry_point("scoring_process")

    # 添加条件分支
    builder.add_conditional_edges(
        source="scoring_process",
        path=has_more_pairs,
        path_map={
            "继续评分": "scoring_process",
            "结束循环": END
        }
    )

    # 编译子图
    return builder.compile()


# 创建子图实例
scoring_loop_graph = create_scoring_loop_graph()

