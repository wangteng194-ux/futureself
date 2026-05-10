"""
网络可视化节点
生成 Gephi 风格的表征网络结构图
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Dict
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk.s3 import S3SyncStorage
from graphs.state import NetworkVisualizationInput, NetworkVisualizationOutput
from utils.file.file import File


def network_visualization_node(
    state: NetworkVisualizationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> NetworkVisualizationOutput:
    """
    title: 网络可视化
    desc: 生成 Gephi 风格的表征网络结构图，分别展示互补性和冲突性
    integrations: 无
    """
    ctx = runtime.context

    correlation_scores = state.correlation_scores
    representations = state.selected_representations

    # 设置matplotlib使用中文字体
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建两个图：互补性图和冲突性图
    G_complement = nx.Graph()
    G_conflict = nx.Graph()

    # 添加节点
    for rep in representations:
        G_complement.add_node(rep)
        G_conflict.add_node(rep)

    # 添加边，根据相关性分数分类
    for score_data in correlation_scores:
        rep1 = score_data.get("rep1", "")
        rep2 = score_data.get("rep2", "")
        correlation = score_data.get("correlation_score", 0)

        if rep1 and rep2:
            if correlation > 0:
                # 正相关（互补性）
                G_complement.add_edge(
                    rep1,
                    rep2,
                    weight=correlation,
                    correlation=correlation
                )
            elif correlation < 0:
                # 负相关（冲突性）
                G_conflict.add_edge(
                    rep1,
                    rep2,
                    weight=correlation,
                    correlation=correlation
                )

    # 生成两个 Gephi 风格图表
    complement_graph_file = _generate_gephi_graph(
        G_complement,
        "表征互补性网络图",
        "#4CAF50",  # 绿色
        representations,
        ctx
    )

    conflict_graph_file = _generate_gephi_graph(
        G_conflict,
        "表征冲突性网络图",
        "#F44336",  # 红色
        representations,
        ctx
    )

    # 生成标签映射
    label_mapping = [{"label": rep, "representation": rep} for rep in representations]

    return NetworkVisualizationOutput(
        network_graph=complement_graph_file,
        label_mapping=label_mapping,
        conflict_graph=conflict_graph_file
    )


def _generate_gephi_graph(G, title, edge_color, representations, ctx):
    """
    生成 Gephi 风格的网络图
    """
    # 创建图形，设置白色背景
    fig, ax = plt.subplots(figsize=(18, 16), facecolor='white')
    ax.set_facecolor('white')

    # 如果没有边，创建简单布局
    if G.number_of_edges() == 0:
        pos = nx.circular_layout(G, scale=1.0)
    else:
        # 使用 Gephi 风格的力导向布局（Force-directed layout）
        # k 控制节点间距，iterations 控制迭代次数
        pos = nx.spring_layout(
            G,
            k=2.5,
            iterations=100,
            seed=42,
            weight='weight'
        )

    # 计算节点大小（固定大小，适中）
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees and max(degrees.values()) > 0 else 1
    node_sizes = [250 + (degrees.get(node, 0) / max_degree) * 150 for node in G.nodes()]

    # 绘制节点（黑色圆点）
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=node_sizes,
        node_color='black',
        edgecolors='black',
        linewidths=0,
        alpha=1.0,
        ax=ax
    )

    # 绘制节点标签（带深黑色文本框，放在节点附近）
    for node, (x, y) in pos.items():
        # 计算标签偏移位置，避免遮挡连线
        # 将标签放在节点右上方
        offset_x = 0.08
        offset_y = 0.08
        label_x = x + offset_x
        label_y = y + offset_y

        # 绘制带黑色边框的白色文本框，黑色加粗字体
        ax.text(
            label_x,
            label_y,
            node,
            fontsize=16,
            fontweight='bold',
            fontfamily='sans-serif',
            color='black',
            bbox=dict(
                facecolor='white',
                edgecolor='black',
                boxstyle='round,pad=0.4',
                alpha=1.0,
                linewidth=2
            ),
            ha='center',
            va='center',
            zorder=10  # 确保标签在连线上方
        )

    # 绘制边
    for u, v, data in G.edges(data=True):
        correlation = data.get('correlation', 0)
        abs_corr = abs(correlation)

        # 根据相关性强度设置线宽
        # 实线表示强相关（>1），虚线表示弱相关（≤1）
        if abs_corr > 1:
            width = 2.5 + abs_corr * 0.5  # 2.5 - 4.5
            alpha = 0.8
            linestyle = '-'
        else:
            width = 1.5 + abs_corr * 0.5  # 1.5 - 2.0
            alpha = 0.5
            linestyle = '--'

        # 绘制边（不显示数值）
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=[(u, v)],
            width=width,
            edge_color=edge_color,
            style=linestyle,
            alpha=alpha,
            ax=ax
        )

    # 添加标题
    ax.set_title(
        title,
        fontsize=22,
        fontweight='bold',
        pad=30,
        color='#333333'
    )

    # 移除坐标轴
    ax.set_axis_off()

    # 调整边距
    plt.tight_layout()

    # 保存图片（限制 dpi 和尺寸避免过大）
    temp_dir = "/tmp"
    if "互补性" in title:
        filename = "complementarity_network.png"
    else:
        filename = "conflict_network.png"

    output_path = os.path.join(temp_dir, filename)
    # 使用 dpi=150 控制图片尺寸，移除 bbox_inches='tight' 避免尺寸异常
    plt.savefig(output_path, dpi=150, facecolor='white', edgecolor='none', pad_inches=0.5)
    plt.close()

    # 上传到对象存储
    try:
        storage = S3SyncStorage(
            endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
            access_key="",
            secret_key="",
            bucket_name=os.getenv("COZE_BUCKET_NAME"),
            region="cn-beijing",
        )
        
        # 读取文件内容并上传
        with open(output_path, 'rb') as f:
            file_content = f.read()
        
        file_key = storage.upload_file(
            file_content=file_content,
            file_name=filename,
            content_type="image/png"
        )
        
        # 生成签名URL
        file_url = storage.generate_presigned_url(key=file_key, expire_time=3600)
        graph_file = File(url=file_url, file_type="image")
    except Exception as e:
        print(f"对象存储上传失败: {str(e)}")
        # 如果上传失败，返回本地路径
        graph_file = File(url=output_path, file_type="image")

    return graph_file
