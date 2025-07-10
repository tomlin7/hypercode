import json
import operator
import re
from typing import Annotated, List, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_node import ToolNode

from hypercode.agents.coding_agent import coding_agent
from hypercode.agents.debugging_agent import debugging_agent
from hypercode.agents.orchestrator import planner
from hypercode.agents.testing_agent import testing_agent
from hypercode.agents.tool_agent import tool_agent
from hypercode.tools import tools

SENSITIVE_TOOLS = ["write_file", "run_cli_command", "move_file", "copy_file", "rename_file", "create_folder"]

class AgentState(TypedDict):
    request: str
    plan: List[dict]
    response: str
    sender: str
    tool_calls: list
    step: int
    needs_confirmation: bool
    pending_tool_calls: list
    user_confirmation: bool
    test_results: str
    debug_info: str
    last_response: str 


tool_node = ToolNode(tools)

def call_planner(state):
    print("--- Calling Planner ---")
    response = planner.invoke({"request": state["request"]})
    print(f"Planner raw response: {response.content}")
    json_match = re.search(r"```json\n([\s\S]*?)\n```", response.content)
    if json_match:
        plan = json.loads(json_match.group(1))
    else:
        raise ValueError(f"Could not extract JSON from planner response: {response.content}")
    print(f"Plan: {plan}")
    return {"plan": plan, "step": 0, "last_response": ""}

def execute_step(state):
    print(f"--- Executing Step {state['step']} ---")
    step_data = state["plan"][state["step"]]
    agent = step_data["agent"]
    instruction = step_data["instruction"]

    print(f"Delegating to {agent} with instruction: {instruction}")

    if agent == "coding_agent":
        response = coding_agent.invoke({"request": instruction})
        return {"response": response.content, "sender": "coding_agent", "step": state["step"] + 1, "last_response": response.content}
    elif agent == "tool_agent":
        
        if "write" in instruction.lower() and state["last_response"]:
            instruction = f"{instruction}\nContent: {state["last_response"]}"
        response = tool_agent.invoke({"request": instruction})
        
        if response.tool_calls:
            return {"tool_calls": response.tool_calls, "sender": "tool_agent", "step": state["step"], "last_response": response.content}
        else:
            
            return {"response": response.content, "sender": "tool_agent", "step": state["step"] + 1, "last_response": response.content}

def call_testing_agent(state):
    print("--- Calling Testing Agent ---")
    
    
    step_data = state["plan"][state["step"]]
    instruction = step_data["instruction"]
    
    
    if state["last_response"] and ("test" in instruction.lower() or "verify" in instruction.lower()):
        instruction = f"{instruction}\nCode to test: {state["last_response"]}"

    response = testing_agent.invoke({"request": instruction})
    
    return {"test_results": response.content, "sender": "testing_agent", "step": state["step"] + 1, "last_response": response.content}

def call_debugging_agent(state):
    print("--- Calling Debugging Agent ---")
    
    
    response = debugging_agent.invoke({"request": f"Test results:\n{state['test_results']}\nOriginal request: {state['request']}"})
    return {"debug_info": response.content, "sender": "debugging_agent", "step": state["step"] + 1, "last_response": response.content}

def check_sensitive_tools(state):
    print("--- Checking Sensitive Tools ---")
    sensitive_calls = []
    non_sensitive_calls = []
    for tool_call in state["tool_calls"]:
        if tool_call['name'] in SENSITIVE_TOOLS:
            sensitive_calls.append(tool_call)
        else:
            non_sensitive_calls.append(tool_call)

    if sensitive_calls:
        print(f"Sensitive tool calls detected: {sensitive_calls}")
        
        return {"needs_confirmation": True, "pending_tool_calls": sensitive_calls, "tool_calls": non_sensitive_calls, "last_response": state["last_response"], "sender": "check_sensitive_tools", "step": state["step"]}
    else:
        print("No sensitive tool calls detected.")
        return {"needs_confirmation": False, "tool_calls": non_sensitive_calls, "last_response": state["last_response"], "sender": "check_sensitive_tools", "step": state["step"]}

def process_confirmation(state):
    print("--- Processing User Confirmation ---")
    if state["user_confirmation"]:
        print("User confirmed. Proceeding with sensitive tool calls.")
        return {"tool_calls": state["pending_tool_calls"], "needs_confirmation": False, "pending_tool_calls": [], "last_response": state["last_response"], "step": state["step"]}
    else:
        print("User denied. Cancelling sensitive tool calls.")
        return {"tool_calls": [], "needs_confirmation": False, "pending_tool_calls": [], "step": state["step"] + 1, "last_response": state["last_response"]} 

def call_tool_node(state):
    print("--- Calling Tool Node ---")
    responses = tool_node.invoke(state["tool_calls"])
    print(f"Tool Responses: {responses}")
    return {"response": responses, "sender": "tool_node", "step": state["step"] + 1, "last_response": str(responses)}

def should_continue(state):
    print(f"--- Checking if should continue (Current step: {state['step']}, Total steps: {len(state['plan'])}) ---")
    if state["step"] < len(state["plan"]):
        return "continue"
    else:
        return "end"


workflow = StateGraph(AgentState)

workflow.add_node("planner", call_planner)
workflow.add_node("execute_step", execute_step)
workflow.add_node("check_sensitive_tools", check_sensitive_tools)
workflow.add_node("process_confirmation", process_confirmation) 
workflow.add_node("tool_node", call_tool_node)
workflow.add_node("testing_agent", call_testing_agent)
workflow.add_node("debugging_agent", call_debugging_agent)


workflow.set_entry_point("planner")
workflow.add_edge("planner", "execute_step")


workflow.add_conditional_edges(
    "execute_step",
    lambda state: (
        "check_sensitive_tools" if state.get("tool_calls") else
        "testing_agent" if state["plan"][state["step"] - 1]["agent"] == "coding_agent" and state["step"] < len(state["plan"]) and state["plan"][state["step"]]["agent"] == "testing_agent" else
        should_continue(state)
    ),
    {
        "check_sensitive_tools": "check_sensitive_tools",
        "testing_agent": "testing_agent",
        "continue": "execute_step",
        "end": END,
    },
)


workflow.add_conditional_edges(
    "check_sensitive_tools",
    lambda state: "process_confirmation" if state.get("needs_confirmation") else "tool_node",
    {
        "process_confirmation": "process_confirmation",
        "tool_node": "tool_node",
    },
)


workflow.add_conditional_edges(
    "process_confirmation",
    lambda state: "tool_node" if state.get("user_confirmation") else "execute_step", 
    {
        "tool_node": "tool_node",
        "execute_step": "execute_step", 
    },
)


workflow.add_edge("tool_node", "execute_step")

workflow.add_conditional_edges(
    "testing_agent",
    lambda state: (
        "debugging_agent" if "FAIL" in state.get("test_results", "") else
        should_continue(state)
    ),
    {
        "debugging_agent": "debugging_agent",
        "continue": "execute_step",
        "end": END,
    },
)


workflow.add_edge("debugging_agent", "execute_step")

app = workflow.compile()
