import os
import pickle
from typing import Dict, Any, List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class RAGRetriever:
    def __init__(self, faiss_index_path: str, logger):
        self.faiss_index_path = faiss_index_path
        self.logger = logger
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.metadata = None
        self._load_index()

    def _load_index(self) -> None:
        index_file = os.path.join(self.faiss_index_path, "index.faiss")
        metadata_file = os.path.join(self.faiss_index_path, "metadata.pkl")

        if not os.path.exists(index_file) or not os.path.exists(metadata_file):
            self.logger.warning("RAGRetriever: FAISS index or metadata not found.")
            self.index = None
            self.metadata = None
            return

        self.index = faiss.read_index(index_file)

        with open(metadata_file, "rb") as file:
            self.metadata = pickle.load(file)

        self.logger.info("RAGRetriever: FAISS index and metadata loaded.")

    def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        if self.index is None or self.metadata is None:
            self.logger.error("RAGRetriever: Index not available for search.")
            return {
                "success": False,
                "answer": "",
                "sources": [],
                "chunks": []
            }

        self.logger.info(f"RAGRetriever: Searching for query: {query}")

        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        retrieved_chunks = []
        sources = []

        for idx in indices[0]:
            if idx < 0 or idx >= len(self.metadata):
                continue

            item = self.metadata[idx]
            retrieved_chunks.append(item["text"])
            sources.append({
                "title": item["title"],
                "source": item["source"]
            })

        answer = " ".join(retrieved_chunks)

        self.logger.info(f"RAGRetriever: Retrieved {len(retrieved_chunks)} chunks.")

        return {
            "success": len(retrieved_chunks) > 0,
            "answer": answer,
            "sources": sources,
            "chunks": retrieved_chunks
        }