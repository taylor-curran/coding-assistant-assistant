from prefect.blocks.system import Secret
import chromadb
from chromadb.utils import embedding_functions

# Load your OpenAI API key from Prefect Secret
openai_api_key = Secret.load("openai-api-key").get()

# Initialize embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_api_key, model_name="text-embedding-3-small"
)

# Connect to Chroma collection
client = chromadb.PersistentClient(path="./data")
collection = client.get_collection(
    name="coding_assistant_document_dump", embedding_function=openai_ef
)

# How can we query the collection?

print("Keys: ")
print(collection.peek().keys())

print("IDs: ")
print(collection.peek()["ids"])

# Example Embedding
result = collection.get(
    ids=["Codeium_Enterprise_1.2.5_new_models"], include=["embeddings", "documents"]
)
example_embedding = result["embeddings"]
example_document = result["documents"]

print("-----------")
print("Embedding: ")
print(example_embedding)
print(type(example_embedding))

print("Shape: ")
print(example_embedding.shape)

print("Document: ")
print(example_document)
