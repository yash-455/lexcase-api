from DB.db_connect import doc_collection
from pymongo.operations import SearchIndexModel

index = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine"
            },
            {
                "type": "filter",
                "path": "doc_id"
            },
            {
                "type": "filter",
                "path": "case_id"
            }
        ]
    },
    name = "rag_data_index",
    type = "vectorSearch"
)

doc_collection.create_search_index(model=index)
print("Search index created successfully.")