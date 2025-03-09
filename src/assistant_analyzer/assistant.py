import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from prefect.blocks.system import Secret

# --- Initialize your vector store ---
# Load your OpenAI API key from a secret
secret_block = Secret.load("openai-api-key")
openai_api_key = secret_block.get()

# Set up the embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_api_key, model_name="text-embedding-3-small"
)

# Create a persistent client and get the collection
client = chromadb.PersistentClient(path="./data")
collection = client.get_collection(
    name="coding_assistant_document_dump", embedding_function=openai_ef
)

# (Optional) Print some basic info from your vector store
print("Example metadata:", collection.peek()["metadatas"][0])
print("Document count:", collection.count())

# --- Create the PydanticAI agent ---
from pydantic_ai import Agent, RunContext

# The system prompt instructs the model on how to interact with your vector store.
agent = Agent(
    'openai:gpt-4o',
    result_type=str,
    system_prompt=(
        "You are an assistant that can chat with a vector store. "
        "When a user asks a question, use the 'query_vector_store' tool to retrieve relevant documents."
    )
)

# Define a tool that queries the vector store.
@agent.tool
async def query_vector_store(ctx: RunContext, query: str) -> str:
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
    for i, doc in enumerate(result["documents"], start=1):
        response += f"\nDocument {i}:\n{doc}\n------------"
    return response

# --- Run the agent with a sample query ---
if __name__ == "__main__":
    sample_query = "Did cursor introduce a context awareness feature? If so, which version introduced it?"
    result = agent.run_sync(sample_query)
    print("Agent response:")
    print(result.data)
