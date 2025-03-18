import uvicorn 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
import re

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

# Initialize DeepSeek LLM via Ollama
llm = OllamaLLM(model="deepseek-r1:1.5b")

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

# Define general query prompt
general_template = """Answer the following question concisely and accurately:

Question: {question}

Response:"""
general_prompt = ChatPromptTemplate.from_template(general_template)

# Database connection setup
postgresql_uri = "postgresql+psycopg2://root:cs620ibdc1234@localhost:5432/IowaLiquorSales"
db = SQLDatabase.from_uri(postgresql_uri)

print("Connected to database")

class Query(BaseModel):
    question: str

memory_db = {
    "last_query": "",
    "last_response": ""
}

@app.post("/query")
def process_query(query: Query):
    user_question = query.question.lower()
    
    # Detect if the query is about the database
    db_keywords = ["table", "database", "rows", "columns", "select", "count", "query"]
    is_db_query = any(keyword in user_question for keyword in db_keywords)

    if is_db_query:
        # Retrieve table schema
        schema = db.get_table_info()
        
        # Generate SQL query using DeepSeek
        response = llm.invoke(db_prompt.format(schema=schema, question=query.question))
        sql_query = response.split("\n")[-1].strip()
        
        # Execute SQL query
        try:
            result = db.run(sql_query)
            print(result)
            # Provide context to DeepSeek to ensure a meaningful response
            formatted_result = f"The database query returned the following data: {result}. This result represents the answer to the question: {query.question}. Please summarize it clearly."

            final_response = llm.invoke(
                final_response_prompt.format(results=formatted_result, question=query.question)
            )

            # Clean up the response (if needed)
            cleaned_response = re.sub(r"<think>.*?</think>", "", final_response, flags=re.DOTALL).strip()

            # Store for reference
            memory_db["last_query"] = sql_query
            memory_db["last_response"] = cleaned_response
            
            return {"query": sql_query, "response": cleaned_response}
        except Exception as e:
            memory_db["last_response"] = str(e)
            return {"error": str(e)}
    else:
        # Generate a general response using DeepSeek
        response = llm.invoke(general_prompt.format(question=query.question))
        # Remove '<think>' sections
        cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
        
        memory_db["last_query"] = query.question
        memory_db["last_response"] = cleaned_response
        return {"response": cleaned_response}

@app.get("/query")
def get_last_query():
    return {"last_query": memory_db["last_query"], "last_response": memory_db["last_response"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    