import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from hypercode.tools import tools

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

llm_with_tools = llm.bind_tools(tools)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a tool agent. Your job is to use tools to complete a task. You will be given a request from the user, and you will need to use the available tools to complete the task. If the instruction includes 'Content:', assume it's a file write operation and use the 'write_file' tool with the provided content."),
        ("human", "{request}"),
    ]
)

tool_agent = prompt | llm_with_tools