# quick test sample
from hypercode.react_agent import ReActAgent


def print_step(phase, content, data):
    print(f"\n[{phase.upper()}] {content}")
    if phase == "act" and "tool" in data:
        print(f"  Tool: {data['tool']}")
        print(f"  Args: {data.get('args', {})}")
    if phase == "observe" and "result" in data:
        print(f"  Result: {data['result']}")


print("Testing ReAct Agent...")
print("=" * 50)

agent = ReActAgent(max_iterations=10, on_step=print_step)
result = agent.run("Create a file called test_hello.txt with the content 'Hello from ReAct agent!'")

print("\n" + "=" * 50)
print(f"Success: {result['success']}")
print(f"Iterations: {result['iterations']}")
print(f"Result: {result['result']}")
