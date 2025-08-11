import json
from typing import Dict
from ...core.state import AcademicState

async def analyze_context(state: AcademicState) -> Dict:
    """
    分析学习状态上下文，为协调者决策提供信息。

    该方法通过以下方式进行全面的上下文分析:
    1. 提取学生的信息；
    2. 分析日程和任务；
    3. 从最新消息中识别相关的课程上下文；
    4. 收集学习偏好和学习模式。

    Args:
        state (AcademicState): 当前学习状态

    Returns:
        Dict: 结构化的上下文分析结果
    
    Implementation Note:
    -----------------
    - 使用嵌套的 `get()` 操作分层提取信息，保证安全 (不引发 KeyError)
    - 从最新消息内容中识别当前课程上下文
    - 为丢失的信息提供默认值，保证稳定性
    """
    profile = state.get("profile", {})
    calendar = state.get("calendar", {})
    tasks = state.get("tasks", {})

    courses = profile.get("academic_info", {}).get("current_courses", [])
    current_course = None
    request = state["messages"][-1].content.lower()

    for course in courses:
        if course["name"].lower() in request:
            current_course = course
            break
    
    return {
        "student": {
            "major": profile.get("personal_info", {}).get("major", "Unknown"),
            "year": profile.get("personal_info", {}).get("academic_year", "Unknown"),
            "learning_style": profile.get("learning_perferences", {}).get("learning_style", {}),
        },
        "course": current_course,
        "upcoming_events": len(calendar.get("events", [])),
        "active_tasks": len(tasks.get("tasks", [])),
        "study_patterns": profile.get("learning_perferences", {}).get("study_patterns", {})
    }

def parse_coordinator_response(response: str) -> Dict:
    """
    将 LLM 协调器的响应解析为结构化分析，供 Agent 执行使用

    此函数实现了稳健地解析策略：
    1. 从安全的默认配置开始
    2. 分析响应中的 ReAct 模式
    3. 根据内容调整 Agent 需求和优先级
    4. 组织可并发执行地 Agent 组

    Args:
        response (str): LLM 原始地响应文本
    
    Returns:
        Dict: 包含以下内容的结构化分析：
            - required_agents: 所需的 Agents 列表
            - priority: 每个 Agent 的优先级
            - concurrent_groups: 可以同时运行的 Agents 组
            - reasoning: 决策的推理说明
    
    Implementation Note:
    -----------------
    1. 默认配置：
        - 始终包含 PLANNER Agent 作为 Baseline
        - 设定基础优先级与并发结构
    
    2. 响应分析：
        - 查找 ReAct 模式（思考/决策结构）
        - 从内容关键词识别 Agent 需求
        - 从思考中提取推理的部分

    3. Agent 配置：
        - 出现与记笔记相关的内容时触发 NOTEWRITER
        - 出现与指导 / 建议相关的内容时触发 ADVISOR
        - 根据依赖关系组织可并发执行的 Agents 组
    
    4. 错误处理：
        - 如果解析失败，提供回退配置
        - 通过默认值保持系统稳定
    """
    try:
        analysis = {
            "required_agents": ["PLANNER"],     # PLANNER 始终必须
            "priority": {"PLANNER": 1},         # 基础优先级结构
            "concurrent_groups": [["PLANNER"]], # 默认执行组
            "reasoning": response               # 默认推理
        }

        # 解析 ReAct 模式以实现更高级的协调
        if "Thought:" in response and "Decision:" in response:
            # 检查是否需要 NOTEWRITER
            if "NOTEWRITER" in response or "note" in response.lower():
                analysis["required_agents"].append("NOTEWRITER")
                analysis["priority"]["NOTEWRITER"] = 2
                # NOTEWRITER 可以与 PLANNER 并发执行
                analysis["concurrent_groups"] = [["PLANNER", "NOTEWRITER"]]
            
            # 检查是否需要 ADVISOR
            if "ADVISOR" in response or "guidance" in response.lower():
                analysis["required_agents"].append("ADVISOR")
                analysis["priority"]["ADVISOR"] = 3
                # ADVISOR 通常在初步规划之后运行
            
            # 从思考中提取并保存推理
            thought_section = response.split("Thought:")[1].split("Action:")[0].strip()
            analysis["reasoning"] = thought_section
        
        return analysis
    except Exception as e:
        print(f"Parse error: {str(e)}")
        return {
            "required_agents": ["PLANNER"],
            "priority": {"PLANNER": 1},
            "concurrent_groups": [["PLANNER"]],
            "reasoning": "Fallback due to parse error"
        }

async def coordinator_agent(state: AcademicState) -> Dict:
    """
    使用 ReAct 框架协调多个学术支持 Agents 的主协调器 Agent

    该 Agent 实现了一个精细的协调策略：
    1. 分析学术上下文与学生需求
    2. 使用 ReAct 框架进行结构化决策
    3. 协调并行的 Agents 执行
    4. 处理回退 (fallback) 场景

    Args:
        state (AcademicState): 当前学术状态，包括消息和上下文信息
    
    Returns:
        Dict: 协调分析结果，包括所需 Agents、优先级和执行分组
    
    Implementation Note:
    -----------------
    1. ReAct 框架实现步骤：
        - Thought: 分析阶段
        - Action: Agent 选择阶段
        - Observation: 能力评估
        - Decision: 最终执行规划
    
    2. Agents 协调策略：
        - 管理三个专用 Agents：
            * PLANNER: 核心日程规划 Agent
            * NOTEWRITER: 内容创作 Agent
            * ADVISOR: 学术指导 Agent
    
    3. 并发执行管理：
        - 为可并行运行的 Agents 分组
        - 保持执行依赖关系
        - 协调并发工作流
    """

    try:
        # 分析当前上下文并提取最新请求
        context = await analyze_context(state)
        query = state["messages"][-1].content

        # 初始化 llm 和定义基于 ReAct 框架的协调提示
        from ...prompts.templates import COORDINATOR_PROMPT
        from ...services.llm_service import OpenRouter
        llm = OpenRouter()
        prompt = COORDINATOR_PROMPT.format(
            request=query,
            context=json.dumps(context, indent=2)
        )

        # LLM 生成协调计划
        response = await llm.agenerate([
            {"role": "user", "content": prompt}
        ])

        # 解析响应并生成结构化协调分析
        analysis = parse_coordinator_response(response)
        return {
            "results": {
                "coordinator_analysis": {
                    "required_agents": analysis.get("required_agents", ["PLANNER"]),
                    "priority": analysis.get("priority", {"PLANNER": 1}),
                    "concurrent_groups": analysis.get("concurrent_groups", [["PLANNER"]]),
                    "reasoning": response
                }
            }
        }

    except Exception as e:
        print(f"Coordinator error: {str(e)}")
        return {
            "results": {
                "coordinator_analysis": {
                    "required_agents": ["PLANNER"],
                    "priority": {"PLANNER": 1},
                    "concurrent_groups": [["PLANNER"]],
                    "reasoning": "Fallback due to error"
                }
            }
        }
