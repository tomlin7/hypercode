import sys
from .react_agent import ReActAgent


def print_step(phase: str, content: str, data: dict):
    phase_symbols = {
        "think": "💭",
        "act": "⚡",
        "observe": "👁️",
        "complete": "✅"
    }
    symbol = phase_symbols.get(phase, "•")
    print(f"\n{symbol} [{phase.upper()}] {content}")
    
    if phase == "act" and "tool" in data:
        print(f"   Tool: {data['tool']}")
        if "args" in data:
            for key, value in data["args"].items():
                print(f"   - {key}: {value}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m hypercode <task>")
        print("   or: python -m hypercode.tui  (for TUI mode)")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    print(f"🚀 Starting task: {task}\n")
    
    agent = ReActAgent(on_step=print_step)
    result = agent.run(task)
    
    print("\n" + "="*50)
    if result["success"]:
        print(f"✅ Task completed in {result['iterations']} iterations")
    else:
        print(f"⚠️  Task incomplete after {result['iterations']} iterations")
    print("="*50)


if __name__ == "__main__":
    main()
