# 项目概述
- **名称**: 未来自我画像职业规划工作流
- **功能**: 基于用户基本信息、大五人格评估、未来自我表征网络分析、市场趋势搜索，通过多智能体协作生成个性化、具有说服力的未来自我画像职业规划报告

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| big_five_assessment | `graphs/nodes/big_five_assessment_node.py` | agent | 大五人格评估（基于CBF-PI-B量表，已正向化处理） | - | `config/big_five_assessment_llm_cfg.json` |
| representation_pairing | `graphs/nodes/representation_pairing_node.py` | task | 表征配对 | - | - |
| loop_scoring | `graphs/nodes/loop_scoring_node.py` | agent | 循环评分（批次处理，每15组调用一次大模型） | - | `config/scoring_llm_cfg.json` |
| network_analysis | `graphs/nodes/network_analysis_node.py` | task | 网络分析（计算互补性、冲突性，生成解读） | - | - |
| network_visualization | `graphs/nodes/network_visualization_node.py` | task | Gephi风格网络可视化（仅节点和连线） | - | - |
| job_analysis | `graphs/nodes/job_analysis_node.py` | task | 岗位分析（市场趋势、岗位推荐） | - | - |
| cartoon_prompt_analysis | `graphs/nodes/cartoon_prompt_analysis_node.py` | agent | 卡通形象提示词分析 | - | `config/cartoon_prompt_analysis_llm_cfg.json` |
| cartoon_image_generation | `graphs/nodes/cartoon_image_generation_node.py` | task | 卡通形象生成 | - | - |
| chart_generation | `graphs/nodes/chart_generation_node.py` | task | 图表生成（雷达图） | - | - |
| report_generation | `graphs/nodes/report_generation_node.py` | agent | 整合报告生成（支持PDF输出） | - | `config/report_generation_llm_cfg.json` |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
无（原循环评分子图已改为普通循环实现）

## 集成使用
- 节点`big_five_assessment`使用大语言模型集成（integration-doubao-seed）
- 节点`loop_scoring`使用大语言模型集成（integration-doubao-seed）
- 节点`job_analysis`使用联网搜索集成（integration-agent-web-search）
- 节点`cartoon_prompt_analysis`使用大语言模型集成（integration-doubao-seed）
- 节点`cartoon_image_generation`使用生图大模型集成（integration-doubao-seedream）
- 节点`report_generation`使用大语言模型集成（integration-doubao-seed）和reportlab库生成PDF
- 节点`network_visualization`使用对象存储集成（integration-s3-storage）
- 节点`chart_generation`使用对象存储集成（integration-s3-storage）

## 工作流程
工作流分为5个主要步骤，最终由报告生成节点整合所有内容：

### 第1步：大五人格评估（前置）
- **big_five_assessment**: 基于五点量表评估用户大五人格特质（数据已正向化处理）
  - 评估外向性、神经质、严谨性、开放性、宜人性五个维度（1-5分制）
  - 根据评分划分等级（较低/中等/较高）
  - 仅输出人格特征分析，不提供职业建议

### 第2步：未来自我网络分析（整合4个步骤）
- **representation_pairing**: 将用户选择的表征两两配对
- **loop_scoring**: 使用大模型循环评估每对表征的相关性（-2到+2）
- **network_analysis**: 计算互补性评分和冲突性评分，生成网络分析解读
- **network_visualization**: 生成Gephi风格网络结构图
  - 互补性网络图：展示正向协同关系（绿色线条）
  - 冲突性网络图：展示负向冲突关系（红色线条）
  - 力导向布局，节点大小根据连接数量动态调整

### 第3步：市场搜索与岗位推荐
- **job_analysis**: 使用联网搜索获取市场趋势和岗位信息
  - 搜索市场趋势分析（行业发展、需求变化、薪资水平）
  - 搜索并推荐3-5个适合的进阶岗位，显示完整信息（公司、薪资、要求）

### 第4步：卡通形象生成
- **cartoon_prompt_analysis**: 基于【用户基本信息 + 大五人格画像 + 表征特征】生成提示词
- **cartoon_image_generation**: 调用生图大模型生成卡通风格的未来自我画像

### 第5步：整合报告生成
- **report_generation**: 汇总所有内容，重新编排章节顺序：
  1. 卡通形象展示（报告开头）
  2. 用户个性画像（大五人格 + 表征解读）
  3. 未来自我画像解读（网络分析说明什么）
  4. 市场趋势与岗位推荐
  5. 学习推荐（在线课程和书籍推荐）
  6. 个性化温暖结语

## 图表输出
- 表征互补性网络图
- 表征冲突性网络图
- 表征能力雷达图
- 卡通风格未来自我画像

## 输入输出
**输入**:
- 用户基本信息（姓名、性别、学历、专业等）
- 选择的表征列表（最多25个）
- 个性化问题回答（3个问题）：
  1. 面对自己的职业发展，在3-5年内，你最关心什么问题？
  2. 面对自己的知识学习，在3-5年内，你最关心什么问题？
  3. 面对自己的生活愿景，在3-5年内，你最关心什么问题？
- 大五人格问卷回答（40题，基于CBF-PI-B量表，每维度8题）

**输出**:
- 完整的未来自我画像职业规划报告（Markdown格式）
- 未来自我画像职业规划报告（PDF格式）
- 卡通风格未来自我画像（URL）
- 表征互补性网络图（URL）
- 表征冲突性网络图（URL）
- 表征能力雷达图（URL）
- 互补性评分
- 冲突性评分
- 大五人格评估结果（五个维度的评分、等级、描述、分析）
- 市场趋势分析
- 岗位推荐列表（含完整信息：公司、薪资、链接）
