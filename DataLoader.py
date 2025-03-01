import time
from sodapy import Socrata
import psycopg2

def safe_int(val):
    """Convert value to int safely; returns None if conversion fails."""
    try:
        return int(val)
    except:
        return None

def safe_float(val):
    """Convert value to float safely; returns None if conversion fails."""
    try:
        return float(val)
    except:
        return None

# Sleep to allow MySQL time to initialize
print("Waiting 30 seconds for MySQL to start...")
time.sleep(30)

# Connect to Socrata
client = Socrata("data.iowa.gov", None)

# Connect to MySQL
print("Attempting to connect to PostgreSQL...")
db_conn = psycopg2.connect(
    host="db",
    user="root",                 
    password="cs620ibdc1234",         
    dbname="IowaLiquorSales"       
)
cursor = db_conn.cursor()

check = True
ofst = 0

while check:
    # Fetch 10,000 rows at a time
    results = client.get("cc6f-sgik", limit=10000, offset=10000 * ofst)
    
    if len(results) == 0:
        check = False
        break

    ofst += 1
    print(f"Inserting batch {ofst} ...")

    for row in results:
        # Extract fields from the API response
        invoice_line_no   = row.get("invoice_line_no", None)
        date_str          = row.get("date", None)
        store             = row.get("store", None)
        name              = row.get("name", None)
        address           = row.get("address", None)
        city              = row.get("city", None)
        zipcode           = row.get("zipcode", None)
        county_number     = row.get("county_number", None)
        county            = row.get("county", None)
        category          = row.get("category", None)
        category_name     = row.get("category_name", None)
        vendor_no         = row.get("vendor_no", None)
        vendor_name       = row.get("vendor_name", None)
        itemno            = row.get("itemno", None)
        im_desc           = row.get("im_desc", None)
        pack_             = safe_int(row.get("pack", None))
        bottle_volume_ml  = safe_float(row.get("bottle_volume_ml", None))
        state_bottle_cost = safe_float(row.get("state_bottle_cost", None))
        state_bottle_retail = safe_float(row.get("state_bottle_retail", None))
        sale_bottles      = safe_int(row.get("sale_bottles", None))
        sale_dollars      = safe_float(row.get("sale_dollars", None))
        sale_liters       = safe_float(row.get("sale_liters", None))
        sale_gallons      = safe_float(row.get("sale_gallons", None))
        
        # Process store_location as a WKT string
        location_data = row.get("store_location", None)
        if isinstance(location_data, dict) and "coordinates" in location_data:
            coords = location_data["coordinates"]
            if len(coords) == 2:
                # Socrata returns coordinates as [longitude, latitude]
                lon = safe_float(coords[0])
                lat = safe_float(coords[1])
                if lon is not None and lat is not None:
                    wkt = f"POINT({lon} {lat})"
                else:
                    wkt = None
            else:
                wkt = None
        else:
            wkt = None

        # Build SQL for insertion using ST_GeomFromText to convert WKT to a POINT
        sql = """
            INSERT INTO LiquorSales (
                invoice_line_no, date, store, name, address, city, zipcode,
                store_location, county_number, county, category, category_name,
                vendor_no, vendor_name, itemno, im_desc, pack, bottle_volume_ml,
                state_bottle_cost, state_bottle_retail, sale_bottles, sale_dollars,
                sale_liters, sale_gallons
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                ST_GeomFromText(%s),
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
        """
        cursor.execute(sql, (
            invoice_line_no, date_str, store, name, address, city, zipcode,
            wkt,
            county_number, county, category, category_name,
            vendor_no, vendor_name, itemno, im_desc,
            pack_, bottle_volume_ml, state_bottle_cost, state_bottle_retail,
            sale_bottles, sale_dollars, sale_liters, sale_gallons
        ))

    db_conn.commit()

cursor.close()
db_conn.close()
print("Data load complete!")
