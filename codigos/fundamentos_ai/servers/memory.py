import asyncio

from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic

from dotenv import load_dotenv
load_dotenv()


class MCPAgent:
    def __init__(self, anthropic_model: str):
        
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

        self.model = anthropic_model

        prompt = (
            "Você é um agente de IA que conversa com as pessoas sobre assuntos cotidianos. \n"
            "Use as ferramentas disponíveis para responder às perguntas dos usuários. \n"
            "Use as ferramentas disponíveis para construir seu grafo de conhecimento."
        )

        self.history = [{"role": "assistant", "content": prompt}]

        self.tools = None

    async def connect_to_server(self):
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "-i", "-v", "claude-memory:/app/dist", "--rm", "mcp/memory"],
            env=None,
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        response = await self.session.list_tools()
        print("\nConnected to server with tools:", [tool.name for tool in response.tools])

    async def process_query(self, query: str) -> str:

        self.history.append({"role": "user", "content": query})

        if not self.tools:
            response = await self.session.list_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in response.tools
            ]

        messages = self.history.copy()
        final_text = []

        while True:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=messages,
                tools=self.tools
            )

            if len(response.content) == 1 and response.content[0].type == "text":
                final_text.append(response.content[0].text)
                messages.append({"role": "assistant", "content": response.content})
                break

            assistant_message_content = []
            for content in response.content:
                if content.type == "text":
                    final_text.append(content.text)
                    assistant_message_content.append(content)
                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input

                    result = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                    
                    assistant_message_content.append(content)
                    
                    messages.append(
                        {"role": "assistant", "content": assistant_message_content}
                    )

                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result.content,
                                }
                            ],
                        }
                    )

        self.history = messages
        return "\n".join(final_text)
    
    async def chat_loop(self):
        print("\nClient Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():

    agent = MCPAgent(anthropic_model="claude-3-5-sonnet-20241022")

    try:
        await agent.connect_to_server()
        await agent.chat_loop()
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())        
