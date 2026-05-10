"""
网络分析节点
计算互补性评分和冲突性评分，并生成解读
"""

from typing import List, Dict
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import NetworkAnalysisInput, NetworkAnalysisOutput


def network_analysis_node(
    state: NetworkAnalysisInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> NetworkAnalysisOutput:
    """
    title: 网络分析
    desc: 计算互补性评分和冲突性评分，并生成未来自我网络分析解读
    integrations: 无
    """
    ctx = runtime.context
    
    correlation_scores = state.correlation_scores
    representation_pairs = state.representation_pairs
    
    # 计算总关系数
    total_pairs = len(correlation_scores)
    if total_pairs == 0:
        return NetworkAnalysisOutput(
            complementarity_score=0.0,
            conflict_score=0.0,
            correlation_scores=correlation_scores,
            network_analysis_interpretation="暂无表征数据，无法进行分析。"
        )
    
    # 计算互补性评分（正关系评分总和 / 总关系数）
    positive_sum = sum(score.get("correlation_score", 0) for score in correlation_scores if score.get("correlation_score", 0) > 0)
    complementarity_score = positive_sum / total_pairs
    
    # 计算冲突性评分（负关系评分总和 / 总关系数）
    negative_sum = sum(abs(score.get("correlation_score", 0)) for score in correlation_scores if score.get("correlation_score", 0) < 0)
    conflict_score = negative_sum / total_pairs
    
    # 生成网络分析解读
    interpretation = _generate_network_interpretation(
        correlation_scores, 
        complementarity_score, 
        conflict_score,
        representation_pairs
    )
    
    return NetworkAnalysisOutput(
        complementarity_score=round(complementarity_score, 2),
        conflict_score=round(conflict_score, 2),
        correlation_scores=correlation_scores,
        network_analysis_interpretation=interpretation
    )


def _generate_network_interpretation(
    correlation_scores: List[Dict],
    complementarity_score: float,
    conflict_score: float,
    representation_pairs: List[Dict[str, str]]
) -> str:
    """
    生成未来自我网络分析解读
    """
    # 找出最强的互补关系
    positive_pairs = []
    negative_pairs = []
    
    for i, score in enumerate(correlation_scores):
        if score.get("correlation_score", 0) > 0 and i < len(representation_pairs):
            positive_pairs.append({
                "rep1": representation_pairs[i].get("rep1", ""),
                "rep2": representation_pairs[i].get("rep2", ""),
                "score": score.get("correlation_score", 0)
            })
        elif score.get("correlation_score", 0) < 0 and i < len(representation_pairs):
            negative_pairs.append({
                "rep1": representation_pairs[i].get("rep1", ""),
                "rep2": representation_pairs[i].get("rep2", ""),
                "score": abs(score.get("correlation_score", 0))
            })
    
    # 按评分排序
    positive_pairs.sort(key=lambda x: x["score"], reverse=True)
    negative_pairs.sort(key=lambda x: x["score"], reverse=True)
    
    # 构建解读文本
    interpretation_parts = []
    
    # 整体概述
    if complementarity_score > conflict_score:
        interpretation_parts.append(f"您的未来自我网络呈现【协同发展型】特征。互补性评分为{complementarity_score}，高于冲突性评分{conflict_score}，说明您追求的表征特质之间能够相互促进、形成正向循环。")
    elif conflict_score > 0:
        interpretation_parts.append(f"您的未来自我网络呈现【张力平衡型】特征。互补性评分为{complementarity_score}，冲突性评分为{conflict_score}，说明您的表征特质之间存在一定张力，但这种张力可以转化为成长动力。")
    else:
        interpretation_parts.append(f"您的未来自我网络呈现【和谐统一型】特征。互补性评分为{complementarity_score}，冲突性评分为0，说明您追求的表征特质之间高度和谐，可以协同发展。")
    
    # 最强互补关系
    if positive_pairs:
        top_positive = positive_pairs[:3]
        interpretation_parts.append("\n【核心协同关系】：")
        for pair in top_positive:
            interpretation_parts.append(f"• {pair['rep1']} 与 {pair['rep2']} 形成强互补（+{pair['score']}），这两个特质可以相互强化，共同提升您的职业竞争力。")
    
    # 潜在冲突关系
    if negative_pairs:
        interpretation_parts.append("\n【需要关注的张力点】：")
        for pair in negative_pairs[:3]:
            interpretation_parts.append(f"• {pair['rep1']} 与 {pair['rep2']} 存在一定竞争（-{pair['score']}），在职业发展中需要平衡这两个特质，避免顾此失彼。")
    
    # 综合建议
    interpretation_parts.append("\n【发展建议】：")
    if complementarity_score > conflict_score:
        interpretation_parts.append("您的表征特质形成了良好的协同生态，建议在职业发展中充分利用这种协同效应，将相互促进的特质组合在一起发展，实现1+1>2的效果。")
    elif conflict_score > 0:
        interpretation_parts.append("您的表征特质之间存在一定张力，这是正常的成长挑战。建议在不同的职业阶段有所侧重，学会在冲突特质之间找到平衡点，将张力转化为成长动力。")
    else:
        interpretation_parts.append("您的表征特质高度一致，建议在保持核心优势的同时，适当拓展新的特质维度，增加职业发展的韧性和适应性。")
    
    return "\n".join(interpretation_parts)
