from pydantic import BaseModel


class SearchResult(BaseModel):
    """Represents a single search result."""

    link: str
    title: str
