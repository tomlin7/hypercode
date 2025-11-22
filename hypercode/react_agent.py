import os
from typing import Any, Callable, Dict, List, Optional

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from .tools import ALL_TOOLS

load_dotenv()


class ReActAgent:
    def __init__(
        self,
        max_iterations: int = 15,
        on_step: Optional[Callable[[str, str, Any], None]] = None
    ):
        self.max_iterations = max_iterations
        self.on_step = on_step or (lambda *args: None)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self.tools_map = {tool.name: tool for tool in ALL_TOOLS}
        self.messages: List[Any] = []
        
    def _create_system_prompt(self) -> str:
        return """You are a helpful coding assistant that follows the ReAct (Reasoning and Acting) pattern.

For each task, you will:
1. THINK: Analyze the current situation and decide what action to take next
2. ACT: Use tools to perform actions (read files, write code, run commands, etc.)
3. OBSERVE: Check the results of your actions and determine if the task is complete

Available tools:
- read_file: Read the contents of a file
- write_file: Write or create a file with content
- create_folder: Create a directory
- run_command: Execute a shell command

CRITICAL GUIDELINES:
- ALWAYS provide your reasoning as text BEFORE calling any tools
- Explain what you're thinking and why you're choosing specific actions
- Your text response should describe your plan before you execute it
- After observing tool results, explain what you learned and what to do next
- When writing code, make it clean, well-documented, and functional
- Complete the task efficiently - don't take unnecessary actions
- When the task is complete, clearly state "TASK COMPLETE" in your response

Example format:
"I need to create a file with specific content. I'll use the write_file tool to create test.txt with the message."
[Then call write_file tool]

Remember: Think out loud, explain your reasoning, then act."""

    def run(self, task: str) -> Dict[str, Any]:
        self.messages = [
            SystemMessage(content=self._create_system_prompt()),
            HumanMessage(content=f"Task: {task}")
        ]
        
        iteration = 0
        task_complete = False
        
        while iteration < self.max_iterations and not task_complete:
            iteration += 1
            
            # THINK
            self.on_step("think", f"Iteration {iteration}", {"iteration": iteration})
            
            response = self.llm_with_tools.invoke(self.messages)
            self.messages.append(response)
            
            thinking = response.content if response.content else ""
            if thinking.strip():
                self.on_step("think", thinking, {"iteration": iteration, "has_content": True})
            
            if response.tool_calls:
                tool_names = [tc["name"] for tc in response.tool_calls]
                self.on_step("think", f"Planning to use tools: {', '.join(tool_names)}", {
                    "iteration": iteration,
                    "planned_tools": tool_names
                })
            
            if "TASK COMPLETE" in thinking.upper():
                task_complete = True
                self.on_step("complete", thinking, {"iteration": iteration})
                break
            
            # ACT
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call["id"]
                    
                    self.on_step(
                        "act",
                        f"Using {tool_name}",
                        {"tool": tool_name, "args": tool_args}
                    )
                    
                    if tool_name in self.tools_map:
                        tool = self.tools_map[tool_name]
                        try:
                            result = tool.invoke(tool_args)
                            
                            # OBSERVE
                            self.on_step(
                                "observe",
                                f"Result from {tool_name}",
                                {"tool": tool_name, "result": result}
                            )
                            
                            self.messages.append(
                                ToolMessage(
                                    content=str(result),
                                    tool_call_id=tool_id
                                )
                            )
                        except Exception as e:
                            error_msg = f"Error executing {tool_name}: {str(e)}"
                            self.on_step("observe", error_msg, {"error": str(e)})
                            self.messages.append(
                                ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_id
                                )
                            )
                    else:
                        error_msg = f"Unknown tool: {tool_name}"
                        self.on_step("observe", error_msg, {"error": error_msg})
                        self.messages.append(
                            ToolMessage(
                                content=error_msg,
                                tool_call_id=tool_id
                            )
                        )
            else:
                # no toolcalls, but not complete
                if not task_complete:
                    self.on_step(
                        "think",
                        "No action taken, continuing...",
                        {"iteration": iteration}
                    )
        
        # final result
        if task_complete:
            return {
                "success": True,
                "result": "Task completed successfully",
                "iterations": iteration,
                "final_message": thinking
            }
        else:
            return {
                "success": False,
                "result": "Max iterations reached without completion",
                "iterations": iteration
            }
