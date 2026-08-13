# DD2477-Project
Search Engines and Information Retrieval Systems Project: Searching the scientific literature

## Adding any libraries:
Remember to run the command:
```
$ pip freeze > requirements.txt
```

## Setup libraries:
Recommended: 
Create a python virtual environment using `python3 -m venv venv` and activate it with `source venv/bin/activate` 

```
$ pip install -r requirements.txt
```
## Run Elastic Search
Quick set up:

Download docker then run the following command in your terminal 
```
$ curl -fsSL https://elastic.co/start-local | sh
```

## Environment Variables
Create a .env file with the following:
```
ES_USERNAME="your_es_username"
ES_PASSWORD="your_es_password"
ES_API_KEY="your_es_API_key"
```

## Running the app
Recommended: Create a python virtual environment using `python3 -m venv venv` and activate it with `source venv/bin/activate` 

After installing via the `pip install -r requirements.txt` 

- To index the documents:
```
$ flask reindex 
```

- To index users and their preferences:
```
$ flask makeusers
```
- For personalized search, you need to have the local model in your machine. Please run the notebook `personalized-search/08-learning-to-rank.ipynb`. Please note the instructions regarding changing the rate limit of Elasticsearch in the "Configure feature extraction" section.

- You can also changing the rate limit using the following curl command, just replace "BASE64_ENCODED_ID_AND_KEY" with your API key
```
curl -X PUT "http://localhost:9200/_cluster/settings" \
     -H "Content-Type: application/json" \
     -H "Authorization: ApiKey BASE64_ENCODED_ID_AND_KEY" \
     -d '{
       "persistent": {
         "script.max_compilations_rate": "100000/5m"
       }
     }'

```

- Run the app with `flask run` OR `python3 -m flask run`

# Methodology:
## General Search

## Personalized Search
1. Coauthors
To see how popular other works/authors are with each other we create a graph with authors that have collaborated with each other.
`cd coauthorsgraph` and run the notebook `coauthorsgraph.ipynb`. Two CSV files `graph.csv` and `id-to-author` will be made in the folder `coauthorsgraph/graph`

2. Generating queries
- To train the model, we use keywords made per author to generate queries per author. How related authors are too each other influences the relevance of the resulting document PIDs. `cd personalized-search` and run ` python uniqueAuthors.py` to create a set of all keywords and PIDs, as well as authors with PIDs. 

- Wih this information, we can now generate our query data. Run the notebook `create-query-data.ipynb` to create our `query_data.csv` 

3. Training the model
*IMPORTANT* You must have your own local model for elasticsearch to reference to when running personalized search locally.
Run the notebook `personalized-search/learning-to-rank.ipynb` to have a local model in your machine.
