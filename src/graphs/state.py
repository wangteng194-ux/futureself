"""
未来自我画像工作流的状态定义
包含全局状态、图输入输出、以及各节点的输入输出定义
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field
from utils.file.file import File


# ========== 全局状态 ==========
class GlobalState(BaseModel):
    """全局状态定义，用于工作流中间数据的流转"""
    
    # 用户基本信息
    user_name: str = Field(default="", description="用户姓名")
    user_age: int = Field(default=0, description="用户年龄")
    user_gender: str = Field(default="", description="用户性别")
    user_education: str = Field(default="", description="用户学历")
    user_occupation: str = Field(default="", description="用户职业")
    company_type: str = Field(default="", description="企业类型")
    industry_type: str = Field(default="", description="行业类型")
    
    # 表征相关
    selected_representations: List[str] = Field(default=[], description="用户选择的表征列表（不超过25个）")
    representation_pairs: List[Dict[str, str]] = Field(default=[], description="表征两两配对列表")
    representation_pairs_texts: List[str] = Field(default=[], description="表征配对文本列表（用于大模型评分）")
    
    # 大五人格评估相关
    big_five_scores: Dict[str, Any] = Field(
        default={},
        description="大五人格评分，格式：{'外向性': {'score': 4.2, 'level': '较高', 'description': '...'}, '神经质': {...}, '严谨性': {...}, '开放性': {...}, '宜人性': {...}}"
    )
    personality_profile: str = Field(default="", description="人格特质综合分析报告")
    
    # 评分相关
    correlation_scores: List[Dict[str, Any]] = Field(default=[], description="每对表征的相关性评分")
    complementarity_score: float = Field(default=0.0, description="互补性评分")
    conflict_score: float = Field(default=0.0, description="冲突性评分")
    network_analysis_interpretation: str = Field(default="", description="未来自我网络分析解读（说明网络说明了什么）")
    
    # 卡通形象相关
    portrait_prompt: str = Field(default="", description="卡通形象生成提示词（中文）")
    image_prompt_en: str = Field(default="", description="卡通形象生成提示词（英文）")
    
    # 可视化相关
    network_graph: File = Field(default=None, description="表征网络密度图（互补性）")
    conflict_graph: File = Field(
        default=None,
        description="表征网络密度图（冲突性）"
    )
    label_mapping: List[Dict[str, str]] = Field(
        default=[],
        description="节点标签映射列表，格式为 [{'label': '表征名称', 'representation': '表征名称'}, ...]"
    )
    radar_chart: File = Field(default=None, description="表征能力雷达图")
    bar_chart: File = Field(default=None, description="岗位适配度评分柱状图")
    cartoon_portrait: File = Field(default=None, description="卡通风格未来自我画像")
    
    # 岗位分析相关
    market_trend: str = Field(default="", description="市场趋势分析")
    recommended_jobs: List[Dict[str, Any]] = Field(
        default=[],
        description="推荐岗位列表"
    )
    job_fit_score: float = Field(default=0.0, description="岗位适配度评分")
    skill_gap_analysis: str = Field(default="", description="技能差距分析")
    
    # 个性化问题
    personal_question_1: str = Field(default="", description="问题1：面对自己的职业发展，在3-5年内，你最关心什么问题？")
    personal_question_2: str = Field(default="", description="问题2：面对自己的知识学习，在3-5年内，你最关心什么问题？")
    personal_question_3: str = Field(default="", description="问题3：面对自己的生活愿景，在3-5年内，你最关心什么问题？")
    
    # 最终报告
    final_report: str = Field(default="", description="生成的未来自我画像职业规划报告")


# ========== 图输入输出 ==========
class GraphInput(BaseModel):
    """工作流的输入"""
    user_name: str = Field(..., description="用户姓名（可为邮箱或其他标识）")
    user_gender: str = Field(..., description="用户性别")
    user_education: str = Field(..., description="用户学历")
    user_major: str = Field(default="", description="用户专业")
    selected_representations: List[str] = Field(..., description="用户选择的表征列表（不超过25个）")
    # 三个个性化问题
    personal_question_1: str = Field(..., description="问题1：面对自己的职业发展，在3-5年内，你最关心什么问题？")
    personal_question_2: str = Field(..., description="问题2：面对自己的知识学习，在3-5年内，你最关心什么问题？")
    personal_question_3: str = Field(..., description="问题3：面对自己的生活愿景，在3-5年内，你最关心什么问题？")
    # 大五人格问卷回答（五点量表，1-5分，每维度8题）
    big_five_answers: Dict[str, int] = Field(
        default={},
        description="大五人格问卷回答，格式：{'N1-N8': 神经质8题, 'C1-C8': 严谨性8题, 'A1-A8': 宜人性8题, 'O1-O8': 开放性8题, 'E1-E8': 外向性8题}"
    )


class GraphOutput(BaseModel):
    """工作流的输出"""
    final_report: str = Field(..., description="生成的未来自我画像职业规划报告")
    final_report_pdf: File = Field(default=None, description="生成的未来自我画像职业规划报告PDF文件")
    network_graph: File = Field(default=None, description="表征网络密度图（互补性）")
    conflict_graph: File = Field(default=None, description="表征网络密度图（冲突性）")
    radar_chart: File = Field(default=None, description="表征能力雷达图")
    bar_chart: File = Field(default=None, description="岗位适配度评分柱状图")
    cartoon_portrait: File = Field(default=None, description="卡通风格未来自我画像")
    complementarity_score: float = Field(..., description="互补性评分")
    conflict_score: float = Field(..., description="冲突性评分")


# ========== 节点输入输出定义 ==========

# 1. 表征配对节点
class RepresentationPairingInput(BaseModel):
    """表征配对节点的输入"""
    selected_representations: List[str] = Field(..., description="用户选择的表征列表")


class RepresentationPairingOutput(BaseModel):
    """表征配对节点的输出"""
    representation_pairs: List[Dict[str, str]] = Field(..., description="表征两两配对列表，格式：[{'rep1': '表征1', 'rep2': '表征2'}, ...]")
    representation_pairs_texts: List[str] = Field(..., description="表征配对文本列表，用于大模型评分")


# 2. 评分节点（用于子图循环）
class SinglePairScoringInput(BaseModel):
    """单对表征评分节点的输入"""
    pair_text: str = Field(..., description="表征配对文本")
    rep1: str = Field(..., description="第一个表征")
    rep2: str = Field(..., description="第二个表征")


class SinglePairScoringOutput(BaseModel):
    """单对表征评分节点的输出"""
    rep1: str = Field(..., description="第一个表征")
    rep2: str = Field(..., description="第二个表征")
    correlation_score: int = Field(..., description="相关性评分，范围-2到+2")


# 3. 循环评分节点（调用子图）
class LoopScoringInput(BaseModel):
    """循环评分节点的输入"""
    representation_pairs_texts: List[str] = Field(..., description="表征配对文本列表")
    representation_pairs: List[Dict[str, str]] = Field(..., description="表征两两配对列表")


class LoopScoringOutput(BaseModel):
    """循环评分节点的输出"""
    correlation_scores: List[Dict[str, Any]] = Field(..., description="每对表征的相关性评分")


# 4. 网络分析节点
class NetworkAnalysisInput(BaseModel):
    """网络分析节点的输入"""
    correlation_scores: List[Dict[str, Any]] = Field(..., description="每对表征的相关性评分")
    representation_pairs: List[Dict[str, str]] = Field(..., description="表征两两配对列表")


class NetworkAnalysisOutput(BaseModel):
    """网络分析节点的输出"""
    complementarity_score: float = Field(..., description="互补性评分")
    conflict_score: float = Field(..., description="冲突性评分")
    correlation_scores: List[Dict[str, Any]] = Field(..., description="每对表征的相关性评分（包含计算后的结果）")
    network_analysis_interpretation: str = Field(..., description="未来自我网络分析解读（说明网络说明了什么）")


# 5. 网络可视化节点
class NetworkVisualizationInput(BaseModel):
    """网络可视化节点的输入"""
    correlation_scores: List[Dict[str, Any]] = Field(..., description="每对表征的相关性评分")
    selected_representations: List[str] = Field(..., description="用户选择的表征列表")


class NetworkVisualizationOutput(BaseModel):
    """网络可视化节点的输出"""
    network_graph: File = Field(..., description="生成的表征互补性网络密度图")
    label_mapping: List[Dict[str, str]] = Field(
        default=[],
        description="节点标签映射列表，格式为 [{'label': '表征名称', 'representation': '表征名称'}, ...]"
    )
    conflict_graph: File = Field(
        default=None,
        description="生成的表征冲突性网络密度图"
    )


# 6. 岗位分析节点
class JobAnalysisInput(BaseModel):
    """岗位分析节点的输入"""
    user_name: str = Field(..., description="用户姓名")
    user_gender: str = Field(..., description="用户性别")
    user_education: str = Field(default="", description="用户学历")
    user_major: str = Field(default="", description="用户专业")
    selected_representations: List[str] = Field(..., description="用户选择的表征列表")
    personal_question_1: str = Field(..., description="个性化问题1的回答（包含职业目标）")


class JobAnalysisOutput(BaseModel):
    """岗位分析节点的输出"""
    market_trend: str = Field(..., description="市场趋势分析（行业发展、需求变化、薪资水平）")
    recommended_jobs: List[Dict[str, Any]] = Field(
        default=[],
        description="推荐岗位列表，每个包含：岗位名称、公司、薪资范围、要求"
    )


# 7. 图表生成节点
class ChartGenerationInput(BaseModel):
    """图表生成节点的输入"""
    complementarity_score: float = Field(..., description="互补性评分")
    conflict_score: float = Field(..., description="冲突性评分")
    selected_representations: List[str] = Field(..., description="用户选择的表征列表")
    correlation_scores: List[Dict[str, Any]] = Field(default=[], description="表征相关性评分")


class ChartGenerationOutput(BaseModel):
    """图表生成节点的输出"""
    radar_chart: File = Field(..., description="表征能力雷达图")


# 7.5. 卡通形象提示词分析节点
class CartoonPromptAnalysisInput(BaseModel):
    """卡通形象提示词分析节点的输入"""
    user_name: str = Field(..., description="用户姓名")
    user_gender: str = Field(..., description="用户性别")
    user_education: str = Field(default="", description="用户学历")
    user_major: str = Field(default="", description="用户专业")
    selected_representations: List[str] = Field(..., description="用户选择的表征列表")
    personal_question_1: str = Field(..., description="个性化问题1的回答（包含职业目标）")


class CartoonPromptAnalysisOutput(BaseModel):
    """卡通形象提示词分析节点的输出"""
    portrait_prompt: str = Field(..., description="用于生成图像的提示词描述")
    career_identity: str = Field(default="", description="职业身份定位")
    image_prompt_en: str = Field(default="", description="英文图像生成提示词")


# 7.6. 卡通形象生成节点
class CartoonImageGenerationInput(BaseModel):
    """卡通形象生成节点的输入"""
    career_identity: str = Field(..., description="职业身份定位")
    image_prompt_en: str = Field(..., description="英文图像生成提示词")


class CartoonImageGenerationOutput(BaseModel):
    """卡通形象生成节点的输出"""
    cartoon_portrait: File = Field(..., description="生成的卡通风格未来自我画像")


# 8. 大五人格评估节点
class BigFiveAssessmentInput(BaseModel):
    """大五人格评估节点的输入"""
    user_name: str = Field(..., description="用户姓名（可为邮箱或其他标识）")
    user_gender: str = Field(..., description="用户性别")
    user_education: str = Field(default="", description="用户学历")
    user_major: str = Field(default="", description="用户专业")
    selected_representations: List[str] = Field(..., description="用户选择的表征列表")
    personal_question_1: str = Field(..., description="个性化问题1的回答")
    personal_question_2: str = Field(..., description="个性化问题2的回答")
    personal_question_3: str = Field(..., description="个性化问题3的回答")
    big_five_answers: Dict[str, int] = Field(
        default={},
        description="大五人格问卷回答（40题完整版），格式：{'N1-N8': 神经质8题, 'C1-C8': 严谨性8题, 'A1-A8': 宜人性8题, 'O1-O8': 开放性8题, 'E1-E8': 外向性8题}"
    )


class BigFiveAssessmentOutput(BaseModel):
    """大五人格评估节点的输出"""
    big_five_scores: Dict[str, Any] = Field(
        ...,
        description="大五人格评分，格式：{'外向性': {'score': 4.2, 'level': '较高', 'description': '...'}, ...}"
    )


# 9. 报告生成节点
class ReportGenerationInput(BaseModel):
    """报告生成节点的输入"""
    user_name: str = Field(..., description="用户姓名")
    user_gender: str = Field(..., description="用户性别")
    user_education: str = Field(default="", description="用户学历")
    user_major: str = Field(default="", description="用户专业")
    selected_representations: List[str] = Field(..., description="用户选择的表征列表")
    personal_question_1: str = Field(..., description="个性化问题1的回答")
    personal_question_2: str = Field(..., description="个性化问题2的回答")
    personal_question_3: str = Field(..., description="个性化问题3的回答")
    complementarity_score: float = Field(..., description="互补性评分")
    conflict_score: float = Field(..., description="冲突性评分")
    correlation_scores: List[Dict[str, Any]] = Field(default=[], description="表征相关性评分")
    market_trend: str = Field(default="", description="市场趋势分析")
    recommended_jobs: List[Dict[str, Any]] = Field(default=[], description="推荐岗位列表")
    job_fit_score: float = Field(default=0.0, description="岗位适配度评分")
    skill_gap_analysis: str = Field(default="", description="技能差距分析")
    network_graph: File = Field(default=None, description="表征网络图")
    conflict_graph: File = Field(default=None, description="表征冲突性网络图")
    radar_chart: File = Field(default=None, description="表征能力雷达图")
    bar_chart: File = Field(default=None, description="岗位适配度评分柱状图")
    cartoon_portrait: File = Field(default=None, description="卡通风格未来自我画像")
    label_mapping: List[Dict[str, str]] = Field(
        default=[],
        description="节点标签映射列表，格式为 [{'label': 'R1', 'representation': '有创造力'}, ...]"
    )
    # 大五人格评估结果
    big_five_scores: Dict[str, Any] = Field(
        default={},
        description="大五人格评分，格式：{'外向性': {'score': 4.2, 'level': '较高', 'description': '...'}, ...}"
    )
    # 网络分析解读
    network_analysis_interpretation: str = Field(
        default="",
        description="未来自我网络分析解读"
    )


class ReportGenerationOutput(BaseModel):
    """报告生成节点的输出"""
    final_report: str = Field(..., description="生成的未来自我画像职业规划报告")
    final_report_pdf: File = Field(..., description="生成的未来自我画像职业规划报告PDF文件")
