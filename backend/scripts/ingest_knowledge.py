"""
Knowledge Base Ingestion Script

Loads markdown documents from rag_data/, chunks them, generates embeddings,
and uploads to Qdrant Cloud.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rag.config import get_rag_settings, validate_settings
from rag.chunker import MarkdownChunker, Chunk
from rag.embeddings import embed_batch
from rag.qdrant_service import get_qdrant_service


def find_markdown_files(directory: str) -> list[Path]:
    """Find all markdown files in a directory."""
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    md_files = list(path.glob("**/*.md"))
    return md_files


def load_and_chunk_files(
    files: list[Path],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> list[Chunk]:
    """Load and chunk all markdown files."""
    chunker = MarkdownChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    all_chunks = []
    
    for file_path in files:
        print(f"  Processing: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = chunker.chunk_document(
            text=content,
            source=str(file_path.name)
        )
        
        print(f"    Created {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    return all_chunks


async def ingest_knowledge_base(
    data_directory: str = "rag_data",
    recreate_collection: bool = True
) -> dict:
    """
    Main ingestion function.
    
    Args:
        data_directory: Directory containing markdown files
        recreate_collection: If True, delete and recreate collection
        
    Returns:
        Dict with ingestion statistics
    """
    print("\n" + "=" * 60)
    print("Voara AI Knowledge Base Ingestion")
    print("=" * 60 + "\n")
    
    # Validate settings
    print("1. Validating configuration...")
    try:
        validate_settings()
        print("   ✓ Configuration valid\n")
    except ValueError as e:
        print(f"   ✗ Configuration error: {e}")
        return {"success": False, "error": str(e)}
    
    settings = get_rag_settings()
    
    # Find markdown files
    print("2. Finding markdown files...")
    
    # Handle relative path from backend directory
    script_dir = Path(__file__).parent.parent.parent
    data_path = script_dir / data_directory
    
    if not data_path.exists():
        # Try from current directory
        data_path = Path(data_directory)
    
    try:
        files = find_markdown_files(str(data_path))
        print(f"   Found {len(files)} markdown file(s)")
        for f in files:
            print(f"   - {f.name}")
        print()
    except FileNotFoundError as e:
        print(f"   ✗ Error: {e}")
        return {"success": False, "error": str(e)}
    
    if not files:
        print("   ✗ No markdown files found")
        return {"success": False, "error": "No markdown files found"}
    
    # Load and chunk files
    print("3. Loading and chunking documents...")
    chunks = load_and_chunk_files(
        files,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    print(f"   Total chunks: {len(chunks)}\n")
    
    if not chunks:
        print("   ✗ No chunks created")
        return {"success": False, "error": "No chunks created"}
    
    # Generate embeddings
    print("4. Generating embeddings...")
    print(f"   Using model: {settings.embedding_model}")
    print(f"   Dimension: {settings.embedding_dimension}")
    
    chunk_texts = [chunk.text for chunk in chunks]
    
    try:
        embeddings = await embed_batch(
            texts=chunk_texts,
            task_type="retrieval_document",
            batch_size=5  # Small batch to avoid rate limits
        )
        print(f"   ✓ Generated {len(embeddings)} embeddings\n")
    except Exception as e:
        print(f"   ✗ Embedding error: {e}")
        return {"success": False, "error": str(e)}
    
    # Create/recreate collection
    print("5. Setting up Qdrant collection...")
    qdrant = get_qdrant_service()
    
    try:
        await qdrant.create_collection(recreate=recreate_collection)
        print(f"   ✓ Collection '{settings.qdrant_collection_name}' ready\n")
    except Exception as e:
        print(f"   ✗ Collection error: {e}")
        return {"success": False, "error": str(e)}
    
    # Upsert vectors
    print("6. Uploading vectors to Qdrant...")
    
    ids = [chunk.id for chunk in chunks]
    payloads = [
        {
            "text": chunk.text,
            "source": chunk.metadata.get("source", "unknown"),
            "header": chunk.metadata.get("header", ""),
            "level": chunk.metadata.get("level", 0)
        }
        for chunk in chunks
    ]
    
    try:
        await qdrant.upsert_vectors(
            ids=ids,
            vectors=embeddings,
            payloads=payloads
        )
        print(f"   ✓ Uploaded {len(ids)} vectors\n")
    except Exception as e:
        print(f"   ✗ Upload error: {e}")
        return {"success": False, "error": str(e)}
    
    # Verify
    print("7. Verifying ingestion...")
    try:
        count = await qdrant.count_points()
        info = await qdrant.get_collection_info()
        print(f"   Collection: {info['name']}")
        print(f"   Points: {count}")
        print(f"   Status: {info['status']}\n")
    except Exception as e:
        print(f"   Warning: Could not verify: {e}\n")
    
    # Close connection
    await qdrant.close()
    
    print("=" * 60)
    print("✓ Ingestion completed successfully!")
    print("=" * 60 + "\n")
    
    return {
        "success": True,
        "files_processed": len(files),
        "chunks_created": len(chunks),
        "vectors_uploaded": len(embeddings)
    }


def main():
    """Entry point for the ingestion script."""
    result = asyncio.run(ingest_knowledge_base())
    
    if not result.get("success"):
        print(f"\nError: {result.get('error')}")
        sys.exit(1)
    
    print(f"Summary:")
    print(f"  Files processed: {result.get('files_processed', 0)}")
    print(f"  Chunks created: {result.get('chunks_created', 0)}")
    print(f"  Vectors uploaded: {result.get('vectors_uploaded', 0)}")


if __name__ == "__main__":
    main()
