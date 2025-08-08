from state import AcademicState

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
    pass