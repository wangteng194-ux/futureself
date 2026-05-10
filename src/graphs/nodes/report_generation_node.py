"""
报告生成节点
生成完整的未来自我画像职业规划报告（Markdown + PDF）
"""

import os
import json
import logging
import re
from datetime import datetime
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from langchain_core.messages import HumanMessage, SystemMessage
from coze_coding_dev_sdk import LLMClient
from coze_coding_dev_sdk.s3 import S3SyncStorage
from utils.file.file import File
from graphs.state import ReportGenerationInput, ReportGenerationOutput

# PDF generation imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from markdown import markdown
from bs4 import BeautifulSoup


def report_generation_node(
    state: ReportGenerationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ReportGenerationOutput:
    """
    title: 报告生成
    desc: 基于所有分析结果，生成完整的未来自我画像职业规划报告，并输出PDF格式
    integrations: 大语言模型、文档生成
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
        "user_name": state.user_name,
        "user_gender": state.user_gender,
        "user_education": state.user_education,
        "user_major": state.user_major,
        "selected_representations": state.selected_representations,
        "personal_question_1": state.personal_question_1,
        "personal_question_2": state.personal_question_2,
        "personal_question_3": state.personal_question_3,
        "complementarity_score": state.complementarity_score,
        "conflict_score": state.conflict_score,
        "correlation_scores": state.correlation_scores,
        "network_analysis_interpretation": state.network_analysis_interpretation,
        "market_trend": state.market_trend,
        "recommended_jobs": state.recommended_jobs,
        "job_fit_score": state.job_fit_score,
        "skill_gap_analysis": state.skill_gap_analysis,
        "network_graph": state.network_graph,
        "conflict_graph": state.conflict_graph,
        "radar_chart": state.radar_chart,
        "bar_chart": state.bar_chart,
        "cartoon_portrait": state.cartoon_portrait,
        "big_five_scores": state.big_five_scores
    })

    # 调用大模型生成报告
    client = LLMClient(ctx=ctx)

    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt_content)
    ]

    resp = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-pro-32k"),
        temperature=llm_config.get("temperature", 0.7),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 4000),
        thinking=llm_config.get("thinking", "disabled")
    )

    # 安全提取响应内容
    if isinstance(resp.content, str):
        final_report = resp.content
    elif isinstance(resp.content, list):
        # 如果是列表，尝试提取文本
        text_parts = []
        for item in resp.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        final_report = " ".join(text_parts)
    else:
        final_report = str(resp.content)

    # 生成 PDF 文件
    pdf_url = _generate_pdf_from_markdown(final_report, state.user_name, ctx)

    # 创建 File 对象
    report_pdf = File(
        url=pdf_url,
        file_type="document"
    )

    return ReportGenerationOutput(
        final_report=final_report,
        final_report_pdf=report_pdf
    )


def _generate_pdf_from_markdown(markdown_content: str, user_name: str, ctx: Context) -> str:
    """
    将 Markdown 内容转换为 PDF 并上传到对象存储

    Args:
        markdown_content: Markdown 格式的报告内容
        user_name: 用户姓名（用于生成文件名）
        ctx: 运行时上下文

    Returns:
        PDF 文件的下载 URL
    """
    # 清理文件名，只保留拼音或英文
    safe_name = "".join(c for c in user_name if c.isalnum() or c in ('_', '-'))
    if not safe_name:
        safe_name = "report"

    # 生成 PDF 文件路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"future_self_portrait_{safe_name}_{timestamp}.pdf"
    pdf_path = f"/tmp/{pdf_filename}"

    try:
        # 使用 reportlab 生成 PDF
        _create_pdf_with_reportlab(markdown_content, pdf_path)
        logging.getLogger(__name__).info(f"PDF generated successfully at {pdf_path}")

        # 上传到对象存储
        storage = S3SyncStorage(
            endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
            access_key=os.getenv("COZE_BUCKET_ACCESS_KEY", ""),
            secret_key=os.getenv("COZE_BUCKET_SECRET_KEY", ""),
            bucket_name=os.getenv("COZE_BUCKET_NAME"),
            region="cn-beijing",
        )

        # 读取 PDF 文件内容并上传
        with open(pdf_path, 'rb') as f:
            file_content = f.read()

        file_key = storage.upload_file(
            file_content=file_content,
            file_name=pdf_filename,
            content_type="application/pdf"
        )

        # 生成签名 URL
        s3_url = storage.generate_presigned_url(key=file_key, expire_time=86400)
        logging.getLogger(__name__).info(f"PDF uploaded to {s3_url}")
        return s3_url
    except Exception as e:
        logging.getLogger(__name__).error(f"PDF generation or upload failed: {e}", exc_info=True)
        return ""


def _create_pdf_with_reportlab(markdown_content: str, output_path: str):
    """
    使用 reportlab 将 Markdown 内容转换为 PDF

    Args:
        markdown_content: Markdown 格式的报告内容
        output_path: 输出 PDF 文件路径
    """
    # 将 Markdown 转换为 HTML（禁用图片扩展以避免格式问题）
    html_content = markdown(
        markdown_content,
        extensions=[],
        output_format='html'
    )

    # 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 创建 PDF 文档
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    # 创建样式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#2c5282'),
        spaceAfter=12,
        spaceBefore=20
    )
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=8,
        spaceBefore=12
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        spaceAfter=12
    )
    # 添加链接样式
    link_style = ParagraphStyle(
        'CustomLink',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=12
    )

    # 构建内容
    story = []

    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'img', 'table', 'br']):
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = element.get_text().strip()
            if text:
                if element.name == 'h1':
                    story.append(Paragraph(text, title_style))
                elif element.name == 'h2':
                    story.append(Paragraph(text, heading_style))
                else:
                    story.append(Paragraph(text, subheading_style))
                story.append(Spacer(1, 6))
        elif element.name == 'p':
            # 移除图片标签，只保留文本
            for img in element.find_all('img'):
                img.decompose()
            text = element.get_text().strip()
            if text:
                # 处理加粗和斜体文本
                html_text = str(element)
                # 移除所有 HTML 标签，只保留文本
                from html import unescape
                clean_text = unescape(re.sub(r'<[^>]+>', '', html_text))
                story.append(Paragraph(clean_text, body_style))
                story.append(Spacer(1, 6))
        elif element.name == 'img':
            # 不嵌入图片，而是显示为链接文本格式
            src = element.get('src', '')
            if src:
                # 将图片显示为超链接格式
                link_text = f"<a href='{src}'>{src}</a>"
                story.append(Paragraph(link_text, link_style))
                story.append(Spacer(1, 12))
        elif element.name == 'ul':
            for li in element.find_all('li', recursive=False):
                text = li.get_text().strip()
                if text:
                    story.append(Paragraph(f"• {text}", body_style))
                    story.append(Spacer(1, 3))
            story.append(Spacer(1, 6))
        elif element.name == 'ol':
            for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                text = li.get_text().strip()
                if text:
                    story.append(Paragraph(f"{idx}. {text}", body_style))
                    story.append(Spacer(1, 3))
            story.append(Spacer(1, 6))
        elif element.name == 'table':
            # 处理表格
            rows_data = []
            for row in element.find_all('tr'):
                cells = []
                for cell in row.find_all(['td', 'th']):
                    cells.append(cell.get_text().strip())
                if cells:
                    rows_data.append(cells)
            if rows_data:
                table = Table(rows_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
        elif element.name == 'hr':
            story.append(Spacer(1, 12))

    # 生成 PDF
    doc.build(story)
