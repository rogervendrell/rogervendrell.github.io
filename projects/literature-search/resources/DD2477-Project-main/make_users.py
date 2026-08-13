from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
import os
import csv
import json
import ast


author_id_file = "authors_with_pids.csv"
id_path = "personalized-search/data/"
topic_format_file = "genres/genres.txt"

class UserGenerator:
    def __init__(self, es, doc_index):
        self.client = es
        self.doc_index = doc_index
        self.usr_index = "user_profiles"
        self.name_to_sim_vec = {}
        self.id_to_name = {}
        self.user_to_int()
        self.read_topics()

    # Creates a dictionary translating author name to corresponding id - also inverse
    def user_to_int(self):
        # Create the author name to id dict
        self.name_to_id = {}
        # Create id to number of docs dict
        # Go through the csv
        with open(id_path + author_id_file, 'r') as file:
            reader = csv.reader(file, delimiter=';')
            # Want to skip first row with column names
            firstrow = True
            for row in reader:
                if firstrow:
                    firstrow = False
                    continue
                # Add to dict - [0] is the author name and [1] is the id
                self.name_to_id[row[0]] = row[1]
                self.id_to_name[row[1]] = row[0]
    
    # Constructs a list with all topics from file
    def read_topics(self):
        self.topics = []
        i = 0
        with open(topic_format_file, 'r') as file:
            for topic in file:
                self.topics.append(topic.strip())

    def add_similarity(self, author, sim_vec):
        # Check if the author already has a vector
        if author not in self.name_to_sim_vec:
            # No vector found - set this one
            self.name_to_sim_vec[author] = sim_vec
        else:
            # Vector found - add them together in a fancy pythonic way
            self.name_to_sim_vec[author] = [sum(x) for x in zip(self.name_to_sim_vec[author], sim_vec)]

    def normalize_sim_vecs(self):
        for author in self.name_to_sim_vec:
            sim_sum = sum(self.name_to_sim_vec[author])
            # Divide all elements by sum in fancy pythonic way
            self.name_to_sim_vec[author] = [x / sim_sum for x in self.name_to_sim_vec[author]]

    # Create the doc representing the author
    def create_doc(self, author):
        doc = {}
        for i in range(len(self.name_to_sim_vec[author])):
            topic = 'top' + str(i)
            doc[topic] = self.name_to_sim_vec[author][i]
        return doc

    def make_user_profiles_from_csv(self, doc_genres_file):
        # Create a new index
        self.client.indices.delete(index=self.usr_index, ignore_unavailable=True)
        self.client.indices.create(index=self.usr_index)
        # Go through the csv with similarity vectors
        with open(doc_genres_file, 'r') as file:
            reader = csv.reader(file)
            # Want to skip first row with column names
            firstrow = True
            i = 0
            for row in reader:
                if firstrow:
                    firstrow = False
                    continue
                # [1] is doc pid - id for index, [6] is scores list
                pid = row[1]
                # Make string into float list
                sim_vec = ast.literal_eval(row[6])
                # Get authors for the doc
                resp = self.client.get(index=self.doc_index, id=pid)
                for author in resp['_source']['Authors']:
                    self.add_similarity(author, sim_vec)
        
        # Normalize the similarity vectors to sum 1
        self.normalize_sim_vecs()

        # Create the user profiles
        actions = []
        i = 0
        last_auth = ''
        for author in self.name_to_id:
            # NOTE: Crude check that author index name is not too long
            if len(self.name_to_id[author]) > 400:
                print("Author name '{}' is too long".format(author))
                continue
            # Check that the author has a similarity vector
            if author not in self.name_to_sim_vec:
                print("{} has no sim_vec in {}".format(author, doc_genres_file))
                continue
            doc = self.create_doc(author)
            actions.append({ "_index": self.usr_index, "_id": self.name_to_id[author], "_source": doc })
            # Bulk index every thousand docs
            if i % 1000 == 0:
                helpers.bulk(self.client, actions)
                actions = []
        # Index any remaining docs
        if actions:
            helpers.bulk(self.client, actions)