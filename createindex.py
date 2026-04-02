from DB.db_connect import doc_collection
from pymongo.operations import SearchIndexModel

INDEX_NAME = "rag_data_index"

index_definition = {
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
        },
        {
            "type": "filter",
            "path": "user_id"
        }
    ]
}

existing_index_names = [idx.get("name") for idx in doc_collection.list_search_indexes()]

if INDEX_NAME in existing_index_names:
    doc_collection.update_search_index(name=INDEX_NAME, definition=index_definition)
    print("Search index updated successfully.")
else:
    index = SearchIndexModel(
        definition=index_definition,
        name=INDEX_NAME,
        type="vectorSearch"
    )
    doc_collection.create_search_index(model=index)
    print("Search index created successfully.")