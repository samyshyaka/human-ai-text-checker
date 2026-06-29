from langchain_community.vectorstores import Chroma

import config
from app.rag.embeddings import get_embeddings


class RAGService:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.vectorstore = self._setup_vectorstore()
        self._log_knowledge_base_status()

    def _setup_vectorstore(self) -> Chroma:
        try:
            vectorstore = Chroma(
                persist_directory=config.CHROMA_DIR,
                embedding_function=self.embeddings,
                collection_name=config.COLLECTION_NAME,
            )
            print("Loaded existing vectorstore")
            return vectorstore
        except Exception:
            vectorstore = Chroma(
                persist_directory=config.CHROMA_DIR,
                embedding_function=self.embeddings,
                collection_name=config.COLLECTION_NAME,
            )
            print("Created new vectorstore")
            return vectorstore

    def _log_knowledge_base_status(self) -> None:
        count = self.vectorstore._collection.count()
        if count == 0:
            print("ChromaDB is empty. Run: python build_knowledge_base.py --reset")
        else:
            print(f"Loaded knowledge base with {count} documents from ChromaDB")

    def retrieve_relevant_context(self, query: str, top_k: int = None) -> str:
        top_k = top_k or config.RAG_TOP_K
        try:
            docs = self.vectorstore.similarity_search(query, k=top_k)
            if docs:
                contexts = [doc.page_content for doc in docs]
                combined_context = "\n\n".join(contexts)
                print(f"Retrieved {len(contexts)} relevant contexts")
                return combined_context
            return "AI detection patterns and human writing characteristics."
        except Exception as exc:
            print(f"RAG retrieval failed: {exc}")
            return "AI detection patterns and human writing characteristics."

    @property
    def collection_count(self) -> int:
        return self.vectorstore._collection.count()

    def retrieve_human_examples(self, query: str, top_k: int = 2) -> str:
        """Retrieve human-labeled writing samples to guide humanization."""
        try:
            docs = self.vectorstore.similarity_search(query, k=10)
            human_docs = [doc for doc in docs if doc.metadata.get("label") == "human"][:top_k]
            selected = human_docs or docs[:top_k]
            if not selected:
                return ""
            return "\n\n---\n\n".join(doc.page_content for doc in selected)
        except Exception as exc:
            print(f"Human example retrieval failed: {exc}")
            return ""
