import json
from typing import Dict
from ...core.state import AcademicState

async def profile_analyzer(state: AcademicState) -> Dict:
    """
    使用 ReAct 框架分析学生档案数据，以提取和解释学习偏好

    该 Agent 的专长包括：
    1. 对学生学习档案进行深入分析
    2. 提取学习偏好与学习模式
    3. 解读学术历史与学习倾向
    4. 生成个性化的学习见解

    Args:
        state (AcademicState): 当前学术状态，包含学生档案数据

    Returns:
        Dict: 结构化分析结果，包括学习偏好和学习建议

    Implementation Note:
    -------------------
    1. 档案分析流程：
       - 从 state 中提取档案数据
       - 应用 ReACT 框架进行结构化分析
       - 生成全面的学习见解

    2. ReACT 模式实现：
       PROFILE_ANALYZER_PROMPT 通常包含：
       - Thought: 对学习模式与偏好的分析
       - Action: 识别关键的学习特征
       - Observation: 从学术历史中识别模式
       - Decision: 综合形成学习档案的建议

    3. LLM 集成：
       - 使用结构化提示，确保分析结果一致
       - 通过 messages 数组保持对话上下文
       - 通过 JSON 序列化方式处理原始档案数据

    4. 结果结构：
       返回分析结果的格式：
       - 可与其他代理的输出结合使用
       - 提供清晰的学习偏好见解
       - 包含可执行的具体建议
    """
    # 从 state 中提取学生档案数据
    profile = state["profile"]

    from ...prompts.templates import PROFILE_ANALYZER_PROMPT
    prompt = PROFILE_ANALYZER_PROMPT.format(json.dumps(profile, indent=2))

    # 初始化 llm 并生成分析结果
    from ...services.llm_service import OpenRouter
    llm = OpenRouter()
    response = await llm.agenerate([
        {"role": "user", "content": prompt}
    ])

    return {
        "results": {
            "profile_analysis": {
                "analysis": response
            }
        }
    }
