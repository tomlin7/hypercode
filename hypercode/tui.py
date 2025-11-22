import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import deque

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Input, Static, Label
from textual.binding import Binding
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.console import Group
from rich.markdown import Markdown

from .react_agent import ReActAgent


class StepDisplay(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.steps: List[Dict[str, Any]] = []
    
    def add_step(self, phase: str, content: str, data: Dict[str, Any]):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # color coding -- phases
        phase_colors = {
            "think": "cyan",
            "act": "yellow",
            "observe": "green",
            "complete": "bright_green",
        }
        color = phase_colors.get(phase, "white")
        
        step = {
            "timestamp": timestamp,
            "phase": phase,
            "content": content,
            "data": data,
            "color": color
        }
        self.steps.append(step)
        self.update_display()
    
    def update_display(self):
        if not self.steps:
            self.update("No steps yet...")
            return
        
        lines = []
        current_iter = None
        
        for step in self.steps[-50:]:  # TODO: last 50 steps
            # if step.get('data', {}).get('iteration') and step['data']['iteration'] != current_iter:
            #     current_iter = step['data']['iteration']
            #     max_iter = step['data'].get('max_iterations', 15)
            #     lines.append(f"\n[bold white]{'═' * 20} Iteration {current_iter}/{max_iter} {'═' * 20}[/]")
            
            phase_label = f"[bold {step['color']}]{step['phase'].upper()}[/]"
            time_label = f"[dim]{step['timestamp']}[/]"
            
            # TODO: we'll show actual thinking
            if step['phase'] == 'think' and step['content'].startswith('Iteration'):
                continue
            
            lines.append(f"{time_label} {phase_label}")
            
            if step['phase'] == 'think' and step['content'] and not step['content'].startswith('No action'):
                thinking_lines = step['content'].split('\n')
                for thinking_line in thinking_lines:
                    if thinking_line.strip():
                        lines.append(f"  [italic cyan]{thinking_line.strip()}[/]")
            else:
                lines.append(f"  {step['content']}")
            
            if step['phase'] == 'act' and 'tool' in step['data']:
                tool_name = step['data']['tool']
                args = step['data'].get('args', {})
                arg_strs = []
                for k, v in args.items():
                    v_str = str(v)
                    if len(v_str) > 50:
                        v_str = v_str[:47] + "..."
                    arg_strs.append(f"{k}={v_str}")
                lines.append(f"  [dim]→ {tool_name}({', '.join(arg_strs)})[/]")
            
            if step['phase'] == 'observe' and 'result' in step['data']:
                result = step['data']['result']
                if isinstance(result, dict) and 'success' in result:
                    icon = "✓" if result['success'] else "✗"
                    color = "green" if result['success'] else "red"
                    lines.append(f"  [{color}]{icon}[/]")
            
            lines.append("") 
        self.update("\n".join(lines))
    
    def clear_steps(self):
        self.steps = []
        self.update_display()


class FileDisplay(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.files: Dict[str, str] = {}
    
    def add_file_change(self, file_path: str, action: str, content: str = ""):
        self.files[file_path] = {
            "action": action,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        self.update_display()
    
    def update_display(self):
        if not self.files:
            self.update("No file changes yet...")
            return
        
        file_icons = {
            ".py": "🐍",
            ".js": "📜",
            ".txt": "📝",
            ".md": "📋",
            ".json": "📊",
            ".html": "🌐",
            ".css": "🎨",
            ".yaml": "⚙️",
            ".yml": "⚙️",
            ".toml": "⚙️",
        }
        
        created_count = sum(1 for info in self.files.values() if info['action'] == 'created')
        modified_count = sum(1 for info in self.files.values() if info['action'] == 'modified')
        
        lines = []
        if self.files:
            lines.append(f"[bold]Modified: {modified_count} | Created: {created_count}[/]\n")
        
        for file_path, info in list(self.files.items())[-10:]:  # TODO: last 10 files
            action_colors = {
                "created": "green",
                "modified": "yellow",
                "read": "blue"
            }
            color = action_colors.get(info['action'], "white")
            
            ext = Path(file_path).suffix.lower()
            icon = file_icons.get(ext, "📄")
            
            lines.append(f"[{color}]● {info['action'].upper()}[/] [dim]{info['timestamp']}[/]")
            lines.append(f"{icon} [bold]{Path(file_path).name}[/]")
            lines.append(f"[dim]{file_path}[/]")
            
            try:
                if Path(file_path).exists():
                    size = Path(file_path).stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    lines.append(f"[dim]Size: {size_str}[/]")
            except:
                pass
            
            if info['content'] and len(info['content']) < 500:
                preview = info['content'][:200]
                if len(info['content']) > 200:
                    preview += "..."
                lines.append(f"[dim]{preview}[/]")
            
            lines.append("")
        
        self.update("\n".join(lines))
    
    def clear_files(self):
        self.files = {}
        self.update_display()


class StatisticsFooter(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total_iterations = 0
        self.tool_usage = {}
        self.total_tasks = 0
        self.completed_tasks = 0
        self.session_start = datetime.now()
    
    def update_stats(self, total_tasks: int, completed_tasks: int, failed_tasks: int, 
                     total_iterations: int, tool_usage: Dict[str, int]):
        self.total_tasks = total_tasks
        self.completed_tasks = completed_tasks
        self.failed_tasks = failed_tasks
        self.total_iterations = total_iterations
        self.tool_usage = tool_usage
        self.update_display()
    
    def update_display(self):
        parts = []
        
        # tasks stats
        if self.total_tasks > 0:
            success_rate = (self.completed_tasks / self.total_tasks) * 100 if self.total_tasks > 0 else 0
            parts.append(f"[bold]📊 Stats:[/] Tasks {self.completed_tasks}/{self.total_tasks} ({success_rate:.0f}%)")
        
        if self.total_iterations > 0:
            parts.append(f"Iterations: {self.total_iterations}")
        
        # tool usage
        if self.tool_usage:
            tool_strs = []
            for tool, count in sorted(self.tool_usage.items(), key=lambda x: x[1], reverse=True)[:3]:
                short_name = tool.replace("_", "")[:6]
                tool_strs.append(f"{short_name}({count})")
            if tool_strs:
                parts.append(f"Tools: {' '.join(tool_strs)}")
        
        # session time
        elapsed = (datetime.now() - self.session_start).total_seconds()
        mins, secs = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            time_str = f"{hours}h{mins}m"
        else:
            time_str = f"{mins}m{secs}s"
        parts.append(f"Session: {time_str}")
        
        self.update(" | ".join(parts) if parts else "No statistics yet...")


class HyperCode(App):
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
    }
    
    #panels {
        height: 1fr;
    }
    
    #left-panel {
        width: 3fr;
        padding: 2;
    }
    
    #right-panel {
        width: 1fr;
        border: solid $accent;
        padding: 1;
    }
    
    #input-container {
        height: auto;
        padding: 1;
        background: $boost;
    }
    
    Input {
        width: 100%;
    }
    
    #status-bar {
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    
    .panel-title {
        text-style: bold;
        color: $accent;
    }
    
    VerticalScroll {
        height: 1fr;
    }

    .hidden {
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit_or_interrupt", "Interrupt", priority=True),
        Binding("ctrl+q", "interrupt", "Quit/Interrupt", show=False),
        Binding("ctrl+b", "toggle_right", "Toggle Right Panel"),
    ]
    
    def __init__(self):
        super().__init__()
        self.agent = None
        self.task_queue = deque()
        self.current_task = None
        self.task_running = False
        self.quit_pressed_time = None
        self.quit_threshold = 2.0  # TODO: seconds for double ctrl+Q
        
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
        self.current_iteration = 0
        self.max_iterations = 15
        self.task_start_time = None
        self.session_start_time = datetime.now()
        self.tool_usage = {} 
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="main-container"):
            # status bar
            yield Static("Ready | Queue: 0", id="status-bar")
            
            # main panels
            with Horizontal(id="panels"):
                with Vertical(id="left-panel"):
                    yield Label("Chat", classes="panel-title")
                    with VerticalScroll(id="steps-scroll"): 
                        yield StepDisplay(id="steps")
                
                with Vertical(id="right-panel"):
                    yield Label("📁 File Changes", classes="panel-title")
                    with VerticalScroll():
                        yield FileDisplay(id="files")
            
            # input
            with Container(id="input-container"):
                yield Input(placeholder="Enter your task here...", id="task-input")
        
        yield Footer()
    
    def on_mount(self):
        self.query_one("#task-input").focus()
    
    async def on_input_submitted(self, event: Input.Submitted):
        """Handle task submission."""
        task = event.value.strip()
        if not task:
            return
        
        # queue first
        self.task_queue.append(task)
        self.update_status()
        
        event.input.value = ""
        
        # immediate execution if not already running
        if not self.task_running:
            asyncio.create_task(self.process_queue())
    
    def update_status(self):
        status_parts = []
        
        if self.current_task:
            task_display = self.current_task[:40] + "..." if len(self.current_task) > 40 else self.current_task
            status_parts.append(f"[bold cyan]Task:[/] {task_display}")
            
            if self.current_iteration > 0:
                status_parts.append(f"[yellow]Iter:[/] {self.current_iteration}/{self.max_iterations}")
            if self.task_start_time:
                elapsed = (datetime.now() - self.task_start_time).total_seconds()
                mins, secs = divmod(int(elapsed), 60)
                status_parts.append(f"[green]Time:[/] {mins:02d}:{secs:02d}")
        else:
            status_parts.append("[bold green]Ready[/]")
        
        if len(self.task_queue) > 0:
            status_parts.append(f"[magenta]Queue:[/] {len(self.task_queue)}")
        
        if self.total_tasks_completed > 0:
            status_parts.append(f"[green]Done:[/] {self.total_tasks_completed}")
        
        status_parts.append("[dim]gemini-2.5-flash[/]")
        
        self.query_one("#status-bar").update(" | ".join(status_parts))
    
    async def process_queue(self):
        self.task_running = True
        
        while self.task_queue:
            self.current_task = self.task_queue.popleft()
            self.current_iteration = 0
            self.task_start_time = datetime.now()
            self.update_status()
            
            # TODO: clear previous steps for new task
            self.query_one("#steps", StepDisplay).clear_steps()
            self.agent = ReActAgent(
                max_iterations=self.max_iterations,
                on_step=self.on_agent_step
            )
            
            try:
                result = await asyncio.to_thread(self.agent.run, self.current_task)
                if result['success']:
                    self.total_tasks_completed += 1
                    self.on_agent_step(
                        "complete",
                        f"✓ Task completed in {result['iterations']} iterations",
                        result
                    )
                else:
                    self.total_tasks_failed += 1
                    self.on_agent_step(
                        "complete",
                        f"⚠ Task incomplete after {result['iterations']} iterations",
                        result
                    )
            except Exception as e:
                self.total_tasks_failed += 1
                self.on_agent_step("complete", f"✗ Error: {str(e)}", {"error": str(e)})
            
            self.current_task = None
            self.current_iteration = 0
            self.task_start_time = None
            self.update_status()
        
        self.task_running = False
    
    def on_agent_step(self, phase: str, content: str, data: Dict[str, Any]):
        if "iteration" in data and data["iteration"] != self.current_iteration:
            self.current_iteration = data["iteration"]
            self.update_status()
        
        step_display = self.query_one("#steps", StepDisplay)
        step_display.add_step(phase, content, data)
        
        self.query_one("#steps-scroll").scroll_end(animate=True)
        if phase == "act" and "tool" in data:
            tool_name = data["tool"]
            self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1

        if phase == "observe" and "result" in data:
            result = data["result"]
            if isinstance(result, dict) and "path" in result:
                file_display = self.query_one("#files", FileDisplay)
                action = result.get("action", "modified")
                content_preview = result.get("content", "")
                file_display.add_file_change(result["path"], action, content_preview)

    def action_toggle_right(self):
        self.query_one("#right-panel").toggle_class("hidden")
    
    def action_quit_or_interrupt(self):
        current_time = datetime.now().timestamp()
        
        if self.quit_pressed_time and (current_time - self.quit_pressed_time) < self.quit_threshold:
            # double q - quit app
            self.exit()
        else:
            # single q - interrupt current task
            self.quit_pressed_time = current_time
            
            if self.task_running:
                self.task_queue.clear()
                self.current_task = None
                self.task_running = False
                self.on_agent_step("complete", "⚠ Task interrupted by user", {})
                self.update_status()
                self.notify("Task interrupted. Press Ctrl+Q again to exit.")
            else:
                self.notify("Press Ctrl+Q again within 2s to exit.")
    
    def action_interrupt(self):
        # single c - quit app
        if self.task_running:
            self.task_queue.clear()
            self.current_task = None
            self.task_running = False
            self.on_agent_step("complete", "⚠ Task interrupted by user", {})
            self.update_status()


def main():
    app = HyperCode()
    app.run()


if __name__ == "__main__":
    main()
