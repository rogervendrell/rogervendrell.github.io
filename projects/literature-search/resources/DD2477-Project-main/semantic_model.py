from sentence_transformers import SentenceTransformer

modelName = 'all-mpnet-base-v2'

class SemanticModel:

    def __init__(self):
        self.model = SentenceTransformer(modelName)
        ...

    def apply_model(self, text:str): 
        return self.model.encode(sentences=text)
        ...

    def get_embedding_size(self):
        return self.model.get_sentence_embedding_dimension()
