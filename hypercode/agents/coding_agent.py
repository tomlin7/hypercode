
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a coding agent. Your job is to write code to complete a task. You will be given a request from the user, and you will need to write the code to complete the task."),
        ("human", "{request}"),
    ]
)

coding_agent = prompt | llm
