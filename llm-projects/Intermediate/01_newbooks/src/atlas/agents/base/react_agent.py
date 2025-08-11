from datetime import datetime, timezone
from typing import Dict, List
from ...core.state import AcademicState


class ReActAgent:
    """
    实现推理和行动能力的 ReAct Agents 的基类

    Features:
    - 具体行动的工具管理器
    - 少样本提示
    - 结构化思考过程
    - 行动执行框架
    """

    def __init__(self, llm):
        """
        初始化 ReActAgent

        Args:
            llm: 语言模型实例
        """
        self.llm = llm
        self.few_shot_examples = []
        self.tools = {
            "search_calendar": self.search_calendar,            # 日程搜索
            "analyze_tasks": self.analyze_tasks,                # 任务分析
            "check_learning_style": self.check_learning_style,   # 学习风格
            "check_performance": self.check_performance          # 学习成绩
        }

    async def search_calendar(self, state: AcademicState) -> List[Dict]:
        """
        搜索日程上的事件

        Args:
            state (AcademicState): 当前状态

        Returns:
            List[Dict]: 事件列表
        """
        # 获取事件
        events = state["calendar"].get("events", [])
        now = datetime.now(timezone.utc)
        # 过滤并返回未来事件
        return [e for e in events if datetime.fromisoformat(e["start"]["dateTime"]) > now]

    async def analyze_tasks(self, state: AcademicState) -> List[Dict]:
        """
        分析当前任务

        Args:
            state (AcademicState): 当前状态

        Returns:
            List[Dict]: 任务列表
        """
        return state["tasks"].get("tasks", [])

    async def check_learning_style(self, state: AcademicState) -> AcademicState:
        """
        检索学习风格

        Args:
            state (AcademicState): 当前状态

        Returns:
            AcademicState: 更新当前状态的学习风格
        """
        profile = state["profile"]

        learning_data = {
            "style": profile.get("learning_perferences", {}).get("learning_style", {}),
            "patterns": profile.get("learning_perferences", {}).get("study_patterns", {})
        }

        if "results" not in state:
            state["results"] = {}
        state["results"]["learning_analysis"] = learning_data
        
        return state

    async def check_performance(self, state: AcademicState) -> AcademicState:
        """
        检索各课程学习成绩

        Args:
            state (AcademicState): 当前状态

        Returns:
            AcademicState: 更新当前状态的学习成绩
        """
        profile = state["profile"]

        courses = profile.get("academic_info", {}).get("current_courses", [])

        if "results" not in state:
            state["results"] = {}
        state["results"]["performance_analysis"] = {"courses": courses}
        
        return state
