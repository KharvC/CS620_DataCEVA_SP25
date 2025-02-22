DROP TABLE IF EXISTS LiquorSales;

CREATE TABLE LiquorSales(
    invoice_line_no TEXT,
    date TIMESTAMP,
    store TEXT,
    name TEXT,
    address TEXT,
    city TEXT,
    zipcode TEXT,
    store_location POINT,
    county_number TEXT,
    county TEXT,
    category TEXT,
    category_name TEXT,
    vendor_no TEXT,
    vendor_name TEXT,
    itemno TEXT,
    im_desc TEXT,
    pack INTEGER,
    bottle_volume_ml FLOAT,
    state_bottle_cost FLOAT,
    state_bottle_retail FLOAT,
    sale_bottles INTEGER,
    sale_dollars FLOAT,
    sale_liters FLOAT,
    sale_gallons FLOAT
);