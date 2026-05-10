"""
大五人格评估节点
基于五点量表评估用户大五人格特质（外向性、神经质、严谨性、开放性、宜人性）
仅输出人格特征分析，不提供职业建议
"""

import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from langchain_core.messages import HumanMessage, SystemMessage
from coze_coding_dev_sdk import LLMClient
from graphs.state import BigFiveAssessmentInput, BigFiveAssessmentOutput


# 大五人格问卷（五点量表，每维度8题，已正向化处理）
BIG_FIVE_QUESTIONS = {
    "神经质": {
        "N1": "我常常担心各种事情",
        "N2": "我容易感到紧张和不安",
        "N3": "我经常感到沮丧或情绪低落",
        "N4": "我容易因为小事而烦恼",
        "N5": "我经常感到焦虑",
        "N6": "我容易感到悲伤或失落",
        "N7": "我经常担心自己的健康",
        "N8": "我容易因为别人的评价而感到不安"
    },
    "严谨性": {
        "C1": "我做事情有条理，会提前规划",
        "C2": "我是一个细心的人",
        "C3": "我总是按时完成任务",
        "C4": "我注重细节，追求完美",
        "C5": "我言出必行，诚实守信",
        "C6": "我做事有计划，不冲动",
        "C7": "我能够坚持完成困难的任务",
        "C8": "我是一个可靠和值得信赖的人"
    },
    "宜人性": {
        "A1": "我善于与他人合作",
        "A2": "我相信大多数人是善良的",
        "A3": "我乐于帮助他人",
        "A4": "我善于理解他人的感受",
        "A5": "我尽量避免与他人发生冲突",
        "A6": "我信任朋友和同事",
        "A7": "我是一个有同情心的人",
        "A8": "我愿意为他人做出牺牲"
    },
    "开放性": {
        "O1": "我对新事物充满好奇",
        "O2": "我喜欢思考抽象的问题",
        "O3": "我乐于接受新的观点和想法",
        "O4": "我喜欢尝试不同的经历",
        "O5": "我具有丰富的想象力",
        "O6": "我喜欢艺术和音乐",
        "O7": "我善于独立思考",
        "O8": "我乐于探索未知领域"
    },
    "外向性": {
        "E1": "我喜欢与人交谈",
        "E2": "我在社交场合中很活跃",
        "E3": "我喜欢参加聚会和活动",
        "E4": "我是一个开朗乐观的人",
        "E5": "我喜欢成为关注的焦点",
        "E6": "我有很多朋友",
        "E7": "我精力充沛，喜欢尝试新事物",
        "E8": "我喜欢与陌生人交流"
    }
}


def big_five_assessment_node(
    state: BigFiveAssessmentInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> BigFiveAssessmentOutput:
    """
    title: 大五人格评估
    desc: 基于五点量表评估用户的大五人格特质（外向性、神经质、严谨性、开放性、宜人性），仅输出人格特征分析
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 计算大五人格评分
    big_five_scores = _calculate_big_five_scores(state.big_five_answers)
    
    # 如果有问卷答案，使用大模型进行人格分析
    if big_five_scores:
        # 读取大模型配置
        cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
        with open(cfg_file, 'r') as fd:
            _cfg = json.load(fd)
        
        llm_config = _cfg.get("config", {})
        sp = _cfg.get("sp", "")
        up = _cfg.get("up", "")
        
        # 使用大模型进行人格分析
        personality_analysis = _generate_personality_analysis(
            big_five_scores,
            state.big_five_answers,
            llm_config,
            sp,
            up
        )
        
        # 合并分析结果到评分中
        for dimension, analysis in personality_analysis.items():
            if dimension in big_five_scores and isinstance(analysis, dict):
                if "description" not in big_five_scores[dimension]:
                    big_five_scores[dimension]["description"] = analysis.get("description", "")
    
    return BigFiveAssessmentOutput(big_five_scores=big_five_scores)


def _calculate_big_five_scores(answers: Dict[str, int]) -> Dict[str, Any]:
    """
    计算大五人格各维度的原始分数和标准化分数
    
    五点量表评分标准（已正向化处理）：
    - 每维度8题，每题1-5分
    - 维度得分 = 8题平均分（1-5分制）
    - 等级划分：<2.5分较低，2.5-3.5分中等，>3.5分较高
    """
    scores = {}
    
    # 如果答案为空，返回空结果
    if not answers:
        return scores
    
    for dimension, questions in BIG_FIVE_QUESTIONS.items():
        dimension_answers = []
        for q_id, question_text in questions.items():
            if q_id in answers:
                score = answers[q_id]
                # 确保分数在1-5范围内（数据已正向化，无需反向计分）
                score = max(1, min(5, score))
                dimension_answers.append(score)
        
        if dimension_answers:
            avg_score = sum(dimension_answers) / len(dimension_answers)
            
            # 确定等级（五点量表）
            if avg_score < 2.5:
                level = "较低"
            elif avg_score <= 3.5:
                level = "中等"
            else:
                level = "较高"
            
            scores[dimension] = {
                "score": round(avg_score, 2),
                "level": level,
                "dimension_answers": dimension_answers,
                "description": ""
            }
    
    return scores


def _generate_personality_analysis(
    big_five_scores: Dict[str, Any],
    answers: Dict[str, int],
    llm_config: Dict,
    sp: str,
    up: str
) -> Dict[str, Any]:
    """
    使用大模型生成基于问卷的人格分析
    仅输出人格特征，不添加额外信息
    """
    # 构建分析提示
    answers_text = []
    for dim, questions in BIG_FIVE_QUESTIONS.items():
        for q_id, question in questions.items():
            if q_id in answers:
                answers_text.append(f"{q_id}: {answers[q_id]}分")
    
    prompt = f"""
请分析用户的大五人格特质。

问卷回答（1-5分制）：
{chr(10).join(answers_text)}

请输出JSON格式的分析结果：
{{
  "外向性": {{"score": 得分, "level": "等级", "description": "基于问卷的回答描述该维度特征"}},
  "神经质": {{"score": 得分, "level": "等级", "description": "基于问卷的回答描述该维度特征"}},
  "严谨性": {{"score": 得分, "level": "等级", "description": "基于问卷的回答描述该维度特征"}},
  "开放性": {{"score": 得分, "level": "等级", "description": "基于问卷的回答描述该维度特征"}},
  "宜人性": {{"score": 得分, "level": "等级", "description": "基于问卷的回答描述该维度特征"}}
}}

注意：只描述问卷能反映的信息，不要添加职业、兴趣等问卷未询问的内容。
"""
    
    try:
        llm_client = LLMClient(
            model=llm_config.get("model", "doubao-seed-1-8-251228"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_completion_tokens", 2000),
            thinking=llm_config.get("thinking", "disabled")
        )
        
        messages = [
            SystemMessage(content=sp),
            HumanMessage(content=prompt)
        ]
        
        response = llm_client.invoke(messages)
        
        # 处理 response.content
        if isinstance(response.content, str):
            analysis_text = response.content.strip()
        elif isinstance(response.content, list):
            content_parts = []
            for part in response.content:
                if isinstance(part, str):
                    content_parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    content_parts.append(part["text"])
            analysis_text = "".join(content_parts).strip()
        else:
            analysis_text = str(response.content)
        
        # 解析JSON响应
        if "```json" in analysis_text:
            json_start = analysis_text.find("```json") + 7
            json_end = analysis_text.find("```", json_start)
            analysis_text = analysis_text[json_start:json_end].strip()
        elif "```" in analysis_text:
            json_start = analysis_text.find("```") + 3
            json_end = analysis_text.find("```", json_start)
            analysis_text = analysis_text[json_start:json_end].strip()
        
        import json
        analysis = json.loads(analysis_text)
        return analysis
        
    except Exception as e:
        # 如果大模型调用失败，返回基于分数的简单分析
        return {
            dim: {
                "score": data.get("score", 0),
                "level": data.get("level", ""),
                "description": _get_default_description(dim, data.get("score", 0))
            }
            for dim, data in big_five_scores.items()
        }


def _get_default_description(dimension: str, score: float) -> str:
    """获取基于分数的简单描述"""
    level = "较低" if score < 2.5 else ("中等" if score <= 3.5 else "较高")
    
    descriptions = {
        "外向性": {
            "较低": "在社交场合中较为内敛，更喜欢独立工作或与少数熟悉的人交流",
            "中等": "在社交中表现适中，既能融入群体也享受独处",
            "较高": "性格开朗活泼，喜欢社交互动，在人群中表现积极主动"
        },
        "神经质": {
            "较低": "情绪较为稳定，不易被小事困扰，能较好地应对压力",
            "中等": "情绪有一定波动，在特定情况下会感到焦虑或担忧",
            "较高": "对情绪变化较为敏感，容易感到紧张或担忧"
        },
        "严谨性": {
            "较低": "做事较为随性，可能不太注重细节或计划",
            "中等": "有一定的责任感和条理性，会平衡计划与灵活性",
            "较高": "做事认真负责，有很强的计划性和自律性"
        },
        "开放性": {
            "较低": "思维较为务实，倾向于遵循传统方法",
            "中等": "对新事物有一定接受度，会在传统与创新间平衡",
            "较高": "思维开放，好奇心强，喜欢探索新想法和体验"
        },
        "宜人性": {
            "较低": "在人际交往中更注重个人目标，可能较少考虑他人感受",
            "中等": "能够与他人合作，但也会维护自己的立场",
            "较高": "善于合作共情，重视人际和谐，愿意帮助他人"
        }
    }
    
    return descriptions.get(dimension, {}).get(level, "")


# 获取问卷题目（供外部调用生成问卷）
def get_big_five_questionnaire() -> Dict[str, Dict[str, str]]:
    """
    返回大五人格问卷题目
    用于前端生成问卷表单
    """
    questions = {}
    for dimension, data in BIG_FIVE_QUESTIONS.items():
        questions[dimension] = {
            k: v for k, v in data.items() if k != "reverse"
        }
    return questions


# 获取问卷说明
def get_big_five_questionnaire_instructions() -> str:
    """
    返回问卷填写说明
    """
    return """
## 大五人格问卷说明

本问卷采用五点量表评估您的大五人格特质。

### 评分标准
- 1 = 完全不符合
- 2 = 比较不符合
- 3 = 中立/不确定
- 4 = 比较符合
- 5 = 完全符合

### 维度说明
1. **外向性**：描述人际交往中的活跃程度和社交倾向
2. **神经质**：描述情绪稳定性和心理调节能力
3. **严谨性**：描述自我约束、责任感和成就导向程度
4. **开放性**：描述对新事物的兴趣和接受程度
5. **宜人性**：描述人际合作、信任和利他程度

### 注意事项
- 请根据您的第一反应作答
- 没有对错之分，如实反映即可
"""
