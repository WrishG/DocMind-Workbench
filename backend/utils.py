#mymupdf
import fitz
import fitz

def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extracts text page by page, preserving the page number."""
    doc = fitz.open(file_path)
    pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Store a dictionary with the page number (1-indexed for humans) and text
        pages.append({
            "page": page_num + 1,
            "text": page.get_text()
        })
        
    doc.close()
    return pages

def chunk_text(pages: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """Splits text into chunks, keeping the page number attached."""
    chunks = []
    
    for page_data in pages:
        text = page_data["text"]
        page_num = page_data["page"]
        
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk_str = text[start:end]
            
            # We save the chunk as a dictionary so it carries its page number
            chunks.append({
                "text": chunk_str,
                "page": page_num
            })
            
            start += (chunk_size - overlap)
            
    return chunks
