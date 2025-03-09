# src/assistant_analyzer/assistant.py

import chromadb

client = chromadb.PersistentClient(path="./data")

collection = client.get_collection(name="coding_assistant_document_dump")

print(collection.peek()["metadatas"][0])

print(collection.count())

result = collection.query(
    query_texts=["Did cursor introduce a context awareness feature?"], n_results=3, include=["documents", "metadatas"]
)

# Access the raw text from the documents:
print("Documents:")
for doc in result["documents"]:
    print(doc)

# Or access the raw text from the metadata:
print("Metadatas:")
for meta in result["metadatas"]:
    print(meta[""])
