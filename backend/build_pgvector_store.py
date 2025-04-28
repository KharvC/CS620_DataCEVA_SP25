import psycopg2
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import PGVector
from langchain.docstore.document import Document
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
db_connection_string = os.getenv("POSTGRESQL_URI")

def build_pgvector_store(
    table_name: str = "liquorsales",
    collection_name: str = "vector_embeds",
    batch_size: int = 100,
    max_rows: int = 10000
):
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    vectorstore = PGVector(
        connection_string=db_connection_string,
        collection_name=collection_name,
        embedding_function=embeddings
    )

    # Keep track of existing record_ids to skip duplicates
    existing_ids = set()
    with psycopg2.connect(db_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT metadata->>'record_id' FROM {collection_name};")
            rows = cur.fetchall()
            existing_ids = {r[0] for r in rows if r[0] is not None}

    offset = 0
    total_processed = 0

    while total_processed < max_rows:
        with psycopg2.connect(db_connection_string) as conn:
            with conn.cursor() as cursor:
                query = f"""
                SELECT
                    name AS store_name,
                    MIN(city) AS city,
                    MIN(zipcode) AS zipcode,
                    MIN(county) AS county,
                    DATE_TRUNC('month', date) AS month,
                    category_name,
                    im_desc AS item_description,
                    STRING_AGG(DISTINCT vendor_name, ', ') AS vendor_names,
                    COUNT(*) AS total_orders,
                    SUM(sale_bottles) AS total_bottles,
                    SUM(sale_dollars) AS total_sales,
                    SUM(sale_liters) AS total_liters,
                    AVG(bottle_volume_ml) AS avg_bottle_volume,
                    MODE() WITHIN GROUP (ORDER BY pack) AS common_pack
                FROM {table_name}
                GROUP BY name, im_desc, DATE_TRUNC('month', date), category_name
                ORDER BY name, item_description, month
                LIMIT {batch_size} OFFSET {offset};
                """

                cursor.execute(query)
                rows = cursor.fetchall()

                if not rows:
                    print("No more rows to process.")
                    break

                documents = []

                for row in rows:
                    (
                        store_name, city, zipcode, county, month, category_name,
                        item_description, vendor_names, total_orders,
                        total_bottles, total_sales, total_liters,
                        avg_vol, common_pack
                    ) = row

                    record_id = f"{store_name.lower().replace(' ', '_')}-{item_description.lower().replace(' ', '_')}-{month.strftime('%Y-%m')}"

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

                if documents:
                    vectorstore.add_documents(documents)
                    total_processed += len(documents)
                    offset += batch_size
                    print(f"✅ Stored {len(documents)} documents — total processed: {total_processed}")

    print("🎯 Done loading vector store!")

if __name__ == "__main__":
    build_pgvector_store()
