Database:

To get the database up and running, run "docker-compose up -d", in the same folder as docker-compose.yml. Do "docker ps" to verify.
Then type "docker exec -it liquor_sales_IA_db mysql -u root -p" on your terminal and type in the root password written in the docker-compose.yml file.
This will give you access to the MySQL database and its tables.
