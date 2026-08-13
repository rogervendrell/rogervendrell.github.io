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
        "window_size": from_ + size,
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
        "window_size": from_ + size,
    }
    results = es.search(
        query={
            'multi_match': {
                'query': query,
                'fields': ['Title', 'Content', 'Authors'],
            },
        }, 
        rescore=ltr_rescorer, size=size, from_=from_
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

def NDCG(results:list[str], relevant:dict[str, int], p:int):
    # Ensure p does not exceed the number of returned results
    p = min(p, len(results))

    # Compute DCG@p
    dcg = 0.0
    for i in range(p):
        rel = relevant.get(results[i], 0)
        dcg += rel  / math.log2(i + 2)

    # Compute ideal DCG@p (IDCG)
    # Sort true relevances in descending order and take the top p
    ideal_rels = sorted(relevant.values(), reverse=True)[:p]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels):
        idcg += rel / math.log2(i + 2)

    # Normalize
    return dcg / idcg if idcg > 0 else 0.0
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

sem_search_ndcp = []
lex_search_ndcp = []

sem_search_ndcp_auth = []

for query in queriesToRun:
    queryText = query[0]
    authorID = int(query[1])
    relevant = query[2] # Dict[str, int]

    lex_ids = []
    sem_ids = []
    sem_auth_ids = []
    for i in range(5):
        f = 10*i
        p = 10

        lex_results = lexical_search(query=queryText, from_=f, size=p)
        sem_results = semantic_search(query=queryText, from_=f, size=p)
        sem_results_auth = semantic_search_with_author(query=queryText, author=authorID, from_=f, size=p)
    
        for i in range(p):
            lex_ids.append(lex_results[i]['_id'])
            sem_ids.append(sem_results[i]['_id'])
            sem_auth_ids.append(sem_results_auth[i]['_id'])
    print("ids length:", len(sem_auth_ids))
    sem_search_ndcp.append(NDCG(sem_ids, relevant, p))
    sem_search_ndcp_auth.append(NDCG(sem_auth_ids, relevant, p))
    lex_search_ndcp.append(NDCG(lex_ids, relevant, p))


print("Lexical Search NDCGs",lex_search_ndcp)
print("Semantic Search NDCGs",sem_search_ndcp)
print("Semantic Search with authors NDCGs",sem_search_ndcp_auth)



