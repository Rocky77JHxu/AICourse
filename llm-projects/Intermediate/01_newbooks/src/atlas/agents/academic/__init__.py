"""
学术智能体模块 (Academic Agents Module)

此模块包含专门用于学术任务处理的智能体，包括档案分析、计划制定、
笔记撰写和学业指导等核心功能。
"""

from .profile_analyzer_agent import profile_analyzer
from .planner_agent import PlannerAgent
from .note_writer_agent import NoteWriterAgent
from .advisor_agent import AdvisorAgent

__all__ = [
    "profile_analyzer",
    "PlannerAgent", 
    "NoteWriterAgent",
    "AdvisorAgent"
]
