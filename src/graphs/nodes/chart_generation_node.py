"""
图表生成节点
生成表征能力雷达图
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk.s3 import S3SyncStorage
from graphs.state import ChartGenerationInput, ChartGenerationOutput
from utils.file.file import File


def chart_generation_node(
    state: ChartGenerationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ChartGenerationOutput:
    """
    title: 图表生成
    desc: 生成表征能力雷达图
    integrations: 无
    """
    ctx = runtime.context

    # 设置matplotlib使用中文字体
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 生成雷达图
    radar_chart_file = _generate_radar_chart(
        state.complementarity_score,
        state.conflict_score,
        state.selected_representations,
        state.correlation_scores
    )

    return ChartGenerationOutput(
        radar_chart=radar_chart_file
    )


def _generate_radar_chart(
    complementarity_score: float,
    conflict_score: float,
    representations: List[str],
    correlation_scores: List[Dict[str, Any]]
) -> File:
    """生成表征能力雷达图"""

    # 定义雷达图的维度
    categories = [
        '互补性',
        '冲突性（反）',
        '表征丰富度',
        '平衡性'
    ]

    # 计算各项指标（归一化到0-100）
    # 互补性评分：原始是0-2，转换到0-100
    complementarity_normalized = min(100, max(0, (complementarity_score / 2.0) * 100))

    # 冲突性评分：原始是0-2，转换到0-100，但这里用反向（冲突越低越好）
    conflict_normalized = min(100, max(0, (1.0 - (conflict_score / 2.0)) * 100))

    # 表征丰富度：根据表征数量，假设15个为满分
    richness_normalized = min(100, max(0, (len(representations) / 15.0) * 100))

    # 平衡性：基于互补性和冲突性的平衡程度
    if complementarity_score + conflict_score > 0:
        balance_normalized = min(100, max(0, 100 - abs(complementarity_score - conflict_score) / (complementarity_score + conflict_score) * 100))
    else:
        balance_normalized = 50.0

    values = [
        complementarity_normalized,
        conflict_normalized,
        richness_normalized,
        balance_normalized
    ]

    # 闭合雷达图
    values_closed = values + values[:1]
    categories_closed = categories + categories[:1]

    # 创建雷达图
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#F8F9FA')

    # 设置角度
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles_closed = angles + angles[:1]

    # 绘制雷达图
    ax.plot(angles_closed, values_closed, 'o-', linewidth=2, color='#2196F3', label='当前能力评估')
    ax.fill(angles_closed, values_closed, alpha=0.25, color='#2196F3')

    # 添加参考线（优秀水平）
    reference_values = [85] * len(categories)
    reference_values_closed = reference_values + reference_values[:1]
    ax.plot(angles_closed, reference_values_closed, '--', linewidth=1, color='#4CAF50', label='优秀水平参考', alpha=0.7)

    # 设置标签
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, size=11, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=9)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.spines['polar'].set_visible(False)

    # 添加标题
    ax.set_title('表征能力评估雷达图', size=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

    # 添加数值标注
    for angle, value, category in zip(angles, values, categories):
        ax.text(angle, value + 5, f'{value:.0f}', ha='center', va='center', fontsize=9, fontweight='bold')

    # 保存图片
    temp_dir = "/tmp"
    output_path = os.path.join(temp_dir, "ability_radar_chart.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()

    # 上传到对象存储
    try:
        storage = S3SyncStorage(
            endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
            access_key=os.getenv("COZE_BUCKET_ACCESS_KEY", ""),
            secret_key=os.getenv("COZE_BUCKET_SECRET_KEY", ""),
            bucket_name=os.getenv("COZE_BUCKET_NAME"),
            region="cn-beijing",
        )
        
        # 读取文件内容并上传
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        file_key = storage.upload_file(
            file_content=file_content,
            file_name="ability_radar_chart.png",
            content_type="image/png"
        )
        
        # 生成签名URL
        s3_url = storage.generate_presigned_url(key=file_key, expire_time=3600)
        return File(url=s3_url, file_type="image")
    except Exception as e:
        print(f"对象存储上传失败: {str(e)}")
        # 如果上传失败，返回本地路径
        return File(url=output_path, file_type="image")
