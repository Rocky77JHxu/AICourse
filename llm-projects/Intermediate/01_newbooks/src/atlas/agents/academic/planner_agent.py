import json
from datetime import datetime, timedelta, timezone
from typing import Dict
from langgraph.graph import StateGraph
from ...core.state import AcademicState
from ..base.react_agent import ReActAgent


class PlannerAgent(ReActAgent):
    def __init__(self, llm):
        super().__init__(llm)  # 初始化父类 ReActAgent
        self.llm = llm
        # 加载示例场景，帮助 AI 生成更合适的回答
        self.few_shot_examples = self._initialize_fewshots()
        # 创建工作流程结构
        self.workflow = self.create_subgraph()
    
    def _initialize_fewshots(self):
        """
        定义示例场景，帮助 AI 理解如何应对不同情况。
        每个示例包含：
        - Input: 学生的请求
        - Thought: 分析过程
        - Action: 需要执行的动作
        - Observation: 得到的发现
        - Plan: 详细的解决方案
        """
        return [
            {
                "input": "在管理注意力缺陷多动症（ADHD）和足球训练的同时复习考试",
                "thought": "需要检查日程冲突和精力模式",
                "action": "search_calendar",
                "observation": "下午6点有足球赛，第二天早上9点考试",
                "plan": """ADHD-OPTIMIZED SCHEDULE:
                    足球前（下午2点-5点）：
                    - 3次20分钟学习冲刺
                    - 中间穿插活动休息
                    - 每次冲刺后快速奖励

                    足球赛（下午6点-8点）：
                    - 用作多巴胺重置
                    - 中场休息时复习公式

                    足球后（晚上9点-12点）：
                    - 环境：咖啡厅的背景噪音
                    - 15/5 学习/休息循环
                    - 每小时更换一次学习地点

                    紧急应对策略：
                    - 集中力丢失 → 原地跳
                    - 压力过大 → 换个房间
                    - 脑雾 → 冷水冲脸"""
            },
            {
                "input": "应对多个截止日期压力",
                "thought": "检查任务优先级和表现问题",
                "action": "analyze_tasks",
                "observation": "有 3 项作业同时到期，微积分成绩最低",
                "plan": """优先级学习安排：
                    高专注时段：
                    - 早晨：微积分练习
                    - 锻炼后：写作业
                    - 晚上：快速复习

                    ADHD 管理策略：
                    - 任务计时挑战
                    - 每完成一个任务就奖励自己
                    - 找学习伙伴监督"""
            }
        ]
    
    # Section 2: 创建计划工作流图并编译返回
    def create_subgraph(self) -> StateGraph:
        """
        创建一个定义计划处理过程的工作流图：
        1. 首先分析日程（calendar_analyzer）
        2. 然后分析任务（task_analyzer）
        3. 最后生成计划（plan_generator）
        """
        # 用 AcademicState 结构初始化新图
        subgraph = StateGraph(AcademicState)

        # 添加每一步处理节点
        subgraph.add_node("calendar_analyzer", self.calendar_analyzer)
        subgraph.add_node("task_analyzer", self.task_analyzer)
        subgraph.add_node("plan_generator", self.plan_generator)

        # 按执行顺序连接节点
        subgraph.add_edge("calendar_analyzer", "task_analyzer")
        subgraph.add_edge("task_analyzer", "plan_generator")

        # 设置工作流的起始点
        subgraph.set_entry_point("calendar_analyzer")

        # 编译并返回可用的工作流
        return subgraph.compile()

    async def calendar_analyzer(self, state: AcademicState) -> AcademicState:
        """
        分析学生的日历数据，找出：
        - 可用的学习时间段
        - 可能的时间冲突
        - 一天中的精力变化模式
        """
        # 获取未来 7 天内的日历事件
        events = state["calendar"].get("events", [])
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=7)

        # 只保留未来的事件
        filtered_events = [
            event for event in events
            if now <= datetime.fromisoformat(event["start"]["dateTime"]) <= future
        ]

        # 给 AI 分析日历的提示语
        prompt = """分析日历事件并识别：
        事件列表: {events}

        请关注：
        - 可用的空档时间
        - 活动对精力的影响
        - 潜在冲突
        - 恢复期安排
        - 学习机会窗口
        - 活动模式
        - 日程优化方案
        """

        # 向 AI 发送分析请求
        messages = [
            {"role": "user", "content": prompt.format(events=json.dumps(filtered_events))}
        ]

        response = await self.llm.agenerate(messages)

        # 返回分析结果
        return {
            "results": {
                "calendar_analysis": {
                    "analysis": response
                }
            }
        }

    async def task_analyzer(self, state: AcademicState) -> AcademicState:
        """
        分析任务信息以确定：
        - 优先级顺序
        - 完成每项任务所需时间
        - 最佳完成方法
        """
        tasks = state["tasks"].get("tasks", [])

        # AI 分析任务优先级提示
        prompt = """分析任务并生成优先结构：
        任务列表: {tasks}

        考虑因素：
        - 紧迫程度
        - 任务复杂度
        - 精力消耗
        - 依赖关系
        - 所需专注程度
        - 时间预估
        - 学习目标
        - 成功标准
        """

        messages = [
            {"role": "user", "content": prompt.format(tasks=json.dumps(tasks))}
        ]

        response = await self.llm.agenerate(messages)

        return {
            "results": {
                "task_analysis": {
                    "analysis": response
                }
            }
        }

    async def plan_generator(self, state: AcademicState) -> AcademicState:
        """
        通过整合以下分析生成全面的学习计划：
        - 学生的学习风格分析（Profile Analysis）
        - 日程分析（可用时间）
        - 任务分析（要做的内容）
        """
        # 收集之前的所有分析结果
        profile_analysis = state["results"]["profile_analysis"]
        calendar_analysis = state["results"]["calendar_analysis"]
        task_analysis = state["results"]["task_analysis"]

        # 生成详细计划的提示语
        prompt = f"""AI 学习计划助手：使用 ReACT 框架制定专注学习计划。

          输入上下文：
          - 学生情况分析: {profile_analysis}
          - 日历分析: {calendar_analysis}
          - 任务分析: {task_analysis}

          示例：
          {json.dumps(self.few_shot_examples, indent=2)}

          指令：
          1. 按 ReACT 模式：
            Thought: 分析情况和需求
            Action: 考虑所有分析结果
            Observation: 综合发现
            Plan: 制定结构化计划

          2. 必须包含：
            - ADHD 管理策略
            - 精力水平优化
            - 任务拆分方法
            - 专注时段安排
            - 更换环境策略
            - 恢复期安排
            - 社交/体育活动平衡

          3. 还需包括：
            - 紧急应对策略
            - 备用方案
            - 快速成果
            - 奖励机制
            - 进度跟踪
            - 调整触发点

          请像一个聪明的学习助理，用口语化的方式帮助学生达成目标或克服困难。

          格式：
          Thought: [推理与情况分析]
          Action: [综合方法]
          Observation: [关键发现]
          Plan: [可执行的结构化计划]
          """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": state["messages"][-1].content}
        ]

        response = await self.llm.agenerate(messages, temperature=0.5)

        return {
                "results": {
                    "final_plan": {
                        "plan": response
                    }
                }
        }

    async def __call__(self, state: AcademicState) -> Dict:
        """
        主执行方法，运行整套规划工作流：
        1. 分析日历
        2. 分析任务
        3. 生成计划
        """
        try:
            final_state = await self.workflow.ainvoke(state)
            # 返回生成的计划
            plan = final_state["results"].get("final_plan", {})
            return {"plan": plan}
        except Exception as e:
            print(f"PlannerAgent error: {e}")
            return {"plan": {"plan": "Error generating plan. Please try again."}}
