"""
表征配对节点
将用户选择的表征两两配对，生成配对列表
"""

from typing import List, Dict
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import RepresentationPairingInput, RepresentationPairingOutput


def representation_pairing_node(
    state: RepresentationPairingInput, 
    config: RunnableConfig, 
    runtime: Runtime[Context]
) -> RepresentationPairingOutput:
    """
    title: 表征配对
    desc: 将用户选择的表征两两配对，生成配对列表
    integrations: 无
    """
    ctx = runtime.context
    
    # 获取用户选择的表征列表
    representations = state.selected_representations
    
    # 生成两两配对
    pairs = []
    pair_texts = []
    
    n = len(representations)
    for i in range(n):
        for j in range(i + 1, n):
            pair = {
                'rep1': representations[i],
                'rep2': representations[j]
            }
            pairs.append(pair)
            
            # 生成配对文本，用于大模型评分
            pair_text = f"表征1：{representations[i]}\n表征2：{representations[j]}\n请评估这两个表征之间的相关性。"
            pair_texts.append(pair_text)
    
    return RepresentationPairingOutput(
        representation_pairs=pairs,
        representation_pairs_texts=pair_texts
    )
