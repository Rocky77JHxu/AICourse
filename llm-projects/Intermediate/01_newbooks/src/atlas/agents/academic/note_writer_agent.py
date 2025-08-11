import json
from typing import Dict
from langgraph.graph import StateGraph, START, END
from ...core.state import AcademicState
from ..base.react_agent import ReActAgent


class NoteWriterAgent(ReActAgent):
    """NoteWriter（笔记撰写）代理，带有自己的子图工作流，用于生成学习笔记。
    该代理专注于通过分析学习风格并生成结构化笔记，提供个性化的学习资料。"""

    def __init__(self, llm):
        """使用 LLM 后端和示例模板初始化 NoteWriter 代理。

        参数:
            llm: 用于文本生成的语言模型实例
        """
        super().__init__(llm)
        self.llm = llm
        self.few_shot_examples = [
            {
                "input": "需要为明天突击复习微积分 III",
                "template": "快速复习",
                "notes": """微积分 III 重点：

                1. 核心概念（80/20 原则）：
                   • 多重积分 → 体积/面积计算
                   • 向量分析 → 流量/功/旋度
                   • 关键公式：
                     - 圆柱/球坐标下的三重积分
                     - 旋度（curl）、散度（divergence）、梯度（gradient）关系

                2. 常见考试题型：
                   • 寻找驻点
                   • 计算通量/功
                   • 有约束条件的优化题

                3. 快速入门技巧：
                   • 一定要画三维图
                   • 检查单位是否匹配
                   • 利用对称性简化运算

                4. 紧急应对建议：
                   • 卡住时尝试坐标变换
                   • 检查边界条件
                   • 注意特殊模式"""
            }
        ]
        self.workflow = self.create_subgraph()

    def create_subgraph(self) -> StateGraph:
        """创建 NoteWriter 的内部工作流（状态机）。

        工作流包含两个主要步骤：
        1. 分析学习风格和内容需求
        2. 生成个性化笔记

        返回:
            StateGraph: 编译后的工作流图
        """
        subgraph = StateGraph(AcademicState)

        # 定义核心工作流节点
        subgraph.add_node("notewriter_analyze", self.analyze_learning_style)
        subgraph.add_node("notewriter_generate", self.generate_notes)

        # 创建工作流顺序：
        # START -> 分析 -> 生成 -> END
        subgraph.add_edge(START, "notewriter_analyze")
        subgraph.add_edge("notewriter_analyze", "notewriter_generate")
        subgraph.add_edge("notewriter_generate", END)

        return subgraph.compile()

    async def analyze_learning_style(self, state: AcademicState) -> AcademicState:
        """分析学生档案与请求，确定最佳的笔记结构。

        使用 LLM 分析：
        - 学生的学习风格偏好
        - 具体的内容需求
        - 时间限制与学习要求

        参数:
            state: 包含学生档案与对话信息的当前学术状态

        返回:
            包含学习分析结果的状态
        """
        profile = state["profile"]
        learning_style = profile["learning_preferences"]["learning_style"]
        # 按特定格式要求构建分析提示语

        prompt = f"""分析内容需求，并确定最佳笔记结构：

        学生档案：
        - 学习风格: {json.dumps(learning_style, indent=2)}
        - 请求: {state['messages'][-1].content}

        格式要求：
        1. 关键主题（80/20 原则）
        2. 针对学习风格的调整
        3. 时间管理策略
        4. 快速查阅格式

        重点关注：
        - 提供最大理解度的核心概念
        - 视觉化与互动化元素
        - 节省时间的学习方法
        """

        response = await self.llm.agenerate([
            {"role": "user", "content": prompt}
        ])

        return {
            "results": {
                "learning_analysis": {
                    "analysis": response
                }
            }
        }

    async def generate_notes(self, state: AcademicState) -> AcademicState:
        """基于学习分析结果生成个性化学习笔记。

        使用 LLM 生成结构化笔记，特点：
        - 适配学生的学习风格
        - 聚焦于关键概念（80/20 原则）
        - 针对学习周期进行时间优化

        参数:
            state: 包含学习分析的当前学术状态
        返回:
            更新后的状态，包含生成的笔记
        """

        analysis = state["results"].get("learning_analysis", "")
        learning_style = state["profile"]["learning_preferences"]["learning_style"]

        # 使用分析结果和 few-shot 示例构建提示语
        prompt = f"""基于分析结果，创建简洁高效的学习资料：

        分析结果: {analysis}
        学习风格: {json.dumps(learning_style, indent=2)}
        请求: {state['messages'][-1].content}

        示例：
        {json.dumps(self.few_shot_examples, indent=2)}

        格式模板：
        **三周密集学习计划**

        [生成包含以下内容的结构化笔记:]
        1. 每周安排
        2. 每日重点
        3. 核心概念
        4. 紧急应对技巧
        """

        response = await self.llm.agenerate([
            {"role": "user", "content": prompt}
        ])

        return {
            "results": {
                "generated_notes": {
                    "notes": response
                }
            }
        }

    async def __call__(self, state: AcademicState) -> Dict:
        """NoteWriter 代理的主执行方法。

        执行完整的工作流：
        1. 分析学习需求
        2. 生成个性化笔记
        3. 清理并返回结果

        参数:
            state: 初始学术状态

        返回:
            包含生成笔记或错误信息的字典
        """
        try:
            final_state = await self.workflow.ainvoke(state)
            # 返回生成的笔记
            notes = final_state["results"].get("generated_notes", {})
            return {"notes": notes}
        except Exception as e:
            print(f"NoteWriterAgent error: {e}")
            return {"notes": {"notes": "Error generating notes. Please try again."}}
