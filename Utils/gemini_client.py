import os

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

DEFAULT_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash-lite")
DEFAULT_MEMORY_MODEL = os.getenv("GEMINI_MEMORY_MODEL", "gemini-2.5-flash-lite")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "models/gemini-embedding-001",
)
DEFAULT_EMBEDDING_DIMENSIONS = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768"))


def get_google_api_key() -> str:
    gemini_key = os.getenv("GEMINI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    google_genai_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")

    # Avoid SDK noise when both GEMINI_API_KEY and GOOGLE_API_KEY are set.
    # Keep a single key in process env so provider clients don't print warnings.
    if gemini_key and google_key:
        os.environ.pop("GEMINI_API_KEY", None)

    api_key = gemini_key or google_key or google_genai_key
    if not api_key:
        raise ValueError(
            "Missing Gemini API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment."
        )
    return api_key


def build_chat_model(
    *,
    model: str,
    temperature: float = 0,
    max_output_tokens: int | None = None,
):
    kwargs = {
        "model": model,
        "google_api_key": get_google_api_key(),
        "temperature": temperature,
    }
    if max_output_tokens is not None:
        kwargs["max_output_tokens"] = max_output_tokens
    return ChatGoogleGenerativeAI(**kwargs)


class GeminiEmbeddings(Embeddings):
    def __init__(
        self,
        *,
        model: str = DEFAULT_EMBEDDING_MODEL,
        output_dimensionality: int = DEFAULT_EMBEDDING_DIMENSIONS,
    ):
        self.model = GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=get_google_api_key(),
        )
        self.output_dimensionality = output_dimensionality

    def embed_documents(self, texts, **kwargs):
        return self.model.embed_documents(
            texts,
            task_type="retrieval_document",
            output_dimensionality=kwargs.get(
                "output_dimensionality", self.output_dimensionality
            ),
        )

    def embed_query(self, text, **kwargs):
        return self.model.embed_query(
            text,
            task_type="retrieval_query",
            output_dimensionality=kwargs.get(
                "output_dimensionality", self.output_dimensionality
            ),
        )

    async def aembed_documents(self, texts, **kwargs):
        return await self.model.aembed_documents(
            texts,
            task_type="retrieval_document",
            output_dimensionality=kwargs.get(
                "output_dimensionality", self.output_dimensionality
            ),
        )

    async def aembed_query(self, text, **kwargs):
        return await self.model.aembed_query(
            text,
            task_type="retrieval_query",
            output_dimensionality=kwargs.get(
                "output_dimensionality", self.output_dimensionality
            ),
        )
