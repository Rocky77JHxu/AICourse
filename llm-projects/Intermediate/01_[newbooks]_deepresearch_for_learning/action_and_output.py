from pydantic import BaseModel, Field
from typing import Optional, Dict

class AgentAction(BaseModel):
    """
    Agent 的行为决策模型

    Attributes:
        action (str): 要采取的具体操作 (e.g., "search_calendar", "analyze_tasks", ... )
        thought (str): 行动决策的背后推理过程
        tool (Optional[str]): 行动中所需的特殊工具
        action_input (Optional[Dict]): 行动的输入参数
    
    Example:
        >>> action = AgentAction(
        ...     action="search_calendar",
        ...     thought="Need to check schedule conflicts",
        ...     tool="calendar_search",
        ...     action_input={"date_range": "next_week"}
        ... )
    """
    action: str = Field(..., description="要采取的具体操作")
    thought: str = Field(..., description="行动决策的背后推理过程")
    tool: Optional[str] = Field(None, description="行动中所需的特殊工具")
    action_input: Optional[Dict] = Field(None, description="行动的输入参数")


class AgentOutput(BaseModel):
    """
    Agent 行动输出模型

    Attributes:
        observation (str): The result or observation from executing the action
        output (Dict): Structured output data from the action
    
    Example:
        >>> output = AgentOutput(
        ...     observation="Found 3 free time slots next week",
        ...     output={
        ...         "free_slots": ["Mon 2PM", "Wed 10AM", "Fri 3PM"],
        ...         "conflicts": []
        ...     }
        ... )
    """
    observation: str = Field(..., description="行动的观察结果")
    output: Dict = Field(..., description="行动的结构化输出数据")