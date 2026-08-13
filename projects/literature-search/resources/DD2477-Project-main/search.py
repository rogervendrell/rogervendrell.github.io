import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from semantic_model import *

from make_users import UserGenerator

load_dotenv()

#docsFile = "test.json"
docsFile = "test_KTH_only.json"
esHost = "http://localhost:9200"
LEARNING_TO_RANK_MODEL_ID = "ltr-model-xgboost"


semanticIndexName = "semantic_index"
userIndex = "user_profiles"

def get_semantic_index_mapping(dims:int):
    return {
        "properties": {
            "PID": {
                "type": "long"
            },
            "Title": {
                "type": "text"
            },
            "Content": {
                "type": "text"
            },
            "Authors": {
                "type": "text"
            },
            "SemanticVector": {
                "type": "dense_vector",
                "dims": dims,
                "index": True,
                "similarity": "l2_norm"
            }
        }
    }

class Search:
    def __init__(self):
        self.es = Elasticsearch(hosts = [esHost],
                                #http_auth = (os.environ['ES_USERNAME'], os.environ['ES_PASSWORD'])) # <-- connection options need to be added here
                                api_key=os.environ['ES_API_KEY'])  # Added api key auth as an option, change to http_auth if preffered
        client_info = self.es.info()

        self.semanticModel = SemanticModel()

        print('Connected to Elasticsearch!')
        pprint(client_info.body)

    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(index='my_documents')

    def get_genre_preferences(self, user_id):
        return self.es.get(index=userIndex, id=user_id)["_source"]

    def insert_document(self, document):
        return self.es.index(index='my_documents', body=document) 
    
    def insert_documents(self, documents):
        operations = []
        i = 0
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append(document)
            self.insert_semantic_index(document)
            i += 1
            if i%10 == 0:
                print(f"processed {i} documents")

        return self.es.bulk(operations=operations)
    
    def reindex(self):
        self.create_index()
        with open(f'./Data/{docsFile}', 'rt') as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents)
    
    def search(self, **query_args):
        return self.es.search(index=semanticIndexName, **query_args)
        #return self.es.search(index='my_documents', **query_args)
    
    def retrieve_document(self, id):
        return self.es.get(index=semanticIndexName, id=id)
        return self.es.get(index='my_documents', id=id)
    
    def create_semantic_index(self):
        self.es.indices.delete(index=semanticIndexName, ignore_unavailable=True)
        self.es.indices.create(index=semanticIndexName, mappings=get_semantic_index_mapping(self.semanticModel.get_embedding_size()))
        ...

    def insert_semantic_index(self, doc):
        try:
            self.es.index(index=semanticIndexName, 
                          document={"PID": int(doc["PID"]),
                                    "Title": doc["Title"],
                                    "Content": doc["Content"], 
                                    "Authors": doc["Authors"],
                                    "SemanticVector": self.semanticModel.apply_model(doc["Content"])}, 
                                    id=int(doc["PID"]))
        except Exception as e:
            print(e)
        ...

    def search_semantic_index(self, queryText, size, from_, rescore=None):
        vectorQuery = self.semanticModel.apply_model(queryText)

        totalDocs = int(self.es.count(index=semanticIndexName)['count'])

        query = {
            "field": "SemanticVector",
            "query_vector": vectorQuery,
            "k" : totalDocs,
            "num_candidates": totalDocs,
        }

        return self.es.search(index=semanticIndexName, knn=query, rescore=rescore, source=["Title", "Content", "Authors"], from_=from_, size=size)
        ...

    def make_user_profiles(self):
        self.users = UserGenerator(self.es, semanticIndexName)
        self.users.make_user_profiles_from_csv("genres/docs_with_genres.csv")