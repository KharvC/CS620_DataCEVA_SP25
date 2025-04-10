import uvicorn 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
#from langchain_ollama.llms import OllamaLLM
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import re
from dotenv import load_dotenv
import os

app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables and set API key
load_dotenv(dotenv_path="../.env")
api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key

# Initialize ChatOpenAI LLM (using GPT-4 here)
llm = ChatOpenAI(model_name="gpt-4", openai_api_key=api_key, temperature=0)

# Define SQL query generation prompt
db_template = """Based on the table schema below, write a SQL query that would answer the user's question:
{schema}

Question: {question}

Respond with only the SQL query and nothing else."""
db_prompt = ChatPromptTemplate.from_template(db_template)

# Define final processing prompt
final_response_template = """Given the following query results:
{results}

Answer the user's question:
Question: {question}

Response:"""
final_response_prompt = ChatPromptTemplate.from_template(final_response_template)

# Define general query prompt (fallback if vector retrieval is not applicable)
general_template = """Answer the following question concisely and accurately:

Question: {question}

Response:"""
general_prompt = ChatPromptTemplate.from_template(general_template)

# Database connection setup
postgresql = os.getenv("postgresql_uri")
os.environ["postgresql_uri"] = postgresql

db = SQLDatabase.from_uri(postgresql)
print("Connected to database")

# --- VECTOR STORE SETUP ---
# Create an embeddings instance using OpenAI embeddings.
embedding_model = OpenAIEmbeddings(openai_api_key=api_key)

def build_vector_store_in_batches(batch_size=1000, max_rows=1000):
    offset = 0
    documents = []
    total_processed = 0
    while total_processed < max_rows:
        query_batch = f"SELECT * FROM liquorsales LIMIT {batch_size} OFFSET {offset}"
        batch_results = db.run(query_batch)
        if not batch_results:
            break
        
        # Print debug info for the first batch
        if total_processed == 0:
            print("Sample row:", batch_results[0])
        
        for row in batch_results:
            if isinstance(row, dict):
                text_content = " ".join([str(value) for key, value in row.items()])
            else:
                text_content = str(row)
            documents.append(Document(page_content=text_content, metadata={'raw': row}))
        
        total_processed += len(batch_results)
        print(f"Processed {total_processed} rows so far...")
        offset += batch_size

    if documents:
        vs = FAISS.from_documents(documents, embedding_model)
        print("Vector store built successfully!")
        return vs
    else:
        print("No documents found in the dataset.")
        return None

# Build the vector store using batches.
vectorstore = build_vector_store_in_batches(batch_size=1000, max_rows=10000)




# -------------------------

class Query(BaseModel):
    question: str

memory_db = {
    "last_query": "",
    "last_response": ""
}

@app.post("/query")
def process_query(query: Query):
    user_question = query.question.lower()
    
    # Detect if the query is about the database (SQL query generation)
    db_keywords = ["table", "database", "rows", "columns", "select", "count", "query"]
    is_db_query = any(keyword in user_question for keyword in db_keywords)

    if is_db_query:
        # Retrieve table schema
        schema = db.get_table_info()
        
        # Generate SQL query using the LLM
        response = llm.invoke(db_prompt.format(schema=schema, question=query.question))
        sql_query = response.content.split("\n")[-1].strip()
        
        # Execute SQL query
        try:
            result = db.run(sql_query)
            print(result)
            # Provide context to the LLM to ensure a meaningful response
            formatted_result = f"The database query returned the following data: {result}. This result represents the answer to the question: {query.question}. Please summarize it clearly."

            final_response = llm.invoke(
                final_response_prompt.format(results=formatted_result, question=query.question)
            )

            # Clean up the response (if needed)
            cleaned_response = re.sub(r"<think>.*?</think>", "", final_response.content, flags=re.DOTALL).strip()

            # Store for reference
            memory_db["last_query"] = sql_query
            memory_db["last_response"] = cleaned_response
            
            return {"query": sql_query, "response": cleaned_response}
        except Exception as e:
            memory_db["last_response"] = str(e)
            return {"error": str(e)}
    else:
        # For general queries, try retrieval augmentation using the vector store.
        if vectorstore is not None:
            try:
                # Perform a similarity search in the vectorstore (retrieve top 3 most relevant documents)
                retrieved_docs = vectorstore.similarity_search(query.question, k=3)
                context = "\n".join([doc.page_content for doc in retrieved_docs])
                
                # Create a prompt that includes the retrieved context.
                retrieval_template = """Using the following context, answer the question:
Context:
{context}

Question: {question}

Response:"""
                retrieval_prompt = ChatPromptTemplate.from_template(retrieval_template)
                response = llm.invoke(retrieval_prompt.format(context=context, question=query.question))
                cleaned_response = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()
            except Exception as e:
                # Fallback to a general prompt if any error occurs during retrieval.
                cleaned_response = f"Error during retrieval: {str(e)}. Falling back to a general response.\n"
                response = llm.invoke(general_prompt.format(question=query.question))
                cleaned_response += re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()
        else:
            # If vectorstore is not available, use the general prompt.
            response = llm.invoke(general_prompt.format(question=query.question))
            cleaned_response = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()
        
        memory_db["last_query"] = query.question
        memory_db["last_response"] = cleaned_response
        return {"response": cleaned_response}

@app.get("/query")
def get_last_query():
    return {"last_query": memory_db["last_query"], "last_response": memory_db["last_response"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
