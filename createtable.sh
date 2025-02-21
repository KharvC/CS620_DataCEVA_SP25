#!/bin/bash

# Starts the MySQL service
docker-compose up -d

# Installs sodapy and mysql connector for Python
pip install sodapy
pip install mysql-connector-python

# Makes sure that enough time has been given to MySQL sevice to be set up
sleep 7

# Runs the SQL queries to create the table
docker exec -i liquor_sales_IA_db mysql -u root -pcs620ibdc1234 <<EOF
USE IowaLiquorSales;
SOURCE /docker-entrypoint-initdb.d/create.sql;
EOF

# Runs a python script to insert data from Iowa liquor sales website into a table in the database
python DataLoader.py