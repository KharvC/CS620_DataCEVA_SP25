# Link to Repo
 
[DataCEVA Git Repository](https://github.com/KharvC/CS620_DataCEVA_SP25)

## Project Overview

This project involves setting up a database, leveraging powerful LLMs, developing custom logic for data retrieval, and building an intuitive front-end to facilitate seamless user interaction. The goal is to bridge the gap between raw data and actionable intelligence, empowering businesses with smarter, data-driven decision-making.

## Customer Persona

The target users for this project include business analysts, sales managers, and data-driven decision-makers who need quick and accurate insights from their datasets without requiring deep technical expertise.

## Setup Steps

Step 1: Setup .env files

- You will need two .env files (one in the `backend` directory and one in the `CS620_DataCEVA_SP25` directory)
- Example of .env file in `backend` directory:

```
SECRET_KEY= //your secret key
REFRESH_SECRET_KEY= //your refresh secret key
OPENAI_API_KEY= //your openai key
POSTGRESQL_URI= //your postgresql connection link
```

- Example of .env file in `CS620_DataCEVA_SP25` directory:

```
OPENAI_API_KEY= //your openai key
POSTGRESQL_URI= //your postgresql connection link
```

Step 2: Run pip install for requirements.txt

- Run this code block (make sure to be in the `backend` directory when running this line):

```
pip install requirements.txt
```

Step 3: Running code to setup backend

- Run this code block (make sure to be in the `backend` directory when running this line):

```
uvicorn main:app
```

Step 4: Running code to startup application

- Run this code block (make sure to be in the `just-ask-ai` directory when running this line):

```
npm install
npm run dev
```

**Note**