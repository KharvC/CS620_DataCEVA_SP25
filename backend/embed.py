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

import time


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
db_connection_string = os.getenv("POSTGRESQL_URI")

def get_db_connection():
    
    #Returns a psycopg2 connection
    
    engine = sqlalchemy.create_engine(db_connection_string)
    return engine.raw_connection()



def build_pgvector_store(
    connection_string: str,
    collection_name: str = "vector_embeds",
    table_name: str = "liquorsales",
    embeddings_batch_size: int = 2000,
    sql_batch_size = 16000,
    max_rows: int = 2622712
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

    sql_offset = 0
    total_processed = 0

    while total_processed < max_rows:
        query_batch = f"""
WITH grouped_data AS (
    SELECT
        name,
        MIN(city) AS city,
        MIN(zipcode) AS zipcode,
        MIN(county) AS county,
        DATE_TRUNC('month', date) AS month,
        category_name,
        im_desc,
        MIN(invoice_line_no) AS first_invoice,
        STRING_AGG(DISTINCT vendor_name, ', ') AS vendor_names,
        COUNT(*) AS total_orders,
        SUM(sale_bottles) AS total_bottles,
        SUM(sale_dollars) AS total_sales,
        SUM(sale_liters) AS total_liters,
        AVG(bottle_volume_ml) AS avg_bottle_volume,
        MODE() WITHIN GROUP (ORDER BY pack) AS common_pack
    FROM {table_name}
    GROUP BY name, im_desc, DATE_TRUNC('month', date), category_name
)
SELECT
    name AS store_name,
    city,
    zipcode,
    county,
    month,
    category_name,
    im_desc AS item_description,
    vendor_names,
    total_orders,
    total_bottles,
    total_sales,
    total_liters,
    avg_bottle_volume,
    common_pack
FROM grouped_data
ORDER BY name, im_desc, month, first_invoice
LIMIT {sql_batch_size} OFFSET {sql_offset};
"""
        cursor.execute(query_batch)
        batch_results = cursor.fetchall()

        if not batch_results:
            break

        documents = []
        for row in batch_results:
            (store_name, city, zipcode, county, month, category_name,
                        item_description, vendor_names, total_orders,
                        total_bottles, total_sales, total_liters,
                        avg_vol, common_pack
                    ) = row
            
            record_id = str(row[0])

            if record_id in existing_ids:
                continue

            summary = (
                        f"In {month.strftime('%B %Y')}, {store_name} in {city}, {county} (ZIP: {zipcode}) sold "
                        f"{int(total_bottles)} bottles of \"{item_description}\" ({category_name}) for a total of ${total_sales:,.2f}. "
                        f"This was across {total_orders} orders. Average bottle size was {int(avg_vol)}ml, usually in {common_pack}-packs. "
                        f"Vendors included: {vendor_names}. Total volume: {int(total_liters)} liters."
                    )
            doc = Document(
                        page_content=summary,
                        metadata={
                            "record_id": record_id,
                            "store_name": store_name,
                            "item_description": item_description,
                            "category_name": category_name,
                            "month": month.strftime("%Y-%m"),
                            "city": city,
                            "county": county,
                            "zipcode": zipcode
                        }
                    )
            documents.append(doc)

        for i in range(0, len(documents), embeddings_batch_size):
            chunk = documents[i:i + embeddings_batch_size]
            if chunk:
                vectorstore.add_documents(chunk)
                for doc in chunk:
                    existing_ids.add(doc.metadata["record_id"])
                time.sleep(3)
                print(f"Embedded {len(chunk)} documents; total embedded so far = {total_processed + len(chunk)}")

        sql_offset += sql_batch_size
        total_processed += len(documents)
        

    cursor.close()
    conn.close()

    return vectorstore


vectorstore = build_pgvector_store(
        connection_string=db_connection_string,
        collection_name="vector_embeds",  
        table_name="liquorsales",         
        embeddings_batch_size=2000,
        sql_batch_size = 16000,
        max_rows=2622712
    )
print("Vector store ready.")