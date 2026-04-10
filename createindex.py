from DB.db_connect import doc_collection
from pymongo.operations import SearchIndexModel
from Utils.gemini_client import DEFAULT_EMBEDDING_DIMENSIONS

INDEX_NAME = "rag_data_index"

index_definition = {
    "fields": [
        {
            "type": "vector",
            "path": "embedding",
            "numDimensions": DEFAULT_EMBEDDING_DIMENSIONS,
            "similarity": "cosine"
        },
        {
            "type": "filter",
            "path": "doc_id"
        },
        {
            "type": "filter",
            "path": "case_id"
        },
        {
            "type": "filter",
            "path": "user_id"
        }
    ]
}

index = SearchIndexModel(
    definition=index_definition,
    name=INDEX_NAME,
    type="vectorSearch"
)
result = doc_collection.create_search_index(model=index)
print("Search index created successfully.", result)
