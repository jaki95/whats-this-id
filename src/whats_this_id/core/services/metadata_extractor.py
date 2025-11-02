"""LLM-based metadata extraction service for DJ set tracklists."""

import logging
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()


class ExtractedMetadata(BaseModel):
    """Pydantic model for structured LLM output."""

    artist: str = Field(description="The artist or DJ name extracted from the title")
    year: int | None = Field(
        description="The year extracted from the title, or None if not found"
    )


class MetadataExtractor:
    """Service for extracting metadata from DJ set titles using LLM."""

    def __init__(self, model_name: str = "gpt-4.1-mini") -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key,
        ).with_structured_output(ExtractedMetadata)

    def extract(self, tracklist_title: str) -> ExtractedMetadata:
        """Extract artist name and year from a DJ set title.
        """
        prompt = f"""Extract the artist name and year from this DJ set title:

"{tracklist_title}"

Extract only the artist/DJ name and year. If the year is not clearly present or ambiguous, return None for the year field.
The artist name should be the DJ, not venue or event names.
A set can be by two or more artists, usually separated by an ampersand (&) or "B2B", "F2F".
In that case, return all the artists separated by ampersands (&).

Examples:
- "SHDW @ Boiler Room Berlin 2023" -> artist="SHDW", year=2023
- "SHDW & Alarico @ Boiler Room Berlin 2023" -> artist="SHDW & Alarico", year=2023
- "SHDW b2b Alarico @ Boiler Room Berlin 2023" -> artist="SHDW & Alarico", year=2023
- "SHDW F2F Alarico @ Boiler Room Berlin 2023" -> artist="SHDW & Alarico", year=2023
"""

        try:
            logger.info(f"Extracting metadata from title: {tracklist_title}")
            result = self.llm.invoke(prompt)
            logger.info(
                f"Extracted metadata: artist={result.artist}, year={result.year}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            raise


def extract_metadata(tracklist_title: str) -> ExtractedMetadata:
    """Extract metadata from a DJ set title.
    """
    extractor = MetadataExtractor()
    return extractor.extract(tracklist_title)
