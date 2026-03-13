import aiofiles
from fastapi import File, UploadFile
from DB.db_connect import doc_collection
from dotenv import load_dotenv
import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
embedding = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))


# insert doc
async def upload_file(file: UploadFile, doc_id: str):
    print("inserting data")

    filepath = f"uploads/{file.filename}"
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)


    # insert into db
    loader = PyPDFLoader(filepath)
    docs = loader.load()

    # for doc in docs:
    #     doc.metadata["doc_id"] = doc_id


    text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

    chunks = text_splitter.split_documents(docs)

    for doc in chunks:
        doc.metadata["doc_id"] = doc_id

    MongoDBAtlasVectorSearch.from_documents(
        documents= chunks,
        embedding= embedding,
        collection = doc_collection,
        inde_name = "rag_data_index"
    )
    print("data injested successfully")
    return {"message": f"file {file.filename} uploaded and processed successfully"}