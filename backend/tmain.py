import os
import uvicorn
from typing import Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import PGVector
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document

import sqlalchemy
from sqlalchemy import text
import psycopg2

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
db_connection_string = os.getenv("POSTGRESQL_URI")

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Model for Query
class Query(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None

rag_chain: Optional[RetrievalQA] = None
llm: Optional[ChatOpenAI] = None


def get_db_connection():
    engine = sqlalchemy.create_engine(db_connection_string)
    return engine


def create_rag_chain(
    vectorstore: PGVector,
    model_name: str = "gpt-4",
    temperature: float = 0.0,
    k_retrieval: int = 50000
) -> RetrievalQA:
    global llm
    llm = ChatOpenAI(
        model_name=model_name,
        openai_api_key=openai_api_key,
        temperature=temperature
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": k_retrieval})

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )

    return qa_chain


@app.on_event("startup")
def startup_event():
    global rag_chain

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    vectorstore = PGVector(
        connection_string=db_connection_string,
        collection_name="vector_embeds",
        embedding_function=embeddings,
    )

    rag_chain = create_rag_chain(
        vectorstore=vectorstore,
        model_name="gpt-4",
        temperature=0.0,
        k_retrieval=50000
    )
    print("RAG chain created.")


@app.post("/query")
def process_query(query: Query):
    global rag_chain, llm
    user_question = query.question.strip()

    if not rag_chain:
        return {"error": "RAG chain not initialized."}

    # 1. Use LLM to decide if SQL is better than RAG
    prompt = f"""
    You are working with a PostgreSQL database. The table is called 'liquorsales' and contains fields like:
    - date (DATE): the date of the sale
    - sale_dollars (NUMERIC): the total dollar value of the sale
    - sale_bottles (INTEGER): number of bottles sold
    - sale_liters (NUMERIC): total liters sold
    - category_name (TEXT): category of the liquor
    - im_desc (TEXT): item description
    - vendor_name (TEXT): vendor of the product
    - name (TEXT): store name

    Question: {user_question}
    If you can answer this using SQL, return a valid SQL query using the 'liquorsales' table.

    Output only the SQL. No explanations.
    """

    sql_candidate = llm.predict(prompt).strip()

    if sql_candidate.lower().startswith("select"):
        # Optional safeguard to correct hallucinated table names
        if "from sales" in sql_candidate.lower():
            sql_candidate = sql_candidate.replace("FROM sales", "FROM liquorsales")

        try:
            db = get_db_connection()
            with db.connect() as conn:
                result = conn.execute(text(sql_candidate))
                rows = result.fetchall()
                keys = result.keys()
                data = [dict(zip(keys, row)) for row in rows]
                return {"question": user_question, "response": data, "sql_used": sql_candidate}
        except Exception as e:
            return {"question": user_question, "response": f"SQL execution failed: {str(e)}", "sql_attempted": sql_candidate}

    # 2. Fall back to RAG
    retriever = rag_chain.retriever.vectorstore.as_retriever(
        search_kwargs={"k": 50000, "filter": query.filters} if query.filters else {"k": 50000}
    )

    response = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff"
    ).run(user_question)

    return {"question": user_question, "response": response}


@app.get("/")
def read_root():
    return {"message": "RAG + Hybrid SQL pipeline is live!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
