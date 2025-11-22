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
        for step in self.steps[-50:]:  # TODO: last 50 steps
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
                        lines.append(f"  [cyan]{thinking_line.strip()}[/]")
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
        
        lines = []
        for file_path, info in list(self.files.items())[-10:]:  # TODO: last 10 files
            action_colors = {
                "created": "green",
                "modified": "yellow",
                "read": "blue"
            }
            color = action_colors.get(info['action'], "white")
            
            lines.append(f"[{color}]● {info['action'].upper()}[/] [dim]{info['timestamp']}[/]")
            lines.append(f"[bold]{Path(file_path).name}[/]")
            lines.append(f"[dim]{file_path}[/]")
            
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


class HyperCodeTUI(App):
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
        width: 60%;
        border: solid $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 40%;
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
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit_or_interrupt", "Quit/Interrupt", priority=True),
        Binding("ctrl+c", "interrupt", "Interrupt", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.agent = None
        self.task_queue = deque()
        self.current_task = None
        self.task_running = False
        self.quit_pressed_time = None
        self.quit_threshold = 2.0  # TODO: seconds for double ctrl+Q
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="main-container"):
            # status bar
            yield Static("Ready | Queue: 0", id="status-bar")
            
            # main panels
            with Horizontal(id="panels"):
                with Vertical(id="left-panel"):
                    yield Label("Agent Steps", classes="panel-title")
                    with VerticalScroll():
                        yield StepDisplay(id="steps")
                
                with Vertical(id="right-panel"):
                    yield Label("File Changes", classes="panel-title")
                    with VerticalScroll():
                        yield FileDisplay(id="files")
            
            # input
            with Container(id="input-container"):
                yield Input(placeholder="Enter your task here...", id="task-input")
        
        yield Footer()
    
    def on_mount(self):
        """Called when app is mounted."""
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
            status_parts.append(f"Running: {self.current_task[:50]}...")
        else:
            status_parts.append("Ready")
        
        status_parts.append(f"Queue: {len(self.task_queue)}")
        
        self.query_one("#status-bar").update(" | ".join(status_parts))
    
    async def process_queue(self):
        self.task_running = True
        
        while self.task_queue:
            self.current_task = self.task_queue.popleft()
            self.update_status()
            
            # TODO: clear previous steps for new task
            self.query_one("#steps", StepDisplay).clear_steps()
            self.agent = ReActAgent(
                max_iterations=15,
                on_step=self.on_agent_step
            )
            
            try:
                result = await asyncio.to_thread(self.agent.run, self.current_task)
                if result['success']:
                    self.on_agent_step(
                        "complete",
                        f"✓ Task completed in {result['iterations']} iterations",
                        result
                    )
                else:
                    self.on_agent_step(
                        "complete",
                        f"⚠ Task incomplete after {result['iterations']} iterations",
                        result
                    )
            except Exception as e:
                self.on_agent_step("complete", f"✗ Error: {str(e)}", {"error": str(e)})
            
            self.current_task = None
            self.update_status()
        
        self.task_running = False
    
    def on_agent_step(self, phase: str, content: str, data: Dict[str, Any]):
        step_display = self.query_one("#steps", StepDisplay)
        step_display.add_step(phase, content, data)

        if phase == "observe" and "result" in data:
            result = data["result"]
            if isinstance(result, dict) and "path" in result:
                file_display = self.query_one("#files", FileDisplay)
                action = result.get("action", "modified")
                content_preview = result.get("content", "")
                file_display.add_file_change(result["path"], action, content_preview)
    
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
    app = HyperCodeTUI()
    app.run()


if __name__ == "__main__":
    main()
