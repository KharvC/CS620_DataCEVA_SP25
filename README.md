## Link to Repo
 
[DataCEVA Git Repository](https://github.com/KharvC/CS620_DataCEVA_SP25)

## Project Overview

This project involves setting up a database, leveraging powerful LLMs, developing custom logic for data retrieval, and building an intuitive front-end to facilitate seamless user interaction. The goal is to bridge the gap between raw data and actionable intelligence, empowering businesses with smarter, data-driven decision-making.

## Customer Persona

The target users for this project include business analysts, sales managers, and data-driven decision-makers who need quick and accurate insights from their datasets without requiring deep technical expertise.

## Setup Steps

**Step 1**: Setup .env files

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

**Step 2**: Run pip install for requirements.txt

- Run this code block (make sure to be in the `backend` directory when running this line):

```
pip install requirements.txt
```

**Step 3**: Running code to setup backend

- Run this code block (make sure to be in the `backend` directory when running this line):

```
uvicorn main:app
```

**Step 4**: Running code to startup application

- Run this code block (make sure to be in the `just-ask-ai` directory when running this line):

```
npm install
npm run dev
```

*Note*: make sure you have nodejs, npm, and pip installed to successfully run the code blocks for setup

## Overview of Code

Once the application is running, you will need to register a username and password if you do not have one already. Otherwise, login using your username and password.

Once in the chatbox, ask question related to your data (for example, how many sales have I had in the first quarter?). The LLM will then generate a quick answer by retrieving data from your database in order to give an accurate response to your question.

### In-Depth Overview

#### Backend
- **Login**: `auth.py`, `database.py`, `models.py`
- - Testing
- **Vector embedding creation**: `embed.py`
- **SQL + RAG**: `main.py`, `main_rag.py`

#### Frontend
- **Logic**: `App.jsx`
- **Styling**: `App.css`, `index.css`
- **Dependencies**: `package.json`


## What Works and What Doesn't Work

As of now, our application is running on SQL queries since using RAG takes a long time to generate an answer. Our application is fully functional
and we are able to get accurate answers based on the given database.

As mentioned before, RAG is taking a lot of time to generate an answer, but we do have the vector embeddings to continue with trying to implement
RAG in a way where the time it takes to generate an answer is significanlty reduced.

## What We Would Work On Next

We would implement an indexing strategy (ANN indexing, specifically IVFFlat) in order to reduce the time it takes for the application to reduce the time it takes to search through the vector embeddings to find relevant data to answer the user's inquiry.

Although we have vector embeddings with dimensions, we would also look into creating vector embeddings with smaller dimensions.

Another thing we would like to implement is chat retention so users can access previous chat logs.

The last thing we would like to work on is potentially improving the look of the UI, making it more aesthetically pleasing.