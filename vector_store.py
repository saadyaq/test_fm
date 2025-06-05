class SimpleIndex:
    def __init__(self):
        self.vectors = []

    def upsert(self, vectors):
        for _id, embedding, metadata in vectors:
            self.vectors.append({"id": _id, "embedding": embedding, "metadata": metadata})


def initialize_vector_store():
    """Initialize an in-memory vector store."""
    return SimpleIndex()


def retrieve_relevant_segments(query: str, index: SimpleIndex, k: int = 3) -> str:
    """Retrieve segments that were inserted. This stub simply returns the first k segments."""
    texts = [entry["metadata"].get("segment_text", "") for entry in index.vectors[:k]]
    return "\n".join(texts)
