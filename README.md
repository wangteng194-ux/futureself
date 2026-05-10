# 未来自我画像职业规划工作流

基于用户基本信息、大五人格评估、未来自我表征网络分析、市场趋势搜索，通过多智能体协作生成个性化、具有说服力的未来自我画像职业规划报告。

## 功能特性

- **大五人格评估**：基于 CBF-PI-B 量表（40题）评估用户五大特质维度
- **未来自我表征分析**：用户选择表征，构建表征网络，计算互补性/冲突性评分
- **市场趋势搜索**：联网获取行业趋势和岗位推荐
- **卡通形象生成**：AI 生成个性化未来自我画像
- **完整报告生成**：Markdown + PDF 双格式输出

## 技术栈

- **框架**：LangGraph、FastAPI
- **语言模型**：Doubao Seed（豆包大模型）
- **生图模型**：Doubao Dream（文生图）
- **存储**：S3 兼容对象存储
- **PDF 生成**：ReportLab

## 目录结构

```
e:\futureself\
├── src/
│   ├── graphs/
│   │   ├── nodes/          # 工作流节点实现
│   │   │   ├── big_five_assessment_node.py      # 大五人格评估
│   │   │   ├── representation_pairing_node.py   # 表征配对
│   │   │   ├── loop_scoring_node.py            # 循环评分（批次处理）
│   │   │   ├── network_analysis_node.py        # 网络分析
│   │   │   ├── network_visualization_node.py   # 网络可视化
│   │   │   ├── job_analysis_node.py            # 岗位分析
│   │   │   ├── cartoon_prompt_analysis_node.py # 卡通提示词分析
│   │   │   ├── cartoon_image_generation_node.py# 卡通形象生成
│   │   │   ├── chart_generation_node.py        # 图表生成
│   │   │   └── report_generation_node.py       # 报告生成
│   │   ├── graph.py           # 主工作流定义
│   │   ├── loop_graph.py      # 评分循环子图
│   │   └── state.py           # 状态定义
│   ├── storage/
│   │   ├── s3/                # S3 存储集成
│   │   └── database/          # 数据库操作
│   ├── utils/
│   │   ├── error/             # 错误分类与处理
│   │   ├── log/               # 日志系统
│   │   ├── messages/           # 消息协议
│   │   ├── openai/             # OpenAI 兼容层
│   │   └── helper/             # 辅助工具
│   └── main.py                # FastAPI 服务入口
├── config/                     # LLM 配置文件
│   ├── big_five_assessment_llm_cfg.json
│   ├── scoring_llm_cfg.json
│   ├── cartoon_prompt_analysis_llm_cfg.json
│   └── report_generation_llm_cfg.json
├── scripts/                    # 运行脚本
│   ├── local_run.sh
│   ├── http_run.sh
│   └── setup.sh
└── assets/                     # 静态资源
```

## 工作流程

```
用户输入
    │
    ▼
┌─────────────────────┐
│ 1. 大五人格评估      │ ◄── 40题问卷（CBF-PI-B量表）
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 2. 表征配对          │ ◄── 用户选择的表征（≤25个）
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 3. 循环评分          │ ◄── 批次处理（每15对调用一次LLM）
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 4. 网络分析          │ ◄── 互补性/冲突性评分
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 5. 网络可视化        │ ◄── Gephi风格网络图
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 6. 岗位分析          │ ◄── 市场趋势 + 岗位推荐
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 7. 卡通形象生成      │ ◄── 提示词分析 + 生图模型
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 8. 报告生成          │ ◄── Markdown + PDF
└─────────┴───────────┘
```

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_name | string | ✓ | 用户姓名 |
| user_gender | string | ✓ | 用户性别 |
| user_education | string | ✓ | 用户学历 |
| user_major | string | | 用户专业 |
| selected_representations | string[] | ✓ | 表征列表（≤25个） |
| personal_question_1 | string | ✓ | 职业发展问题 |
| personal_question_2 | string | ✓ | 知识学习问题 |
| personal_question_3 | string | ✓ | 生活愿景问题 |
| big_five_answers | object | ✓ | 大五人格问卷答案 |

### big_five_answers 格式

```json
{
  "N1-N8": [3, 4, 2, 5, 3, 4, 2, 3],  // 神经质
  "C1-C8": [4, 5, 4, 3, 5, 4, 5, 4],  // 严谨性
  "A1-A8": [3, 4, 4, 3, 3, 4, 3, 4],  // 宜人性
  "O1-O8": [4, 3, 4, 5, 4, 3, 4, 5],  // 开放性
  "E1-E8": [3, 4, 3, 4, 3, 4, 3, 4]   // 外向性
}
```

## 输出结果

| 字段 | 类型 | 说明 |
|------|------|------|
| final_report | string | Markdown 格式报告 |
| final_report_pdf | File | PDF 文件 |
| network_graph | File | 互补性网络图 |
| conflict_graph | File | 冲突性网络图 |
| radar_chart | File | 能力雷达图 |
| cartoon_portrait | File | 卡通画像 |
| complementarity_score | float | 互补性评分 |
| conflict_score | float | 冲突性评分 |

## API 接口

### HTTP 服务

```bash
# 启动服务
bash scripts/http_run.sh -m http -p 5000

# 同步执行
POST /run
Content-Type: application/json

# 流式执行
POST /stream_run

# 取消执行
POST /cancel/{run_id}

# 单节点执行
POST /node_run/{node_id}

# 健康检查
GET /health

# OpenAI 兼容接口
POST /v1/chat/completions
```

### 本地运行

```bash
# 完整流程
bash scripts/local_run.sh -m flow

# 单节点运行
bash scripts/local_run.sh -m node -n node_name
```

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| COZE_WORKSPACE_PATH | 工作空间路径 | ✓ |
| COZE_BUCKET_ENDPOINT_URL | S3 端点 | ✓ |
| COZE_BUCKET_NAME | 存储桶名 | ✓ |
| COZE_BUCKET_ACCESS_KEY | 访问密钥 | |
| COZE_BUCKET_SECRET_KEY | 秘钥 | |

## 安装依赖

```bash
# 使用 uv 安装
uv sync

# 或使用 pip
pip install -r requirements.txt
```

## 配置说明

LLM 配置文件位于 `config/` 目录，使用 JSON 格式：

```json
{
  "config": {
    "model": "doubao-seed-1-8-251228",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_completion_tokens": 2000
  },
  "sp": "系统提示词",
  "up": "用户提示词模板（Jinja2格式）"
}
```
