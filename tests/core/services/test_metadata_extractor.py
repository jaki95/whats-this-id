"""Tests for the metadata extractor service."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from whats_this_id.core.services.metadata_extractor import (
    ExtractedMetadata,
    MetadataExtractor,
    extract_metadata,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestExtractedMetadata:
    """Test cases for the ExtractedMetadata Pydantic model."""

    def test_valid_metadata_with_year(self) -> None:
        """Test creating ExtractedMetadata with valid artist and year.

        Validates that a metadata object with both artist and year can be created.
        """
        metadata = ExtractedMetadata(artist="Nina Kraviz", year=2023)
        assert metadata.artist == "Nina Kraviz"
        assert metadata.year == 2023

    def test_valid_metadata_without_year(self) -> None:
        """Test creating ExtractedMetadata with artist only.

        Validates that year can be None.
        """
        metadata = ExtractedMetadata(artist="Charlotte de Witte", year=None)
        assert metadata.artist == "Charlotte de Witte"
        assert metadata.year is None

    def test_invalid_metadata_missing_artist(self) -> None:
        """Test creating ExtractedMetadata without required artist field.

        Validates that artist is a required field.
        """
        with pytest.raises(ValidationError):
            ExtractedMetadata(year=2023)


class TestMetadataExtractor:
    """Test cases for the MetadataExtractor service."""

    def test_init_with_missing_api_key(self, monkeypatch: MonkeyPatch) -> None:
        """Test initializing extractor without OPENAI_API_KEY.

        Validates that a ValueError is raised when the API key is missing.
        """
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            MetadataExtractor()

    def test_init_with_valid_api_key(self, monkeypatch: MonkeyPatch) -> None:
        """Test initializing extractor with valid API key.

        Validates that the extractor initializes successfully with an API key.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        extractor = MetadataExtractor()
        assert extractor.llm is not None

    def test_extract_calls_llm_correctly(
        self, monkeypatch: MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test that extract method calls the LLM with correct arguments.

        Validates the LLM is invoked with the structured output setup.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

        # Mock the LLM invocation
        mock_llm = mocker.MagicMock()
        mock_llm.invoke.return_value = ExtractedMetadata(
            artist="Test Artist", year=2024
        )

        extractor = MetadataExtractor()
        extractor.llm = mock_llm

        result = extractor.extract("Test DJ Set Title 2024")

        assert result.artist == "Test Artist"
        assert result.year == 2024
        mock_llm.invoke.assert_called_once()

    def test_extract_handles_llm_error(
        self, monkeypatch: MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test that extract handles LLM errors gracefully.

        Validates that exceptions from the LLM are properly raised.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

        # Mock the LLM to raise an exception
        mock_llm = mocker.MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM error")

        extractor = MetadataExtractor()
        extractor.llm = mock_llm

        with pytest.raises(Exception, match="LLM error"):
            extractor.extract("Test Title")

    def test_extract_logs_information(
        self,
        monkeypatch: MonkeyPatch,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that extract logs information about the extraction.

        Validates proper logging of extraction attempts.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

        # Mock the LLM invocation
        mock_llm = mocker.MagicMock()
        mock_llm.invoke.return_value = ExtractedMetadata(
            artist="Logged Artist", year=2025
        )

        extractor = MetadataExtractor()
        extractor.llm = mock_llm

        with caplog.at_level("INFO"):
            extractor.extract("Test Log Title")

        log_output = caplog.text
        assert "Extracting metadata from title: Test Log Title" in log_output
        assert "Extracted metadata: artist=Logged Artist, year=2025" in log_output


class TestExtractMetadataFunction:
    """Test cases for the extract_metadata convenience function."""

    def test_extract_metadata_missing_api_key(self, monkeypatch: MonkeyPatch) -> None:
        """Test extract_metadata without OPENAI_API_KEY.

        Validates that a ValueError is raised when the API key is missing.
        """
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            extract_metadata("Test Title")

    def test_extract_metadata_with_valid_key(
        self, monkeypatch: MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test extract_metadata with valid configuration.

        Validates that the convenience function works correctly.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

        # Mock the LLM invocation
        mock_llm = mocker.MagicMock()
        mock_llm.invoke.return_value = ExtractedMetadata(
            artist="Function Artist", year=2023
        )

        # Patch the MetadataExtractor to use our mock
        with mocker.patch.object(MetadataExtractor, "__init__", return_value=None):
            extractor = MetadataExtractor()
            extractor.llm = mock_llm

            # Patch the function to use our mock extractor
            with mocker.patch(
                "whats_this_id.core.services.metadata_extractor.MetadataExtractor",
                return_value=extractor,
            ):
                result = extract_metadata("Function Test Title")
                assert result.artist == "Function Artist"
                assert result.year == 2023
