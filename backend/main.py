import os
import uvicorn
from typing import Optional, Dict, Any
import numbers
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

import auth
from models import Base
from database import engine

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

app.include_router(auth.router)
Base.metadata.create_all(bind=engine)

# Pydantic Model for Query
class Query(BaseModel):
    question: str

rag_chain: None
llm: None


def get_db_connection():
    engine = sqlalchemy.create_engine(db_connection_string)
    return engine


def create_rag_chain(vectorstore: PGVector,) -> RetrievalQA:
    global llm
    llm = ChatOpenAI(
        model_name="gpt-4",
        openai_api_key=openai_api_key,
        temperature=0.0
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

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

    rag_chain = create_rag_chain(vectorstore=vectorstore)
    print("RAG chain created.")

def format_value(v: Any) -> str:
    """Comma-format numbers, leave everything else as str."""
    if isinstance(v, numbers.Number):
        return f"{v:,}"
    return str(v)

def extract_metadata_filters(user_question: str) -> dict:
    """Use LLM to extract metadata filters like city, month, category from the user's question."""
    filter_prompt = f"""
    Given the following user question:
    
    "{user_question}"
    
    Extract possible metadata filters as a Python dictionary with keys:
    - city
    - category_name
    - month (format: YYYY-MM)
    - store_name
    - item_description

    If any field is missing, omit it. 
    Only output the raw Python dictionary.
    """

    metadata_candidate = llm.predict(filter_prompt).strip()

    try:
        filters = eval(metadata_candidate) 
        return filters
    except Exception as e:
        print(f"Failed to parse filters: {e}")
        return {}

@app.post("/query")
def process_query(query: Query):
    global rag_chain, llm
    user_question = query.question.strip()

    if not rag_chain:
        return {"error": "RAG chain not initialized."}
    
    # Step 1: Extract metadata filters from question
    filters = extract_metadata_filters(user_question)

    # Step 2: Create a customized retriever with filters
    retriever = rag_chain.retriever.vectorstore.as_retriever(
        search_kwargs={"k": 15000, "filter": filters} if filters else {"k": 15000}
    )

    # Step 3: Decide chain type based on number of documents actually retrieved
    retrieved_docs = retriever.get_relevant_documents(user_question)
    num_retrieved = len(retrieved_docs)

    if num_retrieved <= 50:
        chain_type = "stuff"
    else:
        chain_type = "map_reduce"

    # Step 4: Create RetrievalQA chain dynamically
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type=chain_type
    )
    
    rag_response = rag_chain.run(user_question)

    return {"question": user_question, "response": rag_response}
    
    # SQL
    # prompt = f"""
    # You are working with a PostgreSQL database. The table is called 'liquorsales' and contains fields like:
    # - date (DATE): the date of the sale
    # - sale_dollars (NUMERIC): the total dollar value of the sale
    # - sale_bottles (INTEGER): number of bottles sold
    # - sale_liters (NUMERIC): total liters sold
    # - category_name (TEXT): category of the liquor
    # - im_desc (TEXT): item description
    # - vendor_name (TEXT): vendor of the product
    # - name (TEXT): store name

    # Question: {user_question}
    # If you can answer this using SQL, return a valid SQL query using the 'liquorsales' table.

    # Output only the SQL. No explanations.
    # """

    # sql_candidate = llm.predict(prompt).strip()

    # if sql_candidate.lower().startswith("select"):
    #     #safeguard to correct hallucinated table names
    #     if "from sales" in sql_candidate.lower():
    #         sql_candidate = sql_candidate.replace("FROM sales", "FROM liquorsales")

    #     try:
    #         db = get_db_connection()
    #         with db.connect() as conn:
    #             result = conn.execute(text(sql_candidate))
    #             rows = result.fetchall()
    #             keys = result.keys()
    #             data = [dict(zip(keys, row)) for row in rows]
                
    #         if len(data) == 1:
    #             row = data[0]
    #             if len(row) == 1:
    #                 val = next(iter(row.values()))
    #                 answer = f"{user_question} → {format_value(val)}"
    #             else:
    #                 parts = [f"{k}: {format_value(v)}" for k, v in row.items()]
    #                 answer = f"{user_question} → " + "; ".join(parts)
    #         else:
    #             lines = []
    #             for r in data:
    #                 parts = [f"{k}: {format_value(v)}" for k, v in r.items()]
    #                 lines.append(", ".join(parts))
    #             answer = f"{user_question} →\n" + "\n".join(lines)

    #         return {"response": answer}

    #     except Exception as e:
    #         return {"error": f"SQL execution failed: {e}"}                

    # return {"error": "No valid answer could be generated."}

@app.get("/")
def read_root():
    return {"message": "RAG + Hybrid SQL pipeline is live!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
