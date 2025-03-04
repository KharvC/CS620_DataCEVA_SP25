**Database:**

Run these commands to get the data loaded:
1. `docker-compose down -v` (optional: run this only if you had docker up before)
2. `docker-compose up --build -d`

The data is now being loaded to the PostgreSQL, but it takes a while as we have to load 2.6 million rows, 10,000 at a time:
In the meantime to check if it's being loaded, open a new terminal and connect to the database using these commands:
1. `docker exec -it liquor_sales_IA_db psql -U root -d IowaLiquorSales;`
2. `SELECT COUNT(*) FROM LiquorSales;` (keep running this in 30 second intervals to see rows of data being uploaded)
