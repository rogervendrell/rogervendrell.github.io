#!/usr/bin/env python
# coding: utf-8

# ## Install required packages
# 
# First we must install the packages we need for this notebook.

# In[1]:


#get_ipython().system('pip install -qU elasticsearch eland "eland[scikit-learn]" xgboost tqdm')

from tqdm import tqdm

# Setup the progress bar so we can use progress_apply in the notebook.
tqdm.pandas()


# ## Other imports

# In[88]:


import json
import elasticsearch.helpers as es_helpers
import pandas as pd
from urllib.request import urlopen


# ## Configure your Elasticsearch deployment
# 
# For this example, we will be using an [Elastic Cloud](https://www.elastic.co/guide/en/cloud/current/ec-getting-started.html) deployment (available with a [free trial](https://cloud.elastic.co/registration?onboarding_token=vectorsearch&utm_source=github&utm_content=elasticsearch-labs-notebook)).

# In[89]:


import os
from elasticsearch import Elasticsearch

# https://www.elastic.co/search-labs/tutorials/install-elasticsearch/elastic-cloud#finding-your-cloud-id
# ELASTIC_CLOUD_ID = getpass("Elastic Cloud ID: ")

import os
from dotenv import load_dotenv

load_dotenv()

# https://www.elastic.co/search-labs/tutorials/install-elasticsearch/elastic-cloud#creating-an-api-key
ELASTIC_API_KEY = os.environ['ES_API_KEY']

# Create the client instance
es_client = Elasticsearch(
    # For local development
    hosts=["http://localhost:9200"],
    # for deployed elasticsearch
    # cloud_id=ELASTIC_CLOUD_ID,
    api_key=ELASTIC_API_KEY,
)


# ### Test the Client
# Before you continue, confirm that the client has connected with this test.

# In[90]:


client_info = es_client.info()

f"Successfully connected to cluster {client_info['cluster_name']} (version {client_info['version']['number']})"


# ## Configure the dataset
# 
# We'll use a dataset derived from the [MSRD (Movie Search Ranking Dataset)](https://github.com/metarank/msrd/tree/master).
# 
# The dataset is available [here](https://github.com/elastic/elasticsearch-labs/tree/main/notebooks/search/sample_data/learning-to-rank/) and contains the following files:
# 
# - `movies_corpus.jsonl.gz`: Movie dataset to be indexed.
# - `movies_judgements.tsv.gz`: Judgment list of relevance judgments for a set of queries.
# - `movies_index_settings.json`: Settings to be applied to the documents and index.

# In[91]:


DOCS_FILE = '../Data/export_Other_cs_kth_10k.csv'
DOCS_FILE_JSON = '../Data/test_KTH_only.json'
JUDGEMENTS_FILE = './data/query_data.csv'
INDEX_SETTINGS_URL = "./data/index-settings.json"


#  ## Import the documents
# 
# 

# In[92]:


import json
import elasticsearch.helpers as es_helpers
import pandas as pd

INDEX = "my_documents"

# Delete index
print("Deleting index if it already exists:", INDEX)
es_client.options(ignore_status=[400, 404]).indices.delete(index=INDEX)

print("Creating index:", INDEX)
with open(INDEX_SETTINGS_URL, 'r') as f:
    index_settings = json.load(f)
es_client.indices.create(index=INDEX, **index_settings)

print(f"Loading the corpus from {DOCS_FILE_JSON}")
try:
    corpus_df = pd.read_json(DOCS_FILE_JSON, lines=True)
except ValueError as e:
    print(f"Error reading JSON file: {e}")
    print("Attempting to load as a standard JSON file...")
    with open(DOCS_FILE_JSON, 'r') as f:
        corpus_data = json.load(f)
    corpus_df = pd.DataFrame(corpus_data)

print(f"Indexing the corpus into {INDEX} ...")
bulk_result = es_helpers.bulk(
    es_client,
    actions=[
        {"_id": doc["PID"], "_index": INDEX, **doc}
        for doc in corpus_df.to_dict("records")
    ],
)
print(f"Indexed {bulk_result[0]} documents into {INDEX}")


# ## Loading the judgment list
# 
# The judgment list contains human evaluations that we'll use to train our Learning To Rank model.
# 
# Each row represents a query-document pair with an associated relevance grade and contains the following columns:
# 
# | Column    | Description                                                            |
# |-----------|------------------------------------------------------------------------|
# | `query_id`| Pairs for the same query are grouped together and received a unique id. |
# | `author_id`| Author id                                             |
# | `query`   | Actual text of the query.                                             |
# | `PID`  | ID of the document.                                                    |
# | `score`   | The relevance grade of the document for the query.                     |
# 

# In[93]:


judgments_df = pd.read_csv(JUDGEMENTS_FILE, delimiter=",")
judgments_df


# ## Configure feature extraction
# 
# Features are the inputs to our model. They represent information about the query alone, a result document alone, or a result document in the context of a query, such as BM25 scores.
# 
# Features are defined using standard templated queries and the Query DSL.
# 
# To streamline the process of defining and refining feature extraction during training, we have incorporated a number of primitives directly in `eland`.
# 
# We are using elasticsearch scripts because we reach a limit due to the number of genres even when we max out the rate in the elasticsearch settings.

# In[211]:


from eland.ml.ltr import LTRModelConfig, QueryFeatureExtractor

preference_extractors = []

# Create a script that will look up preference values for each document
# "source": f"return params._source.containsKey('top{i}') ? params._source.top{i} : 0.0;",
for i in range(20):
    extractor = QueryFeatureExtractor(
        feature_name=f"top{i}",
        query={
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": f"{{{{top{i}}}}}"
                }
            }
        }
    )
    preference_extractors.append(extractor)


ltr_config = LTRModelConfig(
    feature_extractors=[
        # For the following field we want to use the score of the match query for the field as a features:
        QueryFeatureExtractor(
            feature_name="title_bm25", query={"match": {"Title": "{{query}}"}}
        ),
        QueryFeatureExtractor(
            feature_name="content_bm25", query={"match": {"Content": "{{query}}"}}
        ),
        QueryFeatureExtractor(
            feature_name="author_bm25", query={"match": {"Authors": "{{query}}"}}
        ),
        QueryFeatureExtractor(
            feature_name="title_all_terms_bm25",
            query={
                "match": {
                    "Title": {"query": "{{query}}", "minimum_should_match": "100%"}
                }
            },
        ),
        # One-hot encode genre categories. Make sure `genre` is of type `keyword`.
        QueryFeatureExtractor(
            feature_name="is_0",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Biology / Medicine"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_1",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Cloud / Server / API"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_2",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Clustering"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_3",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Computer Networks / Communication"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_4",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Computer Vision / 3D"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_5",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Data Structures"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_6",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Databases"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_7",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Databases"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_8",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Machine Learning / Deep Learning"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_9",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Marketing / Business"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_10",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Mathematics / Theory"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_11",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Mobile Applications"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_12",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Natural Language Processing"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_13",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Optimization / Algorithms"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_14",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Privacy / Security"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_15",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Robotics"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_16",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Scheduling / Planning"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_17",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Software Engineering"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_18",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Theoretical Computer Science"}},
                "boost": 1,
            }
            },
        ),
        QueryFeatureExtractor(
            feature_name="is_19",
            query={
            "constant_score": {
                "filter": {"term": {"Genre": "Visualisation"}},
                "boost": 1,
            }
            },
        ),
        *preference_extractors
    ]
)


# For this implementation I increased the rate limit of my elasticsearch instance since the default was not sufficient for the number of parameters.
# 
# In Kibana/Postman:

# ```
# PUT http://localhost:9200/_cluster/settings
# ```
# and in the body of the request:
# ```
# {
#   "persistent": {
#     "script.max_compilations_rate": "100000/5m"
#   }
# }
# ```

# In[213]:


import numpy as np

from eland.ml.ltr import FeatureLogger
PREFERENCES_INDEX = "user_profiles"

# First we create a feature logger that will be used to query Elasticsearch to retrieve the features:
feature_logger = FeatureLogger(es_client, INDEX, ltr_config)

def get_genre_preferences(es_client, index_name, user_id):
    return es_client.get(index=index_name, id=user_id)["_source"]


def extract_query_features(es_client, query_judgements_group):
    query_string = query_judgements_group["query"].iloc[0]
    user_id = query_judgements_group["author_id"].iloc[0]
    doc_ids = query_judgements_group["PID"].astype("str").to_list()

    try:
        genre_preferences = get_genre_preferences(es_client, PREFERENCES_INDEX, user_id)


        query_params = {
            "query": query_string,
        }

        # Add each preference parameter explicitly
        for i in range(20):
            pref_key = f"top{i}"
            query_params[pref_key] = float(genre_preferences.get(pref_key, 0.0))


        print(f"Query parameters sample: {json.dumps({k: v for k, v in query_params.items() if k.startswith('top') and v != 0.0}, indent=2)}")

        doc_features = feature_logger.extract_features(query_params, doc_ids)
        # For debugging
        print(f"Successfully extracted features for {len(doc_features)} documents")
        # Debug: Show the actual feature values for the first document
        if doc_features and len(doc_ids) > 0:
            first_doc = doc_ids[0]
            if first_doc in doc_features:
                feature_dict = {
                    feature_name: doc_features[first_doc][idx]
                    for idx, feature_name in enumerate(ltr_config.feature_names)
                }
                print(f"Features for first document ({first_doc}):")
                for feature_name, value in feature_dict.items():
                    if feature_name.startswith("top"):
                        print(f"  - {feature_name}: {value}")
            else:
                print(f"No features found for first document {first_doc}")
        # Process each feature
        for feature_index, feature_name in enumerate(ltr_config.feature_names):
            # Get feature values for each document ID
            feature_values = np.array([
                doc_features.get(doc_id, [0.0] * len(ltr_config.feature_names))[feature_index]
                for doc_id in doc_ids
            ])

            # Handle missing values
            if feature_values.dtype == np.float64 or feature_values.dtype == np.float32:
                feature_values = np.nan_to_num(feature_values, nan=0.0)

            # Add feature values to the dataframe
            query_judgements_group[feature_name] = feature_values 
    except Exception as e:
        print(f"Error extracting features: {str(e)}")
        # Log detailed error information
        print(f"Query parameters: {json.dumps(query_params, indent=2)}")
        print(f"Document IDs: {doc_ids[:5]}...")  # Show first 5 for brevity
        raise e

    return query_judgements_group

# Main execution function
def process_judgments(es_client, judgments_df):
    """Process all judgments, extracting features for each query group"""

    # Process each query group
    judgments_with_features = judgments_df.groupby(
        "query_id", group_keys=False
    ).apply(lambda group: extract_query_features(es_client, group))

    return judgments_with_features


judgments_with_features = process_judgments(es_client, judgments_df)

judgments_with_features


# ## Building the training dataset
# 
# Checking the values look alright

# In[214]:


judgments_with_features[[f"is_{i}" for i in range(20)]]


# In[215]:


judgments_with_features[[f"top{i}" for i in range(20)]]


# ## Create and train the model
# 
# The LTR rescorer supports XGBRanker trained models.
# 
# Learn more in the [XGBoost documentation](https://xgboost.readthedocs.io/en/latest/tutorials/learning_to_rank.html).

# In[216]:


from xgboost import XGBRanker
from sklearn.model_selection import GroupShuffleSplit


# Create the ranker model:
ranker = XGBRanker(
    objective="rank:ndcg",
    eval_metric=["ndcg@10"],
    early_stopping_rounds=20,
)

# Shaping training and eval data in the expected format.
X = judgments_with_features[ltr_config.feature_names]
y = judgments_with_features["score"]
groups = judgments_with_features["query_id"]

# Split the dataset in two parts respectively used for training and evaluation of the model.
group_preserving_splitter = GroupShuffleSplit(n_splits=1, train_size=0.8).split(
    X, y, groups
)
train_idx, eval_idx = next(group_preserving_splitter)

train_features, eval_features = X.loc[train_idx], X.loc[eval_idx]
train_target, eval_target = y.loc[train_idx], y.loc[eval_idx]
train_query_groups, eval_query_groups = groups.loc[train_idx], groups.loc[eval_idx]

# Training the model
ranker.fit(
    X=train_features,
    y=train_target,
    group=train_query_groups.value_counts().sort_index().values,
    eval_set=[(eval_features, eval_target)],
    eval_group=[eval_query_groups.value_counts().sort_index().values],
    verbose=True,
)


# In[217]:


from xgboost import plot_importance

plot_importance(ranker, importance_type="weight");


# ## Import the model into Elasticsearch
# 
# Once the model is trained we can use Eland to load it into Elasticsearch.
# 
# Please note that the `MLModel.import_ltr_model` method contains the `LTRModelConfig` object which defines how features should be extracted for the model being imported.

# In[218]:


from eland.ml import MLModel

LEARNING_TO_RANK_MODEL_ID = "ltr-model-xgboost"

MLModel.import_ltr_model(
    es_client=es_client,
    model=ranker,
    model_id=LEARNING_TO_RANK_MODEL_ID,
    ltr_model_config=ltr_config,
    es_if_exists="replace",
)


# ## Using the rescorer

# In[219]:


query = "machine learning"

# First let's display the result when not using the rescorer:
search_fields = ["Title", "Content", "Authors"]
bm25_query = {"multi_match": {"query": query, "fields": search_fields}}
bm25_search_response = es_client.search(index=INDEX, query=bm25_query)
print(bm25_search_response["hits"]["hits"][0]["_source"])

[
    (document["_source"]["Title"], document["_score"], document["_id"])
    for document in bm25_search_response["hits"]["hits"]
]


# In[224]:


# Now let's display result when using the rescorer:
# user_id = 37

user_id = 999
genre_preferences = get_genre_preferences(es_client, PREFERENCES_INDEX, user_id)
# print(genre_preferences)
search_params = {k: genre_preferences[k] for k in genre_preferences if k.startswith("top")}
ltr_rescorer = {
    "learning_to_rank": {
        "model_id": LEARNING_TO_RANK_MODEL_ID,
        "params": {"query": query,
                   **search_params},
    },
    "window_size": 100,
}
print(search_params)
print(user_id)
# Run the search
response = es_client.search(index=INDEX, query=bm25_query, rescore=ltr_rescorer, explain=True)
# print(response["hits"]["hits"])

# Preview top results
results = [
    (doc["_score"], doc["_source"]["Title"],  doc["_explanation"], doc["_id"])
    for doc in response["hits"]["hits"]
]
for result in results:
    print(result)
# explanation = results[0][2]

