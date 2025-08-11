# ATLAS 项目重构计划

## 目标目录结构

```
atlas/
│
├── src/
│   └── atlas/
│       ├── __init__.py
│       ├── main.py                     # 主入口点
│       ├── core/                       # 核心配置和基础设施
│       │   ├── __init__.py
│       │   ├── config.py               # 配置管理
│       │   ├── state.py                # 状态定义
│       │   └── llm_provider.py         # LLM服务提供者 (重命名自llm_init.py)
│       ├── models/                     # 数据模型
│       │   ├── __init__.py
│       │   └── data_models.py          # 数据结构定义
│       ├── services/                   # 业务服务层
│       │   ├── __init__.py
│       │   ├── data_manager.py         # 数据管理 (重命名自data.py)
│       │   └── orchestration.py       # 工作流编排
│       ├── agents/                     # 智能体模块
│       │   ├── __init__.py
│       │   ├── base/                   # 基础智能体类
│       │   │   ├── __init__.py
│       │   │   ├── executor.py         # 智能体执行器
│       │   │   └── react_agent.py      # ReAct智能体
│       │   ├── academic/               # 学术相关智能体
│       │   │   ├── __init__.py
│       │   │   ├── planner_agent.py
│       │   │   ├── note_writer_agent.py
│       │   │   ├── advisor_agent.py
│       │   │   └── profile_analyzer_agent.py
│       │   └── coordinator/            # 协调器
│       │       ├── __init__.py
│       │       └── coordinator_agent.py
│       ├── prompts/                    # 提示词管理
│       │   ├── __init__.py
│       │   └── prompt_templates.py     # 重命名自prompts.py
│       └── utils/                      # 工具函数
│           ├── __init__.py
│           └── action_and_output.py    # 输出处理工具
│
├── tests/                              # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_core/
│   ├── test_services/
│   └── test_agents/
│
├── .gitignore
├── README.md
├── pyproject.toml
└── requirements.txt                    # 如果存在的话
```

## 文件移动映射

| 原文件名 | 新位置 | 重命名 |
|---------|--------|--------|
| main.py | src/atlas/main.py | 否 |
| state.py | src/atlas/core/state.py | 否 |
| llm_init.py | src/atlas/core/llm_provider.py | 是 |
| data.py | src/atlas/services/data_manager.py | 是 |
| orchestration.py | src/atlas/services/orchestration.py | 否 |
| executor.py | src/atlas/agents/base/executor.py | 否 |
| react_agent.py | src/atlas/agents/base/react_agent.py | 否 |
| planner_agent.py | src/atlas/agents/academic/planner_agent.py | 否 |
| note_writer_agent.py | src/atlas/agents/academic/note_writer_agent.py | 否 |
| advisor_agent.py | src/atlas/agents/academic/advisor_agent.py | 否 |
| profile_analyzer_agent.py | src/atlas/agents/academic/profile_analyzer_agent.py | 否 |
| coordinator_agent.py | src/atlas/agents/coordinator/coordinator_agent.py | 否 |
| prompts.py | src/atlas/prompts/prompt_templates.py | 是 |
| action_and_output.py | src/atlas/utils/action_and_output.py | 否 |

## 需要修改的导入路径

所有文件中的相对导入需要更新为新的包结构路径。
