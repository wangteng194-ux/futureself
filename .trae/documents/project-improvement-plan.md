# 项目完善计划（最终版）

## 已确认的决策

| 决策项    | 结论                  |
| ------ | ------------------- |
| LLM 推理 | Ollama 本地推理引擎       |
| 图像生成   | 完全本地化，开源模型          |
| 前端框架   | Vue3                |
| 实施顺序   | 先本地化改造，后前端开发        |
| 兼容性    | 不向后兼容，彻底移除 Coze SDK |

***

## 一、现状分析

当前项目存在以下核心依赖，全部需要移除：

| 依赖        | 当前方案                                                              | 移除目标                          |
| --------- | ----------------------------------------------------------------- | ----------------------------- |
| LLM 调用    | `coze_coding_dev_sdk.LLMClient` → 豆包云端API                         | → Ollama 本地推理                 |
| 联网搜索      | `coze_coding_dev_sdk.SearchClient`                                | → Tavily / SearXNG            |
| 生图模型      | `coze_coding_dev_sdk.ImageGenerationClient`                       | → Stable Diffusion WebUI 本地生图 |
| 对象存储      | `coze_coding_dev_sdk.s3.S3SyncStorage` + `coze_workload_identity` | → 本地文件系统 / MinIO              |
| 数据库       | PostgreSQL（通过 `coze_workload_identity` 获取连接串）                     | → PostgreSQL（直连）              |
| 运行时上下文    | `coze_coding_utils.runtime_ctx.Context`                           | → 自定义 `RunContext`            |
| 部署配置      | `.coze` 配置驱动                                                      | → `.env` + docker-compose     |
| 消息协议      | `coze_coding_utils` 中的消息格式                                        | → 自定义消息格式                     |
| OpenAI兼容层 | `coze_coding_utils` 中的handler                                     | → 自行实现或精简                     |
| 日志/追踪     | `cozeloop`                                                        | → 标准 logging                  |

需要移除的包：

* `coze-coding-dev-sdk`

* `coze-coding-utils`

* `coze-workload-identity`

* `cozeloop`

***

## 二、阶段 1 — 本地化改造（优先执行）

### 1.1 统一配置管理

**目标**：用 `pydantic-settings` + `.env` 替代所有 Coze 环境变量

**新建文件**：`src/config/settings.py`

配置项包括：

```
# LLM（Ollama）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=

# 图像生成（SD WebUI）
SD_WEBUI_URL=http://localhost:7860
SD_MODEL=sd-xl

# 搜索
SEARCH_PROVIDER=tavily          # tavily | searxng
TAVILY_API_KEY=
SEARXNG_URL=

# 存储
STORAGE_PROVIDER=local          # local | minio
STORAGE_LOCAL_PATH=./data/output
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=futureself

# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/futureself

# 服务
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

**新建文件**：`.env.example`

### 1.2 LLM 客户端 — Ollama 集成

**目标**：通过 Ollama 的 OpenAI 兼容 API 调用本地模型

**新建文件**：`src/clients/llm_client.py`

核心逻辑：

* 使用 `openai` 库（已存在于依赖中）连接 Ollama 的 OpenAI 兼容端点 `http://localhost:11434/v1`

* 支持 `chat.completions.create()` 调用

* 保持与现有节点相同的输入输出接口（messages 列表 → 响应文本）

* 支持 Jinja2 模板渲染（复用现有 `sp` / `up` 配置）

* 流式输出支持（`stream=True`）

Ollama 推荐模型：

| 用途   | 模型            | 说明           |
| ---- | ------------- | ------------ |
| 通用推理 | `qwen2.5:7b`  | 中等规模，平衡性能与速度 |
| 轻量快速 | `qwen2.5:3b`  | 适合评分等简单任务    |
| 长文本  | `qwen2.5:14b` | 适合报告生成       |

适配节点：

* `big_five_assessment_node.py` — 替换 `LLMClient` 为 `OllamaLLMClient`

* `loop_scoring_node.py` — 替换 `LLMClient`

* `single_pair_scoring_node.py` — 替换 `LLMClient`

* `cartoon_prompt_analysis_node.py` — 替换 `LLMClient`

* `report_generation_node.py` — 替换 `LLMClient`

### 1.3 图像生成客户端 — SD WebUI 集成

**目标**：通过 Stable Diffusion WebUI API 实现本地生图

**新建文件**：`src/clients/image_gen_client.py`

核心逻辑：

* 调用 SD WebUI 的 `/sdapi/v1/txt2img` 接口

* 传入英文提示词（复用现有 `image_prompt_en`）

* 返回生成图片的 base64 数据或本地文件路径

* 支持参数配置：采样器、步数、CFG scale、图片尺寸

适配节点：

* `cartoon_image_generation_node.py` — 替换 `ImageGenerationClient`

### 1.4 搜索客户端 — Tavily / SearXNG

**目标**：提供本地化搜索能力

**新建文件**：`src/clients/search_client.py`

两种实现：

* **Tavily**：调用 `https://api.tavily.com/search`，需要 API Key（免费额度）

* **SearXNG**：自建开源元搜索引擎，完全本地化，无需 API Key

核心接口：

```python
def search(query: str, count: int = 5) -> SearchResponse:
    """返回搜索结果列表，每项包含 title、url、snippet"""

def search_with_summary(query: str, count: int = 5) -> SearchResponse:
    """返回搜索结果 + AI 摘要"""
```

适配节点：

* `job_analysis_node.py` — 替换 `SearchClient`

### 1.5 存储客户端 — 本地文件系统

**目标**：替代 S3 云存储，支持本地文件存储

**新建文件**：`src/clients/storage_client.py`

两种实现：

* **LocalStorageClient**：文件存储到本地 `./data/output/` 目录，返回本地路径或静态文件 URL

* **MinIOStorageClient**：可选，MinIO 兼容 S3 API，用于需要对象存储的场景

核心接口：

```python
def upload_file(file_content: bytes, file_name: str, content_type: str) -> str:
    """上传文件，返回文件 URL"""
def generate_file_url(file_key: str, expire_time: int = 3600) -> str:
    """生成文件访问 URL"""
```

适配节点：

* `network_visualization_node.py` — 替换 `S3SyncStorage`

* `chart_generation_node.py` — 替换 `S3SyncStorage`

* `report_generation_node.py` — 替换 `S3SyncStorage`

### 1.6 运行时上下文 — 自定义 RunContext

**目标**：替代 `coze_coding_utils.runtime_ctx.Context`

**新建文件**：`src/context.py`

```python
class RunContext:
    run_id: str
    session_id: str
    method: str
    logid: str
```

适配节点：

* 所有节点函数的 `runtime: Runtime[Context]` 参数

* `main.py` 中的 `new_context()` 调用

### 1.7 主服务重构 — main.py

**目标**：移除所有 Coze SDK 依赖，保持核心功能

修改内容：

* 移除 `from coze_coding_utils.runtime_ctx.context import new_context, Context`

* 移除 `cozeloop.flush()` 调用

* 移除 `coze_coding_dev_sdk` 相关导入

* 替换消息协议为简化版（移除 `utils/messages/` 中的 Coze 依赖）

* 简化 OpenAI 兼容层

* 添加 CORS 中间件支持

* 添加静态文件服务（为前端构建产物和生成的图片/PDF 提供访问）

### 1.8 移除 Coze SDK 依赖

**需要移除/重写的文件**：

* `src/storage/s3/s3_storage.py` — 替换为 `src/clients/storage_client.py`

* `src/utils/messages/client.py` — 移除 Coze 消息格式

* `src/utils/messages/server.py` — 移除 Coze 消息格式

* `src/utils/openai/handler.py` — 移除 Coze 上下文依赖

* `src/utils/helper/agent_helper.py` — 移除 Coze 消息转换

* `src/utils/log/loop_trace.py` — 移除 cozeloop 依赖

* `src/storage/memory/memory_saver.py` — 移除 coze\_workload\_identity 依赖

* `src/storage/database/db.py` — 移除 coze\_workload\_identity 依赖

**需要从 pyproject.toml 移除的依赖**：

* `coze-coding-dev-sdk`

* `coze-coding-utils`

* `coze-workload-identity`

* `cozeloop`

**需要新增的依赖**：

* `pydantic-settings` — 配置管理

* `tavily-python` — Tavily 搜索（可选）

### 1.9 配置文件统一

* 修复 `cartoon_portrait_analysis_llm_cfg.json` → `cartoon_prompt_analysis_llm_cfg.json` 命名不一致

* LLM 配置中的 `model` 字段改为 Ollama 模型名（如 `qwen2.5:7b`）

* 配置读取路径改为相对项目根目录（移除 `COZE_WORKSPACE_PATH` 依赖）

***

## 三、阶段 2 — 前后端分离

### 2.1 后端 API 规范化

**目标**：为前端提供清晰的 RESTful API

| 方法   | 路径                                    | 说明             |
| ---- | ------------------------------------- | -------------- |
| POST | `/api/v1/sessions`                    | 创建会话           |
| POST | `/api/v1/sessions/{id}/run`           | 执行工作流（异步）      |
| GET  | `/api/v1/sessions/{id}/status`        | 查询执行状态         |
| GET  | `/api/v1/sessions/{id}/report`        | 获取报告（JSON）     |
| GET  | `/api/v1/sessions/{id}/report/pdf`    | 下载 PDF         |
| GET  | `/api/v1/sessions/{id}/images/{name}` | 获取生成的图片        |
| GET  | `/api/v1/representations`             | 获取可选表征列表       |
| GET  | `/api/v1/questionnaire`               | 获取大五人格问卷       |
| WS   | `/api/v1/sessions/{id}/stream`        | WebSocket 实时进度 |

### 2.2 前端项目搭建

**技术栈**：Vue3 + Vite + TypeScript + TailwindCSS + Pinia + Vue Router

**项目结构**：

```
frontend/
├── src/
│   ├── views/
│   │   ├── UserInfoView.vue        # 用户信息填写
│   │   ├── QuestionnaireView.vue   # 大五人格问卷
│   │   ├── RepresentationsView.vue # 表征选择
│   │   ├── QuestionsView.vue       # 个性化问题
│   │   ├── ProcessingView.vue      # 执行等待
│   │   └── ReportView.vue          # 报告展示
│   ├── components/
│   │   ├── StepIndicator.vue       # 步骤指示器
│   │   ├── RadarChart.vue          # 雷达图（ECharts）
│   │   ├── NetworkGraph.vue        # 网络图（ECharts/D3）
│   │   └── PdfViewer.vue           # PDF 预览
│   ├── stores/
│   │   └── session.ts              # 会话状态管理
│   ├── api/
│   │   └── client.ts               # API 客户端
│   ├── router/
│   │   └── index.ts                # 路由配置
│   └── App.vue
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

### 2.3 前端页面详情

**步骤1 - 用户信息页**：

* 姓名、性别、学历、专业、职业输入

* 表单校验

**步骤2 - 大五人格问卷页**：

* 40题五点量表（1-5分）

* 按5个维度分组展示

* 进度指示器

* 问卷说明

**步骤3 - 表征选择页**：

* 表征卡片网格展示

* 搜索/分类筛选

* 已选计数（≤25个限制）

* 表征说明 tooltip

**步骤4 - 个性化问题页**：

* 3个开放性文本框

* 字数提示

**步骤5 - 执行等待页**：

* 步骤进度条

* WebSocket 实时节点状态

* 预估耗时提示

**步骤6 - 报告展示页**：

* 卡通形象展示

* 大五人格雷达图（ECharts）

* 互补性/冲突性网络图

* 市场趋势与岗位推荐

* 学习推荐

* PDF 下载/预览

***

## 四、阶段 3 — 工程化增强

### 4.1 测试体系

| 类型     | 范围                   | 框架                         |
| ------ | -------------------- | -------------------------- |
| 单元测试   | 评分计算、配对生成、网络分析、PDF生成 | pytest                     |
| 集成测试   | 完整工作流（Mock LLM）      | pytest + pytest-asyncio    |
| API 测试 | HTTP 接口              | httpx / FastAPI TestClient |

### 4.2 容器化部署

**Dockerfile**（后端）：

* 基础镜像：`python:3.12-slim`

* 安装依赖、复制代码

* 暴露端口 5000

**docker-compose.yml**：

```yaml
services:
  backend:      # FastAPI 后端
  frontend:     # Nginx 托管前端
  postgres:     # PostgreSQL 数据库
  ollama:       # Ollama 推理引擎（需 GPU）
  sd-webui:     # Stable Diffusion WebUI（需 GPU）
  minio:        # MinIO 对象存储（可选）
```

### 4.3 数据库完善

* 定义 `Session`、`Report` 表结构

* 实现 CRUD 操作

* 支持历史报告查询

***

## 五、详细实施步骤

### 阶段 1：本地化改造（共 12 步）

| #  | 任务                                                        | 产出       |
| -- | --------------------------------------------------------- | -------- |
| 1  | 创建 `src/config/settings.py`，用 pydantic-settings 管理所有配置    | 配置统一管理   |
| 2  | 创建 `.env.example`，列出所有环境变量                                | 环境变量模板   |
| 3  | 创建 `src/clients/llm_client.py`，实现 Ollama LLM 客户端          | LLM 本地调用 |
| 4  | 创建 `src/clients/image_gen_client.py`，实现 SD WebUI 生图客户端    | 生图本地调用   |
| 5  | 创建 `src/clients/search_client.py`，实现 Tavily/SearXNG 搜索客户端 | 搜索本地调用   |
| 6  | 创建 `src/clients/storage_client.py`，实现本地文件存储客户端            | 存储本地化    |
| 7  | 创建 `src/context.py`，定义 RunContext                         | 上下文解耦    |
| 8  | 重构 `src/graphs/state.py`，移除 File 类型中的 S3 依赖               | 状态模型适配   |
| 9  | 适配所有节点（10个）使用新客户端                                         | 核心逻辑改造   |
| 10 | 重构 `src/main.py`，移除 Coze SDK 依赖                           | 主服务改造    |
| 11 | 清理 pyproject.toml / requirements.txt，移除 Coze 相关包          | 依赖清理     |
| 12 | 端到端验证：Ollama + SD WebUI + 本地存储完整流程                        | 功能验证     |

### 阶段 2：前后端分离（共 10 步）

| #  | 任务                                       | 产出    |
| -- | ---------------------------------------- | ----- |
| 1  | 后端：添加 RESTful API 路由（会话、报告、问卷）           | API 层 |
| 2  | 后端：添加 WebSocket 流式推送                     | 实时通信  |
| 3  | 后端：添加 CORS 和静态文件服务                       | 前后端联通 |
| 4  | 前端：初始化 Vue3 + Vite + TS + TailwindCSS 项目 | 前端骨架  |
| 5  | 前端：实现步骤指示器和路由框架                          | 导航流程  |
| 6  | 前端：实现用户信息填写页                             | 步骤1   |
| 7  | 前端：实现大五人格问卷页                             | 步骤2   |
| 8  | 前端：实现表征选择页                               | 步骤3   |
| 9  | 前端：实现个性化问题 + 执行等待页                       | 步骤4-5 |
| 10 | 前端：实现报告展示页（图表 + PDF下载）                   | 步骤6   |

### 阶段 3：工程化增强（共 6 步）

| # | 任务                    | 产出    |
| - | --------------------- | ----- |
| 1 | 编写核心节点单元测试            | 测试覆盖  |
| 2 | 编写工作流集成测试（Mock LLM）   | 端到端测试 |
| 3 | 编写后端 Dockerfile       | 容器化   |
| 4 | 编写 docker-compose.yml | 一键部署  |
| 5 | 完善数据库模型和 CRUD         | 数据持久化 |
| 6 | 更新 README.md          | 文档完善  |

