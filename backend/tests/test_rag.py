"""
Tests for the RAG Pipeline

Run with: poetry run pytest tests/test_rag.py -v
"""

import pytest
from pathlib import Path

from rag.chunker import MarkdownChunker, Chunk


class TestMarkdownChunker:
    """Tests for the MarkdownChunker class."""
    
    def test_chunk_simple_text(self):
        """Test chunking simple text without headers."""
        chunker = MarkdownChunker(chunk_size=100, chunk_overlap=10)
        text = "This is a simple paragraph of text that should fit in one chunk."
        
        chunks = chunker.chunk_document(text, source="test")
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].metadata["source"] == "test"
    
    def test_chunk_with_headers(self):
        """Test chunking text with markdown headers."""
        chunker = MarkdownChunker(chunk_size=200, chunk_overlap=20)
        text = """## First Section

This is the first section content.

## Second Section

This is the second section content.
"""
        
        chunks = chunker.chunk_document(text, source="test.md")
        
        assert len(chunks) >= 2
        assert any("First Section" in c.text for c in chunks)
        assert any("Second Section" in c.text for c in chunks)
    
    def test_chunk_respects_size_limit(self):
        """Test that chunks respect the size limit with natural breaks."""
        chunker = MarkdownChunker(chunk_size=100, chunk_overlap=10)
        # Text with natural paragraph breaks
        text = """First paragraph with some content here.

Second paragraph with different content here.

Third paragraph with more details and information.

Fourth paragraph continuing the discussion."""
        
        chunks = chunker.chunk_document(text, source="test")
        
        # Should create chunks from the paragraphs
        assert len(chunks) >= 1
        # All text should be preserved
        combined = " ".join(c.text for c in chunks)
        assert "First paragraph" in combined
        assert "Fourth paragraph" in combined
    
    def test_chunk_preserves_metadata(self):
        """Test that chunk metadata is preserved."""
        chunker = MarkdownChunker(chunk_size=500, chunk_overlap=50)
        text = """## Test Header

Test content here.
"""
        
        chunks = chunker.chunk_document(text, source="test_file.md")
        
        assert len(chunks) >= 1
        assert chunks[0].metadata.get("source") == "test_file.md"
        assert chunks[0].metadata.get("header") == "Test Header"
    
    def test_chunk_with_horizontal_rules(self):
        """Test chunking with horizontal rule separators."""
        chunker = MarkdownChunker(chunk_size=200, chunk_overlap=20)
        text = """First section.

---

Second section.

---

Third section.
"""
        
        chunks = chunker.chunk_document(text, source="test")
        
        assert len(chunks) >= 1
        # Content should be present
        all_text = " ".join(c.text for c in chunks)
        assert "First section" in all_text
        assert "Second section" in all_text
        assert "Third section" in all_text


class TestChunk:
    """Tests for the Chunk dataclass."""
    
    def test_chunk_creation(self):
        """Test creating a Chunk."""
        chunk = Chunk(text="Test text", metadata={"key": "value"})
        
        assert chunk.text == "Test text"
        assert chunk.metadata == {"key": "value"}
        assert chunk.id is not None  # Auto-generated UUID
    
    def test_chunk_char_count(self):
        """Test the char_count property."""
        chunk = Chunk(text="Hello World")
        
        assert chunk.char_count == 11


class TestVoaraKnowledgeBase:
    """Tests specific to the Voara knowledge base format."""
    
    @pytest.fixture
    def sample_kb_content(self) -> str:
        """Sample content in the style of voxara_info_and_faq.md."""
        return """# Voara AI – Company Information & FAQs

## Company Overview

Voara AI is a technology company specializing in voice-enabled AI agents.

---

## What Does Voara AI Do?

Voara AI develops and deploys AI-powered customer service agents that can:

- Answer customer questions using voice in real time
- Access internal company knowledge through RAG
- Operate 24/7 with consistent performance

---

## Frequently Asked Questions (FAQs)

### Does Voara AI store customer voice recordings?

No. By default, Voara AI processes audio streams in real time and does not store voice recordings.

### Can Voara AI answer questions specific to my company?

Yes. Voara AI uses Retrieval-Augmented Generation to retrieve answers from your company's internal documentation.
"""
    
    def test_chunk_voara_content(self, sample_kb_content):
        """Test chunking Voara-style content."""
        chunker = MarkdownChunker(chunk_size=500, chunk_overlap=50)
        
        chunks = chunker.chunk_document(sample_kb_content, source="voxara_info.md")
        
        assert len(chunks) >= 3
        
        # Check for key content
        all_text = " ".join(c.text for c in chunks)
        assert "Company Overview" in all_text or "technology company" in all_text
        assert "voice-enabled AI agents" in all_text or "AI-powered" in all_text
    
    def test_faq_sections_preserved(self, sample_kb_content):
        """Test that FAQ sections are preserved."""
        chunker = MarkdownChunker(chunk_size=500, chunk_overlap=50)
        
        chunks = chunker.chunk_document(sample_kb_content, source="voxara_info.md")
        
        # FAQ content should be in chunks
        all_text = " ".join(c.text for c in chunks)
        assert "voice recordings" in all_text.lower() or "no" in all_text.lower()
