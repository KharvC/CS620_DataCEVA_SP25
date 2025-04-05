import os
from dotenv import load_dotenv

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import PGVector
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()  # Load environment variables

openai_api_key = os.getenv("OPENAI_API_KEY")

def create_rag_chain(
    db_connection_string: str,
    collection_name: str = "vector_embeds",
    model_name: str = "gpt-4",
    temperature: float = 0.0,
    k_retrieval: int = 3
):

    # creating LLM
    llm = ChatOpenAI(
        model_name=model_name,
        openai_api_key=openai_api_key,
        temperature=temperature
    )

    # setup embeddings & vector storage
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = PGVector(
        connection_string=db_connection_string,
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    # creating retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": k_retrieval})

    # creating the RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # "refine" if combined text does not fit into the context window (more expensive since using multiple LLM calls)
        retriever=retriever
    )

    # provide a custom prompt (this is optional)
#     custom_prompt = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
# if not enough information, say don't know
# keep answer concise.

# Context:
# {context}

# Question: {question}

# Answer:
# """
    # prompt = PromptTemplate(
    #     template=custom_prompt,
    #     input_variables=["context", "question"]
    # )
    # Attach custom prompt to the chain
    #qa_chain.combine_documents_chain.llm_chain.prompt = prompt

    return qa_chain