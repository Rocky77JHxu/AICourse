from typing import Annotated, List, TypeVar, Dict, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


T = TypeVar('T')

def dict_reducer(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归合并两个字典
    
    Example:
    dict1 = {"a": {"x": 1}, "b": 2}
    dict2 = {"a": {"y": 2}, "c": 3}
    result = {"a": {"x": 1, "y": 2}, "b": 2, "c": 3}
    """
    merged = dict1.copy()
    for key, value in dict2.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = dict_reducer(merged[key], value)
        else:
            merged[key] = value
    return merged

class AcademicState(TypedDict):
    """学术研究状态"""
    messages: Annotated[List[BaseMessage], add_messages]    # 对话历史
    profile: Annotated[Dict, dict_reducer]                  # 学生信息
    calendar: Annotated[Dict, dict_reducer]                 # 日程表
    tasks: Annotated[Dict, dict_reducer]                    # 待办清单
    results: Annotated[Dict[str, Any], dict_reducer]        # 最终输出
    