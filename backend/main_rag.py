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

# pydantic model for query
class Query(BaseModel):
    question: str

rag_chain: Optional[RetrievalQA] = None


def get_db_connection():
    
    # returns a psycopg2 connection
    
    engine = sqlalchemy.create_engine(db_connection_string)
    return engine.raw_connection()





def create_rag_chain(
    vectorstore: PGVector,
    model_name: str = "gpt-4",
    temperature: float = 0.0,
    k_retrieval: int = 10
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

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    vectorstore = PGVector(
        connection_string=db_connection_string,
        collection_name="vector_embeds",
        embedding_function=embeddings,
    )

    # creating chain
    rag_chain = create_rag_chain(
        vectorstore=vectorstore,
        model_name="gpt-4",
        temperature=0.0,
        k_retrieval=10
    )
    print("RAG chain created.")


@app.post("/query")
def process_query(query: Query):
    
    global rag_chain
    user_question = query.question.strip()

    if not rag_chain:
        return {"error": "RAG chain not initialized."}

    # running question through chain
    response = rag_chain.run(user_question)

    return {"question": user_question, "response": response}


# endpoint to verify service is working
@app.get("/")
def read_root():
    return {"message": "RAG service is started!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)