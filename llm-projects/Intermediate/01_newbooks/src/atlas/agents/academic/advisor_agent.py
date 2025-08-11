import json
from typing import Dict
from langgraph.graph import StateGraph, START, END
from ...core.state import AcademicState
from ..base.react_agent import ReActAgent


class AdvisorAgent(ReActAgent):
    """学业顾问代理（Advisor），带有子图工作流，用于提供个性化指导。
    该代理专注于分析学生的实际情况，并结合学习风格和时间限制，
    提供定制化的学业建议。"""

    def __init__(self, llm):
        """使用 LLM 后端和示例模板初始化 Advisor 代理。

        参数:
            llm: 用于文本生成的语言模型实例
        """
        super().__init__(llm)
        self.llm = llm

        # 定义全面的示例，用于指导生成
        # 这些示例帮助 LLM 理解期望的格式和深度
        self.few_shot_examples = [
            {
                "request": "在时间有限的情况下管理多个截止日期",
                "profile": {
                    "learning_style": "视觉型",
                    "workload": "工作量大",
                    "time_constraints": ["2 场黑客松", "项目", "考试"]
                },
                "advice": """基于优先级的日程安排：

                1. 立即执行的行动
                   • 制作包含所有截止日期的可视化时间表
                   • 将每个任务拆分为 45 分钟的工作块
                   • 高专注工作的时间安排在早晨

                2. 工作量管理
                   • 黑客松：提前组队并明确角色分工
                   • 项目：每天 2 小时专注工作
                   • 考试：交替练习与休息相结合

                3. 精力优化
                   • 高强度任务使用番茄工作法 (25/5)
                   • 学习段落之间进行身体活动
                   • 定期跟踪进度

                4. 紧急应对策略
                   • 压力过大：进行 10 分钟重置休息
                   • 卡住时：切换任务或环境
                   • 感到疲倦：小睡片刻，然后回顾知识点"""
            }
        ]
        # 初始化代理的工作流状态机
        self.workflow = self.create_subgraph()

    def create_subgraph(self) -> StateGraph:
        """创建 Advisor 的内部工作流（状态机）。

        工作流包含两个主要阶段：
        1. 情况分析 - 了解学生的需求
        2. 指导生成 - 制作个性化建议

        返回:
            StateGraph: 编译后的工作流图
        """
        subgraph = StateGraph(AcademicState)

        # 添加分析与指导的节点（命名保持一致）
        subgraph.add_node("advisor_analyze", self.analyze_situation)
        subgraph.add_node("advisor_generate", self.generate_guidance)

        # 连接工作流节点
        subgraph.add_edge(START, "advisor_analyze")
        subgraph.add_edge("advisor_analyze", "advisor_generate")
        subgraph.add_edge("advisor_generate", END)

        return subgraph.compile()

    async def analyze_situation(self, state: AcademicState) -> AcademicState:
        """分析学生当前的学业状况与需求。

        评估内容：
        - 学生档案及偏好
        - 当前挑战与限制
        - 学习风格的匹配度
        - 时间与压力管理需求

        参数:
            state: 当前学术状态，包含学生档案与请求

        返回:
            包含情况分析结果的更新状态
        """
        profile = state["profile"]
        learning_prefs = profile.get("learning_preferences", {})

        prompt = f"""分析学生情况并确定指导方案：

        背景信息：
        - 档案: {json.dumps(profile, indent=2)}
        - 学习偏好: {json.dumps(learning_prefs, indent=2)}
        - 请求: {state['messages'][-1].content}

        分析维度：
        1. 当前挑战
        2. 学习风格匹配度
        3. 时间管理需求
        4. 压力管理需求
        """

        response = await self.llm.agenerate([
            {"role": "user", "content": prompt}
        ])

        return {
            "results": {
                "situation_analysis": {
                    "analysis": response
                }
            }
        }

    async def generate_guidance(self, state: AcademicState) -> AcademicState:
        """基于情况分析生成个性化学业指导意见。

        制作的建议重点包括：
        - 可立即执行的行动步骤
        - 日程优化方案
        - 精力与资源管理
        - 支持策略
        - 预案与应急方案

        参数:
            state: 包含情况分析的当前学术状态

        返回:
            包含生成指导结果的更新状态
        """

        analysis = state["results"].get("situation_analysis", "")

        prompt = f"""基于分析结果生成个性化学业指导：

        分析结果: {analysis}
        示例: {json.dumps(self.few_shot_examples, indent=2)}

        格式要求：
        1. 立即执行步骤
        2. 日程优化
        3. 精力管理
        4. 支持策略
        5. 紧急应对 protocol
        """

        response = await self.llm.agenerate([
            {"role": "user", "content": prompt}
        ])

        return {
            "results": {
                "guidance": {
                    "advice": response
                }
            }
        }

    async def __call__(self, state: AcademicState) -> Dict:
        """Advisor 代理的主执行方法。

        执行完整的顾问工作流：
        1. 分析学生情况
        2. 生成个性化指导
        3. 返回包含元数据的格式化结果

        参数:
            state: 初始学术状态

        返回:
            包含指导结果和元数据的字典，或错误信息

        说明:
            元数据包含建议是否与课程相关，以及是否考虑学习风格
        """

        try:
            final_state = await self.workflow.ainvoke(state)
            return {
                "advisor_output": {
                    "guidance": final_state["results"].get("guidance"),
                    "metadata": {
                        "course_specific": True,
                        "considers_learning_style": True
                    }
                }
            }
        except Exception as e:
            print(f"AdvisorAgent error: {e}")
            return {
                "advisor_output": {
                    "guidance": {"advice": "生成指导出错，请重试。"}
                }
            }
