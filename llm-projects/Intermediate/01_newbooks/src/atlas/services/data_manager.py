import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List

class DataManager:
    
    def __init__(self):
        """
        初始化数据存储容器
        在通过 `load_data()` 显式加载之前，所有数据源都以 None 开始。
        """
        self.profile_data = None
        self.calendar_data = None
        self.task_data = None

    def load_data(self, profile_json: str, calendar_json: str, task_json: str):
        """
        同时加载和解析多个 JSON 数据源

        Args:
            profile_json (str): JSON string containing user profile information
            calendar_json (str): JSON string containing calendar events
            task_json (str): JSON string containing task/todo items
        
        Note: 该方法需要有效的 JSON 字符串，任何解析异常都会向上抛出。
        """
        self.profile_data = json.loads(profile_json)
        self.calendar_data = json.loads(calendar_json)
        self.task_data = json.loads(task_json)
    
    def get_student_profile(self, student_id: str) -> Dict:
        """
        获取学生个人资料

        Args:
            student_id (str): 唯一的学生 ID
        
        Returns:
            Dict: 学生的个人资料，未找到则为 None
        
        Implementation Note:
            使用生成器表达式和 `next()` 函数进行高效搜索配置文件，尽可能避免完整列表迭代。
        """
        if self.profile_data:
            return next((p for p in self.profile_data["profiles"]
                        if p["id"] == student_id), None)
        return None
    
    def parse_datetime(self, dt_str: str) -> datetime:
        """
        智能日期解析器，支持多种日期格式并确保 UTC 时区

        Args:
            dt_str (str): 日期时间字符串
        
        Returns:
            datetime: 解析后的日期时间对象
        
        Implementation Note:
            处理时区感知和朴素日期字符串:
            1. 首先尝试使用时区信息进行解析；
            2. 如果没有指定时区，则返回到假设 UTC
        """
        try:
            # First attempt:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except ValueError:
            # Fallback:
            dt = datetime.fromisoformat(dt_str)
            return dt.replace(tzinfo=timezone.utc)
    
    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """
        智能过滤和检索指定时间范围内的事件

        Args:
            days (int): 指定时间范围的天数
        
        Implementation Note:
            - 使用 UTC 时间戳进行一致的时区处理
            - 实现对畸形事件数据的错误处理
            - 仅包含在指定时间段内未来事件
        """
        if not self.calendar_data:
            return []
        
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=days)
        
        events = []
        for event in self.calendar_data.get("events", []):
            try:
                start_time = self.parse_datetime(event["start"]["dateTime"])
                
                if now <= start_time <= future:
                    events.append(event)
            except (KeyError, ValueError) as e:
                print(f"Warning: Could not process event due to {str(e)}")
                continue
                
        return events
    
    def get_active_tasks(self) -> List[Dict]:
        """
        检索并筛选出活跃任务，用解析出的日期时间信息对其进行丰富。

        Returns:
            List[Dict]: 活跃任务列表
        
        Implementation Note:
            - 任务筛选器适用于以下任务:
                1. 未完成（`needsAction` 状态）
                2. 未来待办事项
            - 为任务对象添加解析后的日期时间信息
            - 实现对格式错误的任务数据的稳健处理
        """
        if not self.task_data:
            return []
        
        now = datetime.now(timezone.utc)
        active_tasks = []

        for task in self.task_data.get("tasks", []):
            try:
                due_date = self.parse_datetime(task["due"])
                if task["status"] == "needsAction" and due_date > now:
                    # 用解析过的日期时间替换原始字符串
                    task["due_datetime"] = due_date
                    active_tasks.append(task)
            except (KeyError, ValueError) as e:
                print(f"Warning: Could not process task due to {str(e)}")
                continue
        
        return active_tasks
