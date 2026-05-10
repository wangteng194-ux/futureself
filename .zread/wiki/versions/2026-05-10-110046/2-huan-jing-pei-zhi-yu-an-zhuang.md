本页面将指导您完成 FutureSelf 项目的开发环境配置和依赖安装。按照以下步骤操作，即可快速搭建完整的开发环境。

## 系统要求

在开始安装之前，请确保您的开发环境满足以下最低要求：

| 环境要素 | 最低版本要求 | 说明 |
|---------|-------------|------|
| Python | 3.12+ | 项目使用 Python 3.12 新特性，不兼容旧版本 |
| 操作系统 | Windows 10+/macOS 11+/Linux | 跨平台兼容 |
| 内存 | 4GB+ | 推荐 8GB 以上以获得更好的开发体验 |
| 磁盘空间 | 2GB+ | 用于存储依赖包和生成的资源文件 |

Sources: [pyproject.toml](pyproject.toml#L3)

## 依赖管理方案

项目采用**双模式依赖管理**策略，兼顾现代开发效率与旧环境兼容性：

```mermaid
flowchart TD
    A[开始安装] --> B{检查 uv 命令?}
    B -->|是| C{检查 pyproject.toml?}
    C -->|是| D{部署模式?}
    D -->|是| E[uv export + uv pip install --target]
    D -->|否| F[uv sync 到 .venv]
    B -->|否| G[回退到 pip 模式]
    C -->|否| G
    G --> H[pip install -r requirements.txt]
    E --> I[安装完成]
    F --> I
    H --> I
```

**推荐使用 uv**：这是一个高性能的 Python 包管理器，安装速度比传统 pip 快 10-100 倍。项目已配置阿里云 PyPI 镜像源，国内访问速度更快。

Sources: [scripts/setup.sh](scripts/setup.sh#L8-L35)

## 安装步骤

### 第一步：克隆项目

```bash
git clone <repository-url>
cd futureself
```

### 第二步：创建虚拟环境（推荐）

#### 方式一：使用 uv（推荐）

如果您已安装 uv，项目会自动创建并管理虚拟环境：

```bash
# 安装 uv（如未安装）
pip install uv

# uv 会在执行时自动创建 .venv 虚拟环境
```

#### 方式二：手动创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

Sources: [.gitignore](.gitignore#L8)

### 第三步：安装依赖

#### Windows 环境安装

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### macOS/Linux 环境安装

```bash
# 使用提供的 setup 脚本
bash scripts/setup.sh
```

setup 脚本会自动检测可用的包管理器并执行相应的安装操作，支持以下两种模式：

| 模式 | 触发条件 | 安装目标 |
|------|---------|---------|
| Devbox 模式 | 未设置 PIP_TARGET 环境变量 | 安装到本地 .venv 虚拟环境 |
| 部署模式 | 设置了 PIP_TARGET 环境变量 | 安装到指定目录，用于容器部署 |

Sources: [scripts/setup.sh](scripts/setup.sh#L12-L33)

## 核心依赖说明

项目包含 150+ 个依赖包，主要分为以下几个核心类别：

| 类别 | 代表库 | 用途 |
|-----|-------|------|
| **AI 框架** | LangChain, LangGraph, LangSmith | 构建智能 Agent 和工作流编排 |
| **LLM 集成** | OpenAI, langchain-openai | 大语言模型 API 调用 |
| **Web 服务** | FastAPI, Uvicorn, HTTPX | HTTP 服务和网络请求 |
| **数据处理** | Pandas, NumPy, NetworkX | 数据分析和网络构建 |
| **可视化** | Matplotlib, Pillow, OpenCV | 图表生成和图像处理 |
| **存储系统** | SQLAlchemy, Supabase, Boto3 | 数据库和对象存储 |
| **文档生成** | ReportLab, python-pptx, python-docx | 生成报告文档 |
| **开发工具** | Pydantic, python-dotenv | 数据验证和环境管理 |

Sources: [pyproject.toml](pyproject.toml#L4-L168)

## 环境变量配置

项目使用环境变量管理敏感配置和运行参数。

### 本地开发环境

在项目根目录创建 `.env` 文件，配置必要的环境变量：

```env
# OpenAI 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 数据库配置（可选）
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# S3 存储配置（可选）
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
```

### Coze 平台环境

在 Coze 开发环境中，环境变量通过 `coze_workload_identity` 服务自动获取。使用 `load_env.py` 脚本加载环境变量：

```bash
# Linux/macOS
eval $(python scripts/load_env.py)

# Windows PowerShell
# 请手动设置环境变量或使用 .env 文件
```

Sources: [scripts/load_env.py](scripts/load_env.py#L1-L36)

## 目录结构说明

安装完成后，您的工作目录应包含以下关键目录：

```mermaid
graph TD
    Root[futureself/] --> src[src/]
    Root --> config[config/]
    Root --> scripts[scripts/]
    Root --> assets[assets/]
    Root --> venv[.venv/]
    Root --> pyproject[pyproject.toml]
    Root --> requirements[requirements.txt]
    Root --> dotenv[.env]
    
    src --> agents[agents/ 智能体]
    src --> graphs[graphs/ 工作流]
    src --> storage[storage/ 存储]
    src --> tools[tools/ 工具库]
    src --> utils[utils/ 工具函数]
    
    config --> llm[LLM 配置文件]
    scripts --> setup[setup.sh]
    scripts --> run[local_run.sh]
    scripts --> env[load_env.py]
    assets --> images[生成的图片]
    assets --> reports[生成的报告]
    venv --> python[Python 虚拟环境]
```

Sources: [pyproject.toml](pyproject.toml#L1-L171)

## 验证安装

完成安装后，执行以下命令验证环境配置是否正确：

```bash
# 检查 Python 版本
python --version
# 应该显示 Python 3.12.x 或更高

# 检查主要依赖是否安装成功
python -c "import langgraph, langchain, fastapi; print('核心依赖安装成功！')"

# 查看项目帮助信息
python src/main.py --help
```

如果所有命令都能正常执行且没有报错，说明您的环境配置已完成。

## 常见问题

### Q: 安装时出现网络错误怎么办？

**A**: 项目已配置阿里云 PyPI 镜像源。如仍有问题，可手动设置镜像：

```bash
# 使用 uv 时自动使用配置的镜像
uv sync

# 或手动指定镜像源
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### Q: Windows 下虚拟环境无法激活？

**A**: 请以管理员身份运行 PowerShell，执行：

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新激活虚拟环境。

### Q: 某些依赖安装失败（如 psycopg2）？

**A**: 部分二进制包需要编译环境。建议：
1. 更新 pip 到最新版本：`pip install --upgrade pip`
2. Windows 用户安装 [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/downloads/)
3. 或使用预编译的二进制包：`pip install psycopg2-binary`

Sources: [requirements.txt](requirements.txt#L58-L60)

## 后续步骤

环境配置完成后，建议继续阅读：

- [本地运行流程](3-ben-di-yun-xing-liu-cheng) - 了解如何在本地运行工作流
- [输入参数说明](5-shu-ru-can-shu-shuo-ming) - 掌握程序的输入参数配置
- [项目结构规范](24-xiang-mu-jie-gou-gui-fan) - 深入了解项目的代码组织