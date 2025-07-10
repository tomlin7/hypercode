
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a testing agent. Your job is to write and execute tests for the given code. You will be given a request from the user, and you will need to write the tests and execute them."),
        ("human", "{request}"),
    ]
)

testing_agent = prompt | llm
