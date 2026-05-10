"""
未来自我画像工作流主图
实现从用户输入到报告生成的完整流程
"""

from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)

# 导入所有节点
from graphs.nodes.cartoon_prompt_analysis_node import cartoon_prompt_analysis_node
from graphs.nodes.cartoon_image_generation_node import cartoon_image_generation_node
from graphs.nodes.representation_pairing_node import representation_pairing_node
from graphs.nodes.loop_scoring_node import loop_scoring_node
from graphs.nodes.network_analysis_node import network_analysis_node
from graphs.nodes.network_visualization_node import network_visualization_node
from graphs.nodes.job_analysis_node import job_analysis_node
from graphs.nodes.big_five_assessment_node import big_five_assessment_node
from graphs.nodes.chart_generation_node import chart_generation_node
from graphs.nodes.report_generation_node import report_generation_node


# 创建状态图
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点
# 1. 大五人格评估节点（第1步）
builder.add_node("big_five_assessment", big_five_assessment_node, metadata={"type": "agent", "llm_cfg": "config/big_five_assessment_llm_cfg.json"})

# 2. 表征配对节点（第2步）
builder.add_node("representation_pairing", representation_pairing_node)

# 3. 循环评分节点（第2步）
builder.add_node("loop_scoring", loop_scoring_node)

# 4. 网络分析节点（第2步）
builder.add_node("network_analysis", network_analysis_node)

# 5. 网络可视化节点（第2步）
builder.add_node("network_visualization", network_visualization_node)

# 6. 岗位分析节点（第3步）
builder.add_node("job_analysis", job_analysis_node)

# 7. 卡通形象提示词分析节点（第4步）
builder.add_node("cartoon_prompt_analysis", cartoon_prompt_analysis_node, metadata={"type": "agent", "llm_cfg": "config/cartoon_prompt_analysis_llm_cfg.json"})

# 8. 卡通形象生成节点（第4步）
builder.add_node("cartoon_image_generation", cartoon_image_generation_node)

# 9. 图表生成节点
builder.add_node("chart_generation", chart_generation_node)

# 10. 报告生成节点（第5步，整合报告）
builder.add_node("report_generation", report_generation_node, metadata={"type": "agent", "llm_cfg": "config/report_generation_llm_cfg.json"})

# 设置入口点
builder.set_entry_point("big_five_assessment")

# 添加边（调整后的线性流程）
# 第1步：大五人格评估
builder.add_edge("big_five_assessment", "representation_pairing")
# 第2步：表征配对 → 循环评分 → 网络分析 → 网络可视化
builder.add_edge("representation_pairing", "loop_scoring")
builder.add_edge("loop_scoring", "network_analysis")
builder.add_edge("network_analysis", "network_visualization")
# 第3步：岗位分析
builder.add_edge("network_visualization", "job_analysis")
# 第4步：卡通形象生成
builder.add_edge("job_analysis", "cartoon_prompt_analysis")
builder.add_edge("cartoon_prompt_analysis", "cartoon_image_generation")
# 图表生成
builder.add_edge("cartoon_image_generation", "chart_generation")
# 第5步：整合报告生成
builder.add_edge("chart_generation", "report_generation")
builder.add_edge("report_generation", END)

# 编译图
main_graph = builder.compile()
