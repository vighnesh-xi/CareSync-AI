import os
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

from app.config import get_settings
from app.dependencies import get_logger
from rag.chunking import chunk_text


class RAGIngestor:
    def __init__(self, reference_path: str, faiss_index_path: str, logger):
        self.reference_path = reference_path
        self.faiss_index_path = faiss_index_path
        self.logger = logger
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def extract_text(self) -> str:
        if not os.path.exists(self.reference_path):
            raise FileNotFoundError(f"Reference file not found: {self.reference_path}")

        file_ext = os.path.splitext(self.reference_path)[1].lower()

        if file_ext == ".txt":
            self.logger.info(f"RAGIngestor: Reading text file from {self.reference_path}")
            with open(self.reference_path, "r", encoding="utf-8") as file:
                return file.read()

        if file_ext == ".pdf":
            self.logger.info(f"RAGIngestor: Reading PDF from {self.reference_path}")
            reader = PdfReader(self.reference_path)
            all_text = []

            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    all_text.append(page_text)

            return "\n".join(all_text)

        raise ValueError("Unsupported reference file format. Use .txt or .pdf")

    def build_index(self) -> None:
        text = self.extract_text()
        chunks = chunk_text(text, chunk_size=500, overlap=100)

        if not chunks:
            raise ValueError("No chunks generated from reference material.")

        self.logger.info(f"RAGIngestor: Generated {len(chunks)} chunks.")

        embeddings = self.embedding_model.encode(chunks, convert_to_numpy=True)
        embeddings = np.array(embeddings).astype("float32")

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        os.makedirs(self.faiss_index_path, exist_ok=True)

        faiss.write_index(index, os.path.join(self.faiss_index_path, "index.faiss"))

        metadata = []
        source_name = os.path.basename(self.reference_path)

        for idx, chunk in enumerate(chunks):
            metadata.append({
                "chunk_id": idx,
                "text": chunk,
                "source": source_name,
                "title": f"Nephrology Reference Chunk {idx + 1}"
            })

        with open(os.path.join(self.faiss_index_path, "metadata.pkl"), "wb") as file:
            pickle.dump(metadata, file)

        self.logger.info("RAGIngestor: FAISS index and metadata saved successfully.")


if __name__ == "__main__":
    settings = get_settings()
    logger = get_logger()

    ingestor = RAGIngestor(
        reference_path=settings.nephrology_reference_path,
        faiss_index_path=settings.faiss_index_path,
        logger=logger
    )
    ingestor.build_index()