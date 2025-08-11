"""
ATLAS - Academic Task Learning Agent System

一个基于 LangGraph 的多智能体学术辅助系统，为学生提供个性化的
学业规划、笔记整理和学术指导服务。

主要功能模块:
- agents: 智能体实现
- core: 核心功能和配置
- models: 数据模型定义
- services: 业务服务层
- utils: 通用工具函数
- prompts: 提示模板管理
"""

__version__ = "0.1.0"
__author__ = "ATLAS Development Team"

# 导出主要组件
from .core.state import AcademicState
from .core.orchestration import create_agents_graph
from .services.data_manager import DataManager
from .services.llm_service import OpenRouter

__all__ = [
    "AcademicState",
    "create_agents_graph", 
    "DataManager",
    "OpenRouter"
]
