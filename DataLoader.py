from sodapy import Socrata
import mysql.connector

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

# Connect to Socrata
client = Socrata("data.iowa.gov", None)

# Connect to MySQL
db_conn = mysql.connector.connect(
    host="db",
    user="root",
    password="cs620ibdc1234",    # Update if your password differs
    database="IowaLiquorSales"
)
cursor = db_conn.cursor()

check = True
ofst = 0

while check:
    # Fetch 10k rows at a time
    results = client.get("cc6f-sgik", limit=10000, offset=10000 * ofst)
    
    if len(results) == 0:
        # No more data
        check = False
        break

    ofst += 1
    print(f"Inserting batch {ofst} ...")

    for row in results:
        # Extract columns from the API response
        invoice_line_no   = row.get("invoice_line_no", None)
        date_str          = row.get("date", None)  # MySQL can parse some date strings automatically
        store             = row.get("store", None)
        name              = row.get("name", None)
        address           = row.get("address", None)
        city              = row.get("city", None)
        zipcode           = row.get("zipcode", None)  # Confirm the field name from Socrata
        county_number     = row.get("county_number", None)
        county            = row.get("county", None)
        category          = row.get("category", None)
        category_name     = row.get("category_name", None)
        vendor_no         = row.get("vendor_no", None)
        vendor_name       = row.get("vendor_name", None)
        itemno            = row.get("itemno", None)
        im_desc           = row.get("im_desc", None)   # or "item_description" if that’s the actual field
        pack_             = safe_int(row.get("pack", None))
        bottle_volume_ml  = safe_float(row.get("bottle_volume_ml", None))
        state_bottle_cost = safe_float(row.get("state_bottle_cost", None))
        state_bottle_retail = safe_float(row.get("state_bottle_retail", None))
        sale_bottles      = safe_int(row.get("sale_bottles", None))
        sale_dollars      = safe_float(row.get("sale_dollars", None))
        sale_liters       = safe_float(row.get("sale_liters", None))
        sale_gallons      = safe_float(row.get("sale_gallons", None))

        # Handle store_location if present (may be lat/lon or a nested object)
        # Adjust based on how your Socrata location field is structured
        # Example: {"type":"Point","coordinates":[-93.1234, 41.1234]}
        location_data = row.get("store_location", None)
        lat, lon = None, None
        if isinstance(location_data, dict) and "coordinates" in location_data:
            coords = location_data["coordinates"]
            if len(coords) == 2:
                lon, lat = coords[0], coords[1]  # Socrata often returns [lon, lat]

        # Build SQL for insertion
        # Option 1: Use MySQL's POINT() directly (works in many MySQL setups)
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
                POINT(%s, %s),
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
        """

        # Execute insert row by row
        cursor.execute(sql, (
            invoice_line_no, date_str, store, name, address, city, zipcode,
            lat, lon,   # used for POINT(lat, lon)
            county_number, county, category, category_name,
            vendor_no, vendor_name, itemno, im_desc,
            pack_, bottle_volume_ml, state_bottle_cost, state_bottle_retail,
            sale_bottles, sale_dollars, sale_liters, sale_gallons
        ))

    # Commit every batch of 10k rows
    db_conn.commit()

# Cleanup
cursor.close()
db_conn.close()
print("Data load complete!")