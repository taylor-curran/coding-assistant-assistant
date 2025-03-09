import chromadb
from datetime import datetime
from prefect import flow
from src.loaders.cursor.load_cursor_changelog import fetch_and_parse_cursor_changelog
from src.loaders.codeium.load_codeium_changelog import fetch_and_parse_codeium_changelog
import chromadb.utils.embedding_functions as embedding_functions
from prefect.blocks.system import Secret

# Initialize OpenAI API key.
secret_block = Secret.load("openai-api-key")
openai_api_key = secret_block.get()

# Initialize the OpenAI embedding function using the loaded API key.
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_api_key, model_name="text-embedding-3-small"
)


@flow(log_prints=True)
def refresh_changelog():
    # Initialize a persistent Chroma client that saves data to the ./data directory.
    """
    This Prefect flow refreshes the changelog collection by fetching new changelogs from
    both Codeium and Cursor and adding them to the collection. It also prints the number
    of items in the collection before and after processing.

    The flow does the following:

    1. Initializes a persistent Chroma client that saves data to the ./data directory.
    2. Gets or creates the persistent collection with the OpenAI embedding function.
    3. Prints the number of items in the collection before processing.
    4. Loads changelogs from both sources.
    5. Checks each changelog by its unique_id.
    6. If a new changelog is detected, adds it to the collection.
    7. Prints the number of items in the collection after processing.
    8. Prints the difference in the number of items in the collection before and after processing.

    The flow is designed to be run periodically to keep the changelog collection up-to-date.
    """
    client = chromadb.PersistentClient(path="./data")

    # Get or create the persistent collection with the OpenAI embedding function.
    collection = client.get_or_create_collection(
        name="coding_assistant_document_dump",
        embedding_function=openai_ef,
        metadata={"last_update_date": datetime.now().isoformat()},
    )

    # Print the number of items in the collection before processing.
    original_count = collection.count()
    print("Number of items in the collection before processing:", original_count)

    # Load changelogs from both sources.
    codeium_changelogs = fetch_and_parse_codeium_changelog()
    cursor_changelogs = fetch_and_parse_cursor_changelog()
    all_changelogs = codeium_changelogs + cursor_changelogs

    # Check each changelog by its unique_id.
    new_items = []
    for changelog in all_changelogs:
        if not changelog.unique_id:
            print(f"Skipping changelog with missing unique_id: {changelog.title}")
            continue

        result = collection.get(ids=[changelog.unique_id], include=["ids"])
        if not result["ids"]:
            new_items.append(changelog)
            print(f"New changelog detected: {changelog.unique_id} - {changelog.title}")
            # TODO: Add a notification to Slack here
        else:
            print(f"Changelog already exists: {changelog.unique_id}")

    # If there are new items, add them to the collection.
    if new_items:
        ids_to_add = [changelog.unique_id for changelog in new_items]
        documents_to_add = [
            changelog.changes for changelog in new_items
        ]  # The text to embed.
        metadatas_to_add = [
            changelog.model_dump() for changelog in new_items
        ]  # Save all attributes.
        collection.add(
            ids=ids_to_add,
            documents=documents_to_add,
            metadatas=metadatas_to_add,
        )
        print(f"Added {len(new_items)} new changelogs to the collection.")
    else:
        print("No new changelogs found.")

    # Print the number of items in the collection after processing.
    final_count = collection.count()
    print("Number of items in the collection after processing:", final_count)
    print("Difference:", final_count - original_count)


if __name__ == "__main__":
    refresh_changelog()
