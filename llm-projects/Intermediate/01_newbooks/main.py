import json
import re
import asyncio
from pathlib import Path
from rich.panel import Panel
from rich.markdown import Markdown
from rich.console import Console
from IPython.display import display, Image
from langchain_core.messages import HumanMessage
from src.atlas.services.llm_service import OpenRouter
from src.atlas.services.data_manager import DataManager
from src.atlas.core.orchestration import create_agents_graph


async def run_all_system(profile_json: str, calendar_json: str, task_json: str):
    """运行整个学业辅助系统，并优化输出处理。

    这是 ATLAS（Academic Task Learning Agent System，学业任务学习智能体系统）
    的主入口点。
    它负责初始化、用户交互、工作流执行，以及结果的展示。

    参数：
        profile_json: 包含学生档案数据的 JSON 字符串
        calendar_json: 包含课程表/日程数据的 JSON 字符串
        task_json: 包含学业任务数据的 JSON 字符串

    返回：
        Tuple[Dict, Dict]: 协调器输出与最终状态；出错时返回 (None, None)

    特性：
        - 具有状态实时更新的丰富控制台界面
        - 异步流式执行工作流步骤
        - 全面的错误处理
        - 实时进度反馈
    """
    try:
        # 初始化富文本控制台（增强 UI）
        console = Console()

        # 显示欢迎横幅
        console.print("\n[bold magenta]🎓 ATLAS: Academic Task Learning Agent System[/bold magenta]")
        console.print("[italic blue]正在初始化学业支持系统...[/italic blue]\n")

        # 初始化核心系统组件
        # NeMoLLaMa 是语言模型底层
        llm = OpenRouter()

        # DataManager 负责所有数据的加载与访问
        dm = DataManager()
        dm.load_data(profile_json, calendar_json, task_json)

        # 获取用户请求
        console.print("[bold green]请输入你的学业请求：[/bold green]")
        user_input = str(input())
        console.print(f"\n[dim italic]正在处理请求: {user_input}[/dim italic]\n")

        # 构建初始状态对象
        # 内含智能体运行所需的全部上下文
        state = {
            "messages": [HumanMessage(content=user_input)],  # 用户请求
            "profile": dm.get_student_profile("student_123"),  # 学生信息
            "calendar": {"events": dm.get_upcoming_events()},  # 日程安排
            "tasks": {"tasks": dm.get_active_tasks()},        # 当前任务
            "results": {}                                     # 存储智能体输出
        }

        # 初始化智能体编排的工作流图
        graph = create_agents_graph(llm)

        console.print("[bold cyan]系统已初始化，正在处理请求...[/bold cyan]\n")
        # 此处可添加可视化
        console.print("[bold cyan]工作流图结构：[/bold cyan]\n")
        display(Image(graph.get_graph().draw_mermaid_png()))

        # 跟踪关键状态变化
        coordinator_output = None  # 初始分析结果
        final_state = None         # 最终执行结果

        # 在显示实时状态的同时处理工作流
        with console.status("[bold green]Processing...", spinner="dots") as status:
            # 按步骤异步流式执行工作流
            async for step in graph.astream(state):
                # 当有协调器分析结果时进行记录
                if "coordinator_analysis" in step.get("results", {}):
                    coordinator_output = step
                    analysis = coordinator_output["results"]["coordinator_analysis"]

                    # 输出所选定的智能体，提升过程透明度
                    console.print("\n[bold cyan]已选择的智能体：[/bold cyan]")
                    for agent in analysis.get("required_agents", []):
                        console.print(f"• {agent}")

                # 捕获最终执行状态
                if "execute" in step:
                    final_state = step

        # # 如果有最终结果，则使用格式化输出方式展示
        # if final_state:
        #     display_formatted_output(final_state)
        # 替换为更简单的控制台输出：
        if final_state:
            agent_outputs = final_state.get("execute", {}).get("results", {}).get("agent_outputs", {})

            # 逐个智能体输出结果
            for agent, output in agent_outputs.items():
                console.print(f"\n[bold cyan]{agent.upper()} 输出：[/bold cyan]")

                # 处理嵌套字典结果
                if isinstance(output, dict):
                    for key, value in output.items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if subvalue and isinstance(subvalue, str):
                                    console.print(subvalue.strip())
                        elif value and isinstance(value, str):
                            console.print(value.strip())
                # 处理直接的字符串结果
                elif isinstance(output, str):
                    console.print(output.strip())

        # 显示已完成提示
        console.print("\n[bold green]✓[/bold green] [bold]任务完成！[/bold]")
        return coordinator_output, final_state

    except Exception as e:
        # 全面的错误处理并输出堆栈追踪
        console.print(f"\n[bold red]系统错误：[/bold red] {str(e)}")
        console.print("[yellow]堆栈追踪：[/yellow]")
        import traceback
        console.print(traceback.format_exc())
        return None, None


async def load_json_and_test():
    """从本地文件系统加载 JSON 文件并运行学业辅助系统。"""
    console = Console()
    console.print("[bold magenta]学业助手测试环境[/bold magenta]")
    console.print("-" * 50)
    console.print("\n正在从本地文件系统加载 JSON 文件...")

    try:
        # 定义测试数据文件路径
        current_dir = Path(".")
        data_files = {
            'profile': current_dir / "profile_student_123.json",
            'calendar': current_dir / "calendar_student_123.json", 
            'task': current_dir / "task_student_123.json"
        }

        # 检查文件是否存在
        missing_files = []
        for file_type, file_path in data_files.items():
            if not file_path.exists():
                missing_files.append(str(file_path))

        if missing_files:
            console.print(f"[bold red]错误：缺少以下必需文件:[/bold red]")
            for file in missing_files:
                console.print(f"- {file}")
            console.print(f"\n[yellow]请确保这些JSON文件存在于当前目录中。[/yellow]")
            return None, None

        console.print("\n[green]找到的文件：[/green]")
        for file_type, file_path in data_files.items():
            console.print(f"- {file_type}: {file_path.name}")

        # 读取 JSON 文件内容
        json_contents = {}
        for file_type, file_path in data_files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_contents[file_type] = f.read()
            except Exception as e:
                console.print(f"[bold red]读取 {file_type} 文件时出错:[/bold red] {str(e)}")
                return None, None

        console.print("\n[bold cyan]开始运行学业辅助工作流...[/bold cyan]")
        
        # 运行系统
        coordinator_output, output = await run_all_system(
            json_contents['profile'],
            json_contents['calendar'],
            json_contents['task']
        )
        return coordinator_output, output

    except Exception as e:
        console.print(f"\n[bold red]错误：[/bold red]{str(e)}")
        console.print("[yellow]详细错误信息：[/yellow]")
        import traceback
        console.print(traceback.format_exc())
        return None, None


async def main():
    """主函数：运行ATLAS学业辅助系统"""
    try:
        # 运行系统
        coordinator_output, output = await load_json_and_test()
        
        if output is None:
            return
            
        # 格式化输出结果
        console = Console()
        
        if output and hasattr(output, 'get'):
            # 检查是否有执行结果
            execute_results = output.get("execute", {})
            if execute_results and "results" in execute_results:
                agent_outputs = execute_results["results"].get("agent_outputs", {})
                
                console.print("\n[bold green]✨ 系统执行完成！[/bold green]")
                console.print("\n[bold cyan]智能体输出结果：[/bold cyan]")
                
                # 显示每个智能体的输出
                for agent_name, agent_result in agent_outputs.items():
                    console.print(f"\n[bold yellow]📋 {agent_name.upper()}:[/bold yellow]")
                    
                    if isinstance(agent_result, dict):
                        for key, value in agent_result.items():
                            if isinstance(value, dict) and "plan" in value:
                                # 格式化计划输出
                                plan_content = value["plan"]
                                if isinstance(plan_content, str):
                                    md = Markdown(plan_content)
                                    panel = Panel(md, title=f"{agent_name} 计划", border_style="blue")
                                    console.print(panel)
                            elif isinstance(value, dict) and "notes" in value:
                                # 格式化笔记输出
                                notes_content = value["notes"]
                                if isinstance(notes_content, str):
                                    md = Markdown(notes_content)
                                    panel = Panel(md, title=f"{agent_name} 笔记", border_style="green")
                                    console.print(panel)
                            elif isinstance(value, dict) and "advice" in value:
                                # 格式化建议输出
                                advice_content = value["advice"]
                                if isinstance(advice_content, str):
                                    md = Markdown(advice_content)
                                    panel = Panel(md, title=f"{agent_name} 建议", border_style="yellow")
                                    console.print(panel)
                            elif isinstance(value, str):
                                console.print(f"  {value}")
                    elif isinstance(agent_result, str):
                        console.print(f"  {agent_result}")
            else:
                console.print("[yellow]没有找到智能体执行结果[/yellow]")
        else:
            console.print("[yellow]系统没有返回有效输出[/yellow]")
            
    except Exception as e:
        console = Console()
        console.print(f"\n[bold red]主函数执行出错：[/bold red]{str(e)}")
        console.print("[yellow]详细错误信息：[/yellow]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    """程序入口点"""
    asyncio.run(main())