import re
from flask import Flask, render_template, request

from search import Search


app = Flask(__name__)
es = Search()

LEARNING_TO_RANK_MODEL_ID = "ltr-model-xgboost"

@app.get('/')
def index():
    return render_template('index.html')


@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    from_ = request.form.get('from_', type=int, default=0)
    author = request.form.get('author', type=int)
    semantic_search = request.form.get('semantic_search') == 'on'  # checkbox sends 'on' when checked
    # get genre preferences
    print(f"author {author}")
    print(f"semantic_search {semantic_search}")
    if semantic_search:
        print("doing semantic search")
        results = {}
        if (author is not None and author > -1):
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
            results = es.search_semantic_index(queryText=query, size=10, from_=from_, rescore=ltr_rescorer)
        else:
            results = es.search_semantic_index(queryText=query, size=10, from_=from_)
    else:  
        print("doing simple search")
        results = {}
        if (author is not None and author > -1):
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
        else:
            results = es.search(
                query={
                    'multi_match': {
                        'query': query,
                        'fields': ['Title', 'Content', 'Authors'],
                    },
                }, size=10, from_=from_
            )

    return render_template(
        'index.html', query=query, results=results['hits']['hits'], semantic_search=semantic_search,
        from_=from_, author=author, total=results['hits']['total']['value'])

@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document['_source']['Title']
    paragraphs = document['_source']['Content'].split('\n')
    return render_template('document.html', title=title, paragraphs=paragraphs)


@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    print(f'Index with {len(response["items"])} documents created '
          f'in {response["took"]} milliseconds.')
    # And add users
    es.make_user_profiles()

@app.cli.command()
def makeusers():
    """Make the user profiles"""
    es.make_user_profiles()
