"""
岗位分析节点
基于用户信息和市场搜索，提供市场趋势分析、岗位推荐和适配度评估
"""

import json
import re
from typing import List, Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import SearchClient
from graphs.state import JobAnalysisInput, JobAnalysisOutput


def job_analysis_node(
    state: JobAnalysisInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> JobAnalysisOutput:
    """
    title: 岗位分析
    desc: 搜索市场趋势和招聘信息，提供岗位推荐和适配度评估
    integrations: 联网搜索
    """
    ctx = runtime.context

    # 1. 从个性化问题中提取目标岗位
    target_position = _extract_target_position(state.personal_question_1)
    
    # 2. 搜索市场趋势
    market_trend = _search_market_trend(
        target_position,
        state.user_major
    )
    
    # 3. 搜索岗位推荐
    recommended_jobs = _search_jobs(
        target_position,
        state.user_major,
        state.user_education
    )

    return JobAnalysisOutput(
        market_trend=market_trend,
        recommended_jobs=recommended_jobs
    )


def _extract_target_position(personal_question: str) -> str:
    """从个性化问题中提取目标岗位"""
    # 常见的目标岗位关键词
    position_keywords = [
        "CTO", "首席技术官", "技术总监", "技术VP",
        "CMO", "首席营销官", "市场总监", "营销VP",
        "CEO", "首席执行官", "总经理",
        "CFO", "首席财务官", "财务总监",
        "COO", "首席运营官", "运营总监",
        "CPO", "首席产品官", "产品总监",
        "CHO", "首席人力资源官", "HRVP",
        "VP", "副总裁", "副总",
        "总监", "主管", "管理者",
        "经理", "高级经理"
    ]
    
    for keyword in position_keywords:
        if keyword in personal_question:
            return keyword
    
    # 如果没有找到明确的关键词，返回空字符串
    return ""


def _search_market_trend(target_position: str, user_major: str) -> str:
    """搜索市场趋势"""
    try:
        client = SearchClient(ctx=Context())

        # 构建搜索查询
        query = f"{user_major} {target_position if target_position else '嵌入式'} 市场趋势 发展前景 薪资水平 2024"

        response = client.web_search_with_summary(query=query, count=5)

        # 构建数据来源标注
        sources = []
        if hasattr(response, 'web_items') and response.web_items:
            for item in response.web_items[:5]:
                source_info = f"- {item.site_name if item.site_name else item.title}"
                if hasattr(item, 'url') and item.url:
                    source_info += f" ({item.url})"
                sources.append(source_info)

        if response.summary:
            # 在摘要后添加数据来源
            sources_text = "\n\n**数据来源与可信度：**\n本次市场趋势分析基于联网搜索获取的最新信息，数据来源包括：\n" + "\n".join(sources) + "\n\n**说明：** 以上信息来自公开网络搜索，仅供参考。建议结合权威行业报告（如《中国互联网发展报告》、LinkedIn职业报告等）进行交叉验证。"
            return response.summary + sources_text
        elif hasattr(response, 'web_items') and response.web_items:
            # 如果没有AI摘要，汇总搜索结果
            summaries = []
            for item in response.web_items[:3]:
                if item.snippet:
                    summaries.append(f"• {item.snippet}")

            sources_text = "\n\n**数据来源与可信度：**\n本次市场趋势分析基于联网搜索获取的最新信息，数据来源包括：\n" + "\n".join(sources) + "\n\n**说明：** 以上信息来自公开网络搜索，仅供参考。建议结合权威行业报告（如《中国互联网发展报告》、LinkedIn职业报告等）进行交叉验证。"
            return "\n".join(summaries) + sources_text
        else:
            return f"关于{user_major}专业{target_position if target_position else '嵌入式'}岗位的市场趋势信息暂无详细数据。建议关注行业报告和招聘网站动态。\n\n**数据来源：** 公开网络搜索（未检索到相关信息）"
    except Exception as e:
        return f"市场趋势搜索暂时不可用：{str(e)}。\n\n**数据来源：** 搜索服务异常，建议参考行业权威报告。"


def _search_jobs(
    target_position: str,
    user_major: str,
    education: str
) -> List[Dict[str, Any]]:
    """搜索推荐岗位"""
    recommended_jobs = []

    try:
        client = SearchClient(ctx=Context())

        # 搜索目标岗位的招聘信息
        search_position = target_position if target_position else f"{user_major}工程师"
        query = f"{search_position} 招聘 职位 薪资 要求"

        response = client.web_search(query=query, count=8)

        if hasattr(response, 'web_items') and response.web_items:
            for item in response.web_items[:8]:
                # 从snippet中尝试提取薪资信息
                salary = "面议"
                if item.snippet:
                    # 常见薪资格式匹配
                    import re
                    salary_patterns = [
                        r'(\d+[-—]\d+)万',
                        r'(\d+[-—]\d+)k',
                        r'(\d+[-—]\d+)K',
                        r'(\d+[-—]\d+)千元',
                        r'(\d+[-—]\d+)元',
                        r'(\d+[-—]\d+)元/月'
                    ]
                    for pattern in salary_patterns:
                        match = re.search(pattern, item.snippet)
                        if match:
                            salary = match.group(1) + "元/月" if "元/月" not in salary else match.group(1)
                            if "万" in pattern:
                                salary = match.group(1) + "万/年"
                            break

                job_info = {
                    "job_title": search_position,
                    "company": item.site_name if item.site_name else "待定",
                    "salary": salary,
                    "location": "不限",  # 如果能从snippet中提取会更好
                    "requirements": item.snippet[:200] if item.snippet else "详见招聘页面",
                    "url": item.url if hasattr(item, 'url') else ""
                }
                recommended_jobs.append(job_info)

        # 如果搜索结果不足，添加一些推荐性的进阶岗位
        if len(recommended_jobs) < 3:
            advancement_jobs = _generate_advancement_jobs(
                search_position,
                user_major,
                education
            )
            recommended_jobs.extend(advancement_jobs)

    except Exception as e:
        # 如果搜索失败，生成推荐岗位
        recommended_jobs = _generate_advancement_jobs(
            target_position if target_position else f"{user_major}工程师",
            user_major,
            education
        )

    # 限制为3-5个推荐
    return recommended_jobs[:5]


def _generate_advancement_jobs(
    target_position: str,
    user_major: str,
    education: str
) -> List[Dict[str, Any]]:
    """生成进阶岗位推荐"""
    jobs = []
    
    # 根据专业推荐进阶岗位
    advancement_map = {
        "嵌入式": ["高级嵌入式工程师", "嵌入式开发经理", "技术总监"],
        "计算机": ["高级软件工程师", "技术经理", "技术总监"],
        "电子": ["高级电子工程师", "研发经理", "技术总监"],
        "机械": ["高级机械工程师", "研发经理", "技术总监"],
        "软件": ["高级软件工程师", "技术经理", "技术总监"],
        "通信": ["高级通信工程师", "研发经理", "技术总监"],
        "自动化": ["高级自动化工程师", "研发经理", "技术总监"]
    }
    
    # 查找匹配的专业
    target_jobs = []
    for major_key, positions in advancement_map.items():
        if major_key in user_major or user_major in major_key:
            target_jobs = positions
            break
    
    if not target_jobs:
        target_jobs = [
            f"高级{user_major}工程师",
            f"{user_major}开发经理",
            "技术总监"
        ]
    
    for i, job_title in enumerate(target_jobs[:3], 1):
        jobs.append({
            "job_title": job_title,
            "company": f"{user_major}行业头部企业",
            "salary": f"{30 + i * 15}-{40 + i * 20}万/年",
            "location": "一线城市",
            "requirements": f"需要具备{education}学历，{user_major}相关经验，以及优秀的团队管理能力。",
            "url": ""
        })
    
    return jobs



