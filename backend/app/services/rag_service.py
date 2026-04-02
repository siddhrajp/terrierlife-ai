import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from sqlalchemy.orm import Session

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

CONNECTION_STRING = os.getenv("DATABASE_URL", "postgresql://localhost/terrierlife")


def _get_vectorstore() -> PGVector:
    return PGVector(
        connection_string=CONNECTION_STRING,
        embedding_function=embeddings,
        collection_name="bu_resources",
        use_jsonb=True,
    )


async def search_bu_resources(db: Session, query: str) -> dict:
    vectorstore = _get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    docs = retriever.invoke(query)

    if not docs:
        return {
            "context": "No relevant BU resources found.",
            "sources": [],
        }

    context = "\n\n".join([
        f"Source: {doc.metadata.get('title', 'BU Resource')} ({doc.metadata.get('url', '')})\n{doc.page_content[:1000]}"
        for doc in docs
    ])

    return {
        "context": context,
        "sources": [
            {
                "title": doc.metadata.get("title", "BU Resource"),
                "url": doc.metadata.get("url", ""),
                "category": doc.metadata.get("category", ""),
            }
            for doc in docs
        ],
    }
