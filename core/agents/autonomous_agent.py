import os
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from dotenv import load_dotenv

# Import system tools
try:
    from core.tools.system_integrator import create_system_tools
except ImportError:
    # Handle relative import when running as script
    from tools.system_integrator import create_system_tools

load_dotenv()

class AutonomousAgent:
    """
    Enterprise-grade autonomous agent implementation using LangChain.
    Uses ReAct logic through OpenAI Functions for reliable tool execution.
    """
    
    def __init__(
        self, 
        model_name: str = "gpt-4-turbo-preview", 
        temperature: float = 0.0,
        tools: Optional[List[Tool]] = None
    ):
        self.llm = ChatOpenAI(
            model=model_name, 
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = tools or create_system_tools()
        self.agent_executor = self._initialize_agent()

    def _initialize_agent(self) -> AgentExecutor:
        """Sets up the agent with a professional system prompt and toolset."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an Intelligent Automation Agent. 
            Your goal is to execute operational tasks with high precision and reasoning.
            You have access to a set of professional tools for file system, database, and API interactions.
            Always provide a logical breakdown of your steps before executing them.
            If a task requires multiple steps, execute them sequentially and verify the outcome of each step.
            Always handle errors gracefully and suggest alternatives if a tool fails.
            """),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=10
        )

    def run(self, task: str) -> str:
        """Executes a given task and returns the final response."""
        try:
            response = self.agent_executor.invoke({"input": task})
            return response.get("output", "No output generated.")
        except Exception as e:
            return f"Error executing task: {str(e)}"

if __name__ == "__main__":
    # Example usage
    agent = AutonomousAgent()
    # result = agent.run("Create a report.txt with a summary of the current directory.")
    # print(result)
