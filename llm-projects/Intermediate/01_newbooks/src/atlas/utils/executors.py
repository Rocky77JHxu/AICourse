import asyncio
from typing import Dict
from ..core.state import AcademicState
from ..agents.academic.planner_agent import PlannerAgent
from ..agents.academic.note_writer_agent import NoteWriterAgent
from ..agents.academic.advisor_agent import AdvisorAgent


class AgentExecutor:

    def __init__(self, llm):
        """
        使用语言模型初始化执行器并创建 Agent 实例

        Args:
            llm: 语言模型实例
        
        Implementation Note:
            - 创建一个专有的 Agents 字典，每个 Agent 都使用相同的 LLM 进行初始化；
            - 支持多种 Agent 类型: PLANNER (default), NOTEWRITER, and ADVISOR
            - 这些 Agents 仅实例化一次并在多次执行中重复使用
        """
        self.llm = llm
        self.agents = {
            "PLANNER": PlannerAgent(llm),       # Strategic planning agent
            "NOTEWRITER": NoteWriterAgent(llm), # Documentation agent
            "ADVISOR": AdvisorAgent(llm)        # Acadmic advice agent
        }

    async def execute(self, state: AcademicState) -> Dict:
        """
        基于分析结果协调多个 AI Agents 的并发执行

        该方法实现了一个复杂的执行模式：
        1. 读取协调分析以确定所需的 Agent
        2. 为并发执行对 Agent 进行分组
        3. 并发执行 Agent 组
        4. 使用回退机制处理失败

        Args:
            state (AcademicState): 当前状态（包含分析结果）

        Returns:
            Dict: 所有 Agents 执行的合并结果

        Implementation Details:
        ----------------------
        1. 分析推断结果:
            - 从 State 中读取协调分析结果
            - 根据分析结果确定所需的 Agents 组
        2. 并发执行模式：
            - 将 Agents 分组，组内的 Agents 并发执行
            - 在每组内使用 `asyncio.gather()` 实现并发执行
        3. 结果管理：
            - 收集并处理每个并发组的结果
            - 过滤掉失败的执行（异常）
            - 将成功的结果格式化为结构化的输出
        4. 回退机制：
            - 如果没有收集到结果，则返回到 PLANNER Agent
            - 在完全失败的情况下，提供紧急回退计划
        
        Error Handling:
        ---------------
        - 在多个层级捕获并处理异常：
            * 单个 Agent 执行失败不会影响其它 Agent
            * 系统级故障触发紧急回退
        - 通过优雅降级保持系统稳定性
        """
        try:
            # 从 state 中提取协调分析结果
            analysis = state["results"].get("coordinator_analysis", {})

            # 确定执行需求
            required_agents = analysis.get("required_agents", ["PLANNER"])
            concurrent_groups = analysis.get("concurrent_groups", [])

            # 初始化结果容器
            results = {}

            # 按顺序处理每个并发组
            for group in concurrent_groups:
                # 为每个组准备并发任务集
                tasks = []
                for agent_name in group:
                    # 校验 Agent 可用性和需求
                    if agent_name in required_agents and agent_name in self.agents:
                        tasks.append(self.agents[agent_name](state))
                
                # 并发执行任务组
                if tasks:
                    # 收集并发执行结果
                    group_results = await asyncio.gather(*tasks, return_exceptions=True)

                    # 仅处理成功的结果
                    for agent_name, result in zip(group, group_results):
                        if not isinstance(result, Exception):
                            results[agent_name.lower()] = result
            
            # 实现回退机制
            if not results and "PLANNER" in self.agents:
                planner_result = await self.agents["PLANNER"](state)
                results["planner"] = planner_result

            print("agent_outputs", results)

            # 返回结构化结果
            return {
                "results": {
                    "agent_outputs": results
                }
            }   

        except Exception as e:
            print(f"Execution error: {e}")
            # 最小响应紧急回退
            return {
                "results": {
                    "agent_outputs": {
                        "planner": {
                            "plan": "Emergency fallback plan: Please try again or contact support."
                        }
                    }
                }
            }
