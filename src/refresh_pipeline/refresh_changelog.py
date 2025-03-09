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


def clean_metadata(metadata: dict) -> dict:
    # Remove keys with None values.
    return {k: v for k, v in metadata.items() if v is not None}


@flow(log_prints=True)
def refresh_changelog():
    """
    This Prefect flow refreshes the changelog collection by fetching new changelogs from
    both Codeium and Cursor and adding them to the collection. It prints the number
    of items in the collection before and after processing.
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

        result = collection.get(ids=[changelog.unique_id])
        if not result["ids"]:
            new_items.append(changelog)
            print("------------- !!!!!!! -------------")
            print(f"New changelog detected: {changelog.unique_id} - {changelog.title}")
            print("------------- !!!!!!! -------------")
            # TODO: Add a notification to Slack here
        else:
            print(f"Changelog already exists: {changelog.unique_id}")

    # Print duplicates before deduplication for inspection.
    duplicates = {}
    for changelog in new_items:
        duplicates.setdefault(changelog.unique_id, []).append(changelog)
    for uid, changelog_list in duplicates.items():
        if len(changelog_list) > 1:
            print(f"\nDuplicate found for unique_id {uid}:")
            for cl in changelog_list:
                print(f"   Title: {cl.title} --- Version: {cl.version}")
                print(f"   Changes: {cl.changes}\n")

    # Deduplicate new_items based on unique_id.
    unique_new_items = {
        changelog.unique_id: changelog for changelog in new_items
    }.values()
    unique_new_items = list(unique_new_items)

    # Prepare metadata by cleaning out None values.
    metadatas_to_add = [
        clean_metadata(changelog.model_dump()) for changelog in unique_new_items
    ]

    # Print metadata for debugging.
    for md in metadatas_to_add:
        print("Cleaned metadata:", md)

    # If there are new items, add them to the collection.
    if unique_new_items:
        ids_to_add = [changelog.unique_id for changelog in unique_new_items]
        documents_to_add = [
            changelog.changes for changelog in unique_new_items
        ]  # The text to embed.
        collection.add(
            ids=ids_to_add,
            documents=documents_to_add,
            metadatas=metadatas_to_add,
        )
        print(f"Added {len(unique_new_items)} new changelogs to the collection.")
    else:
        print("No new changelogs found.")

    # Print the number of items in the collection after processing.
    final_count = collection.count()
    print("Number of items in the collection after processing:", final_count)
    print("Difference:", final_count - original_count)


if __name__ == "__main__":
    refresh_changelog()
