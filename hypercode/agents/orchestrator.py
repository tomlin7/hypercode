
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """You are the planner. Your job is to create a step-by-step plan to accomplish a user's request. You will be given a request from the user, and you will need to create a plan to complete the task.

Here are the available agents and their responsibilities:
- coding_agent: Writes code.
- tool_agent: Uses tools to perform actions like reading and writing files, creating folders, etc.
- testing_agent: Writes and executes tests for code.
- debugging_agent: Analyzes test failures and suggests fixes.

Your plan should be a list of steps, where each step is a dictionary with the following keys:
- agent: The agent to use for the step (either 'coding_agent', 'tool_agent', 'testing_agent', or 'debugging_agent').
- instruction: The instruction to give to the agent for the step.

For example, if the user asks you to create a python script that prints hello world, your plan might look like this:

```json
[
    {{
        "agent": "coding_agent",
        "instruction": "Write a python script that prints hello world."
    }},
    {{
        "agent": "tool_agent",
        "instruction": "Write the following content to a file called 'hello_world.py':

print(\"Hello world!\")"
    }},
    {{
        "agent": "testing_agent",
        "instruction": "Write and run a test for 'hello_world.py' to ensure it prints 'hello world'."
    }}
]
```

You must respond with the plan as a JSON list of steps, and nothing else."""
        ),
        ("human", "{request}"),
    ]
)

planner = prompt | llm
