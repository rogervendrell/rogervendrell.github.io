from search import *
import math
import json

es = Search()

queriesFile = "TestQueries.json"

def semantic_search_with_author(query, author, from_, size):
    genre_preferences = es.get_genre_preferences(author)
    search_params = {k: genre_preferences[k] for k in genre_preferences if k.startswith("top")}
    ltr_rescorer = {
        "learning_to_rank": {
            "model_id": LEARNING_TO_RANK_MODEL_ID,
            "params": {"query": query,
                    **search_params},
        },
        "window_size": 100,
    }
    results = es.search_semantic_index(queryText=query, size=size, from_=from_, rescore=ltr_rescorer)
    return results['hits']['hits']
    ...

def semantic_search(query, from_, size):
    results = es.search_semantic_index(queryText=query, size=size, from_=from_)
    return results['hits']['hits']
    ...

def lexical_search_with_author(query, author, from_, size):
    genre_preferences = es.get_genre_preferences(author)
    search_params = {f"top{i}": genre_preferences[f"top{i}"] for i in range(20)} # 20 genres
    search_params = {k: genre_preferences[k] for k in genre_preferences if k.startswith("top")}
    ltr_rescorer = {
        "learning_to_rank": {
            "model_id": LEARNING_TO_RANK_MODEL_ID,
            "params": {"query": query,
                    **search_params},
        },
        "window_size": 100,
    }
    results = es.search(
        query={
            'multi_match': {
                'query': query,
                'fields': ['Title', 'Content', 'Authors'],
            },
        }, 
        rescore=ltr_rescorer, size=10, from_=from_
    )

    return results['hits']['hits']
    ...

def lexical_search(query, from_, size):
    results = es.search(
        query={
            'multi_match': {
                'query': query,
                'fields': ['Title', 'Content', 'Authors'],
            },
        }, size=size, from_=from_
    )
    
    return results['hits']['hits']
    ...

def readJSON():
    with open(queriesFile, 'r', encoding='utf-8') as f:
        data = json.load(f)  

    results = []
    for entry in data:
        
        query = entry['query']
        author = entry['author']
        relevant_results = entry['relevantResults']

        results.append((query, author, relevant_results))

    return results
    ...

queriesToRun = readJSON()

p=50

for query in queriesToRun:
    queryText = query[0]
    authorID = int(query[1])

    lex_results = lexical_search(query=queryText, from_=0, size=p)
    sem_results = semantic_search(query=queryText, from_=0, size=p)
    auth_results = semantic_search_with_author(query=queryText, author=authorID, from_=0, size=p)

    pidSet = {"PID SET"}

    responseList = []

    for i in range(p):
        if lex_results[i]['_id'] not in pidSet:
            responseList.append((lex_results[i]['_id'], lex_results[i]['_source']['Title'], lex_results[i]['_source']['Content']))
            pidSet.add(lex_results[i]['_id'])

        if sem_results[i]['_id'] not in pidSet:
            responseList.append((sem_results[i]['_id'], sem_results[i]['_source']['Title'], sem_results[i]['_source']['Content']))
            pidSet.add(lex_results[i]['_id'])

        if auth_results[i]['_id'] not in pidSet:
            responseList.append((auth_results[i]['_id'], auth_results[i]['_source']['Title'], auth_results[i]['_source']['Content']))
            pidSet.add(lex_results[i]['_id'])
    
    print("***Query Start***")
    print("Query:", queryText)
    print("Author ID:", authorID)
    print("Results: ")
    pprint(responseList)
    print("***Query End***")

