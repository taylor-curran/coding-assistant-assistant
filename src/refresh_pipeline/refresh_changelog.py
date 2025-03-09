# src/refresh_pipeline/refresh_changelog.py

import chromadb
from datetime import datetime
from prefect import flow
from src.loaders.cursor.load_cursor_changelog import fetch_and_parse_cursor_changelog
from src.loaders.codeium.load_codeium_changelog import fetch_and_parse_codeium_changelog


@flow(log_prints=True)
def refresh_changelog():
    # Initialize a persistent Chroma client.
    # The path provided ensures data is saved in the /data/ directory.
    client = chromadb.PersistentClient(path="./data")

    # Use get_or_create_collection to retrieve the collection if it exists,
    # or create it if it doesn't. Here we add metadata with the current date.
    collection = client.get_or_create_collection(
        name="coding_assistant_document_dump",
        metadata={"last_update_date": datetime.now().isoformat()},
    )

    # Optional: Print some collection info
    print("Number of items in the collection:", collection.count())


if __name__ == "__main__":
    refresh_changelog()
