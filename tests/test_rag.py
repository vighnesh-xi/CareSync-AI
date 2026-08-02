import logging
import os
import pickle
import tempfile

import faiss
import numpy as np

from rag.retriever import RAGRetriever


def build_logger():
    logger = logging.getLogger("test_rag")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    return logger


def test_rag_retriever_returns_chunks_and_sources():
    with tempfile.TemporaryDirectory() as temp_dir:
        dimension = 4
        index = faiss.IndexFlatL2(dimension)

        embeddings = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.9, 0.8, 0.7, 0.6],
            [0.2, 0.1, 0.4, 0.3]
        ]).astype("float32")

        index.add(embeddings)
        faiss.write_index(index, os.path.join(temp_dir, "index.faiss"))

        metadata = [
            {
                "chunk_id": 0,
                "text": "CKD patients should monitor fluid intake carefully.",
                "source": "nephrology_reference.pdf",
                "title": "Nephrology Reference Chunk 1"
            },
            {
                "chunk_id": 1,
                "text": "SGLT2 inhibitors may provide renal benefits in some patients.",
                "source": "nephrology_reference.pdf",
                "title": "Nephrology Reference Chunk 2"
            },
            {
                "chunk_id": 2,
                "text": "Warning signs include swelling and decreased urine output.",
                "source": "nephrology_reference.pdf",
                "title": "Nephrology Reference Chunk 3"
            }
        ]

        with open(os.path.join(temp_dir, "metadata.pkl"), "wb") as file:
            pickle.dump(metadata, file)

        retriever = RAGRetriever(temp_dir, build_logger())

        # monkeypatch-like direct replacement to keep test simple
        class DummyEmbeddingModel:
            def encode(self, texts, convert_to_numpy=True):
                return np.array([[0.2, 0.1, 0.4, 0.3]])

        retriever.embedding_model = DummyEmbeddingModel()

        result = retriever.search("What are warning signs in CKD?", top_k=2)

        assert result["success"] is True
        assert len(result["chunks"]) > 0
        assert len(result["sources"]) > 0
        assert "title" in result["sources"][0]
        assert "source" in result["sources"][0]