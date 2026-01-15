"""
Document Chunker Module

Provides text chunking functionality optimized for markdown FAQ-style documents.
Uses recursive splitting on section headers for semantic coherence.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class Chunk:
    """Represents a document chunk with metadata."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    metadata: dict = field(default_factory=dict)
    
    @property
    def char_count(self) -> int:
        """Return the character count of the chunk text."""
        return len(self.text)


class MarkdownChunker:
    """
    Markdown-aware document chunker.
    
    Splits documents on markdown headers while respecting chunk size limits.
    Preserves section context by including parent headers in chunks.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters  
            min_chunk_size: Minimum chunk size (smaller chunks are merged)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Markdown header patterns (## and ###)
        self.section_pattern = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)
        self.separator_pattern = re.compile(r'^---+$', re.MULTILINE)
    
    def chunk_document(
        self,
        text: str,
        source: Optional[str] = None
    ) -> list[Chunk]:
        """
        Split a markdown document into chunks.
        
        Args:
            text: The document text to chunk
            source: Optional source identifier for metadata
            
        Returns:
            List of Chunk objects
        """
        # First, split by horizontal rules and major sections
        sections = self._split_by_sections(text)
        
        chunks = []
        for section in sections:
            section_chunks = self._chunk_section(section, source)
            chunks.extend(section_chunks)
        
        # Merge small chunks
        chunks = self._merge_small_chunks(chunks)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> list[dict]:
        """
        Split document into sections based on headers.
        
        Returns:
            List of dicts with 'header' and 'content' keys
        """
        # Split by horizontal rules first
        parts = self.separator_pattern.split(text)
        
        sections = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Find all headers in this part
            headers = list(self.section_pattern.finditer(part))
            
            if not headers:
                # No headers, treat as single section
                sections.append({
                    'header': '',
                    'content': part,
                    'level': 0
                })
            else:
                # Split by headers
                for i, match in enumerate(headers):
                    header_level = len(match.group(1))
                    header_text = match.group(2).strip()
                    
                    # Get content until next header or end
                    start = match.end()
                    if i + 1 < len(headers):
                        end = headers[i + 1].start()
                    else:
                        end = len(part)
                    
                    content = part[start:end].strip()
                    
                    if content or header_text:
                        sections.append({
                            'header': header_text,
                            'content': content,
                            'level': header_level
                        })
        
        return sections
    
    def _chunk_section(
        self,
        section: dict,
        source: Optional[str] = None
    ) -> list[Chunk]:
        """
        Chunk a single section, respecting size limits.
        """
        header = section.get('header', '')
        content = section.get('content', '')
        level = section.get('level', 0)
        
        # Combine header and content
        if header:
            full_text = f"## {header}\n\n{content}" if level <= 2 else f"### {header}\n\n{content}"
        else:
            full_text = content
        
        full_text = full_text.strip()
        
        if not full_text:
            return []
        
        # If small enough, return as single chunk
        if len(full_text) <= self.chunk_size:
            return [Chunk(
                text=full_text,
                metadata={
                    'source': source or 'unknown',
                    'header': header,
                    'level': level
                }
            )]
        
        # Split into smaller chunks
        return self._split_large_section(full_text, header, level, source)
    
    def _split_large_section(
        self,
        text: str,
        header: str,
        level: int,
        source: Optional[str]
    ) -> list[Chunk]:
        """
        Split a large section into smaller chunks with overlap.
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds limit
            if len(current_chunk) + len(para) + 2 > self.chunk_size:
                if current_chunk:
                    chunks.append(Chunk(
                        text=current_chunk.strip(),
                        metadata={
                            'source': source or 'unknown',
                            'header': header,
                            'level': level
                        }
                    ))
                    
                    # Keep overlap from end of current chunk
                    if self.chunk_overlap > 0 and len(current_chunk) > self.chunk_overlap:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    # Paragraph itself is too long, split by sentences
                    sentence_chunks = self._split_by_sentences(para, header, level, source)
                    chunks.extend(sentence_chunks)
                    current_chunk = ""
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append(Chunk(
                text=current_chunk.strip(),
                metadata={
                    'source': source or 'unknown',
                    'header': header,
                    'level': level
                }
            ))
        
        return chunks
    
    def _split_by_sentences(
        self,
        text: str,
        header: str,
        level: int,
        source: Optional[str]
    ) -> list[Chunk]:
        """
        Split text by sentences when paragraphs are too long.
        """
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                if current_chunk:
                    chunks.append(Chunk(
                        text=current_chunk.strip(),
                        metadata={
                            'source': source or 'unknown',
                            'header': header,
                            'level': level
                        }
                    ))
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk.strip():
            chunks.append(Chunk(
                text=current_chunk.strip(),
                metadata={
                    'source': source or 'unknown',
                    'header': header,
                    'level': level
                }
            ))
        
        return chunks
    
    def _merge_small_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Merge chunks that are too small.
        """
        if not chunks:
            return []
        
        merged = []
        current = chunks[0]
        
        for chunk in chunks[1:]:
            # If current chunk is small, try to merge with next
            if current.char_count < self.min_chunk_size:
                combined_text = current.text + "\n\n" + chunk.text
                if len(combined_text) <= self.chunk_size:
                    current = Chunk(
                        text=combined_text,
                        metadata=current.metadata
                    )
                    continue
            
            merged.append(current)
            current = chunk
        
        merged.append(current)
        return merged


def chunk_markdown_file(
    file_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> list[Chunk]:
    """
    Convenience function to chunk a markdown file.
    
    Args:
        file_path: Path to the markdown file
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of Chunk objects
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    chunker = MarkdownChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return chunker.chunk_document(text, source=file_path)
