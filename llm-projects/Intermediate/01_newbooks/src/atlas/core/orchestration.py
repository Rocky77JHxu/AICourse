"""
这段代码展示了如何创建一个协调的工作流系统（StateGraph），该系统管理多个并行运行的 AI 学术支持代理。

关键组件：
- 状态图创建
- 使用节点和边构建工作流
- 定义 Agents 之间的执行路径
- 管理状态转换
- 并行 Agents 协调

三个主 Agents 协调工作：
- PlannerAgent (scheduling/calendar)
- NoteWriterAgent (study materials)
- AdvisorAgent (academic guidance)

Orchestrator: 协调多个 Agents 的工作流
Router: 将请求导向合适的 Agent
State Manager: 维护工作流状态和转换
Completion Handler: 确定何时所有必要工作完成
"""

from typing import List, Union, Literal
from langgraph.graph import StateGraph, START, END
from .state import AcademicState
from ..agents.coordinator.coordinator_agent import coordinator_agent
from ..agents.academic.profile_analyzer_agent import profile_analyzer
from ..agents.academic.planner_agent import PlannerAgent
from ..agents.academic.note_writer_agent import NoteWriterAgent
from ..agents.academic.advisor_agent import AdvisorAgent
from ..utils.executors import AgentExecutor

def create_agents_graph(llm) -> StateGraph:
    """创建一个多智能体协作的工作流图。

    该编排系统负责并行调度三个专门的智能体：
    - PlannerAgent：负责日程安排与日历管理  
    - NoteWriterAgent：生成个性化的学习资料  
    - AdvisorAgent：提供学业指导与支持  

    此工作流采用状态机机制，根据对学生需求的分析进行条件路由。

    参数：
        llm: 所有智能体共享的语言模型实例

    返回：
        StateGraph: 编译好的支持并行执行路径的工作流图
    """
    # 初始化主工作流状态机
    workflow = StateGraph(AcademicState)

    # 创建我们的专用智能体实例
    # 每个智能体都有自己的内部操作子图
    planner_agent = PlannerAgent(llm)
    notewriter_agent = NoteWriterAgent(llm)
    advisor_agent = AdvisorAgent(llm)
    executor = AgentExecutor(llm)

    # === 主工作流节点 ===
    # 这些节点负责高层的协调与分析
    workflow.add_node("coordinator", coordinator_agent)  # 初始请求分析
    workflow.add_node("profile_analyzer", profile_analyzer)  # 学生档案分析
    workflow.add_node("execute", executor.execute)  # 最终执行节点

    # === 并行执行路径选择 ===
    def route_to_parallel_agents(state: AcademicState) -> List[str]:
        """决定当前请求需要由哪些智能体处理。

        通过分析协调器的输出，将任务路由到合适的智能体。  
        如果没有明确指定智能体，则默认使用 Planner。

        参数：
            state: 当前学业状态，包含协调器的分析结果

        返回：
            List: 后续需要执行的节点名称列表
        """
        analysis = state["results"].get("coordinator_analysis", {})
        required_agents = analysis.get("required_agents", [])
        next_nodes = []

        # 根据分析结果路由到对应智能体入口
        if "PLANNER" in required_agents:
            next_nodes.append("calendar_analyzer")
        if "NOTEWRITER" in required_agents:
            next_nodes.append("notewriter_analyze")
        if "ADVISOR" in required_agents:
            next_nodes.append("advisor_analyze")

        # 如果没指定特定智能体，默认使用 Planner
        return next_nodes if next_nodes else ["calendar_analyzer"]

    # === 智能体子工作流节点 ===
    # 添加 Planner 智能体的工作流节点
    workflow.add_node("calendar_analyzer", planner_agent.calendar_analyzer)
    workflow.add_node("task_analyzer", planner_agent.task_analyzer)
    workflow.add_node("plan_generator", planner_agent.plan_generator)

    # 添加 NoteWriter 智能体的工作流节点
    workflow.add_node("notewriter_analyze", notewriter_agent.analyze_learning_style)
    workflow.add_node("notewriter_generate", notewriter_agent.generate_notes)

    # 添加 Advisor 智能体的工作流节点
    workflow.add_node("advisor_analyze", advisor_agent.analyze_situation)
    workflow.add_node("advisor_generate", advisor_agent.generate_guidance)

    # === 工作流连接关系 ===
    # 主工作流入口
    workflow.add_edge(START, "coordinator")
    workflow.add_edge("coordinator", "profile_analyzer")

    # 将档案分析结果连接到可能的并行执行路径
    workflow.add_conditional_edges(
        "profile_analyzer",
        route_to_parallel_agents,
        ["calendar_analyzer", "notewriter_analyze", "advisor_analyze"]
    )

    # 连接 Planner 智能体的内部工作流
    workflow.add_edge("calendar_analyzer", "task_analyzer")
    workflow.add_edge("task_analyzer", "plan_generator")
    workflow.add_edge("plan_generator", "execute")

    # 连接 NoteWriter 智能体的内部工作流
    workflow.add_edge("notewriter_analyze", "notewriter_generate")
    workflow.add_edge("notewriter_generate", "execute")

    # 连接 Advisor 智能体的内部工作流
    workflow.add_edge("advisor_analyze", "advisor_generate")
    workflow.add_edge("advisor_generate", "execute")

    # === 工作流完成状态检查 ===
    def should_end(state) -> Union[Literal["coordinator"], Literal[END]]:
        """判断是否所有所需智能体都已完成任务。

        将已完成的智能体输出与所需智能体进行比较，  
        决定是结束还是继续工作流。

        参数：
            state: 当前学业状态

        返回：
            "coordinator" 表示继续，END 表示结束
        """
        analysis = state["results"].get("coordinator_analysis", {})
        executed = set(state["results"].get("agent_outputs", {}).keys())
        required = set(a.lower() for a in analysis.get("required_agents", []))
        return END if required.issubset(executed) else "coordinator"

    # 如果需要则条件跳回协调器节点
    workflow.add_conditional_edges(
        "execute",
        should_end,
        {
            "coordinator": "coordinator",  # 如果有更多任务则循环
            END: END  # 所有任务完成则结束
        }
    )

    # 编译并返回完整的工作流
    return workflow.compile()
