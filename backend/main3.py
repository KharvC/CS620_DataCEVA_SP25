import os
import uvicorn
from typing import Optional
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

#Pydantic Model for Query
class Query(BaseModel):
    question: str

rag_chain: Optional[RetrievalQA] = None


def get_db_connection():
    
    #Returns a psycopg2 connection
    
    engine = sqlalchemy.create_engine(db_connection_string)
    return engine.raw_connection()


def build_pgvector_store(
    connection_string: str,
    collection_name: str = "vector_embeds",
    table_name: str = "liquorsales",
    embeddings_batch_size: int = 1000,
    max_rows: int = 10000
):
    
    # Creating embeddings instance and PGVector store object
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = PGVector(
        connection_string=connection_string,
        collection_name=collection_name,        
        embedding_function=embeddings,
    )

    existing_ids = set()
    with psycopg2.connect(connection_string) as pgconn:
        with pgconn.cursor() as cur:
            metadata_query = f"SELECT metadata->>'record_id' FROM {collection_name};"
            cur.execute(metadata_query)
            rows = cur.fetchall()
            existing_ids = {r[0] for r in rows if r[0] is not None}


    conn = get_db_connection()
    cursor = conn.cursor()

    offset = 0
    total_processed = 0

    while total_processed < max_rows:
        query_batch = f"SELECT * FROM {table_name} LIMIT {embeddings_batch_size} OFFSET {offset};"
        cursor.execute(query_batch)
        batch_results = cursor.fetchall()

        if not batch_results:
            break

        documents = []
        for row in batch_results:
            record_id = str(row[0])

            if record_id in existing_ids:
                continue

            page_content = " ".join([str(col) for col in row])

            doc = Document(
                page_content=page_content,
                metadata={"record_id": record_id}
            )
            documents.append(doc)

        if documents:
            vectorstore.add_documents(documents)
            for doc in documents:
                existing_ids.add(doc.metadata["record_id"])

        offset += embeddings_batch_size
        batch_size_retrieved = len(batch_results)
        total_processed += batch_size_retrieved
        print(f"Processed {batch_size_retrieved} new rows; total so far = {total_processed}")

    cursor.close()
    conn.close()

    return vectorstore


def create_rag_chain(
    vectorstore: PGVector,
    model_name: str = "gpt-4",
    temperature: float = 0.0,
    k_retrieval: int = 50
) -> RetrievalQA:
    
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

    # Build the vector store from your table
    print("Building/Updating vector store from DB ...")
    vectorstore = build_pgvector_store(
        connection_string=db_connection_string,
        collection_name="vector_embeds",  
        table_name="liquorsales",         
        embeddings_batch_size=1000,
        max_rows=10000
    )
    print("Vector store ready.")

    # Create the chain
    rag_chain = create_rag_chain(
        vectorstore=vectorstore,
        model_name="gpt-4",
        temperature=0.0,
        k_retrieval=50
    )
    print("RAG chain created.")


@app.post("/query")
def process_query(query: Query):
    
    global rag_chain
    user_question = query.question.strip()

    if not rag_chain:
        return {"error": "RAG chain not initialized."}

    # Run the question through the chain
    response = rag_chain.run(user_question)

    return {"question": user_question, "response": response}


#endpoint to verify the service's working
@app.get("/")
def read_root():
    return {"message": "RAG service is started!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)