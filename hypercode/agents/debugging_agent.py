
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a debugging agent. Your job is to analyze test failures and suggest fixes. You will be given a test failure, and you will need to suggest a fix."),
        ("human", "{request}"),
    ]
)

debugging_agent = prompt | llm
