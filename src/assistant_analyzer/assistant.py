# src/assistant_analyzer/dev/assistant_openai_agent.py

import chromadb
from chromadb.utils import embedding_functions
from prefect.blocks.system import Secret
from typing import Any
import asyncio

# Import the OpenAI Agents SDK
from agents import Agent, Runner, function_tool, RunContextWrapper

# Initialize OpenAI API key using secret block
secret_block = Secret.load("openai-api-key")
openai_api_key = secret_block.get()

# Set up the embedding function with the API key directly
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_api_key, model_name="text-embedding-3-small"
)

# Create a persistent client and get the collection
client = chromadb.PersistentClient(path="./data")
collection = client.get_collection(
    name="coding_assistant_document_dump", embedding_function=openai_ef
)


# --- Create the tool for querying the vector store ---
@function_tool
async def query_vector_store(ctx: RunContextWrapper[Any], query: str) -> str:
    """
    Query the vector store for documents related to the user's question.

    Args:
        query: The user input to search against the vector store.

    Returns:
        A formatted string with the retrieved documents.
    """
    result = collection.query(
        query_texts=[query],
        n_results=3,
        include=["documents", "metadatas"],
    )

    # Build a response that summarizes the results
    response = "Here are some relevant documents from the vector store:\n"
    for i, doc in enumerate(result["documents"][0], start=1):
        response += f"\nDocument {i}:\n{doc}\n------------"
    return response


# Create the agent with the tools and model
agent = Agent(
    name="Vector Store Assistant",
    instructions=(
        "You are an assistant that can chat with a vector store. "
        "When a user asks a question, use the 'query_vector_store' tool to retrieve relevant documents."
    ),
    tools=[query_vector_store],
    model="gpt-4o",
)


async def main(query: str):
    """Run the agent with the given query.

    Args:
        query: The question to ask the agent

    Returns:
        The agent's response
    """
    # Print some basic info from the vector store
    print(
        "Vector store info:\n\n"
        f"Example metadata: {collection.peek()['metadatas'][0]}\n"
        f"Document count: {collection.count()}"
        "\n\n"
        "-------------------"
    )

    # Run the agent with the query
    result = await Runner.run(agent, query)

    # Print and return the result
    print("Agent response:\n\n" f"{result.final_output}" "\n\n" "-------------------")
    return result.final_output


# --- Run the agent ---
if __name__ == "__main__":
    # Default sample query if run directly
    sample_query = "Did cursor introduce a feature like codeium's mcp feature? If so, which version introduced it? Which company has the most advanced mcp support?"
    asyncio.run(main(sample_query))
