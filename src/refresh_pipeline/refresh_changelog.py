import chromadb
from prefect import flow

client = chromadb.PersistentClient(path="/path/to/save/to")


@flow
def refresh_changelog():
    pass


if __name__ == "__main__":
    refresh_changelog()
