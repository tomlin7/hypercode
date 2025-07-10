import argparse
import os

from dotenv import load_dotenv

load_dotenv()


if not os.environ.get("GOOGLE_API_KEY"):
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set it in your .env file or as a system environment variable.")
    exit(1)

from hypercode.graph import app


def main():
    """
    Main function for the HyperCode CLI.
    """
    parser = argparse.ArgumentParser(description="A Gemini-like code assistant.")
    parser.add_argument("request", type=str, help="The request to process.")
    args = parser.parse_args()
    
    current_state = {"request": args.request}
    
    while True:
        user_confirmed = None
        
        for output in app.stream(current_state):
            for key, value in output.items():
                if key == "check_sensitive_tools" and value.get("needs_confirmation"):
                    print("\n--- Confirmation Required ---")
                    print("The agent wants to perform the following actions:")
                    for call in value["pending_tool_calls"]:
                        print(f"  - Tool: {call['name']}, Args: {call['args']}")
                    
                    confirmation = input("Do you want to proceed? (y/n): ").lower()
                    user_confirmed = (confirmation == 'y')
                    current_state = value 
                    break 
                elif key != "__end__":
                    print(f"Output from node '{key}':")
                    print("---")
                    print(value)
                    print("\n")
            
            if user_confirmed is not None:
                current_state["user_confirmation"] = user_confirmed
                current_state["needs_confirmation"] = False 
            else:
                break

if __name__ == "__main__":
    main()