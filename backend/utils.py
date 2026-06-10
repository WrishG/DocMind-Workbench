#mymupdf
import fitz
def extract_text_from_pdf(file_path : str) -> str:
    #opens pdf extraact text form it
    doc = fitz.open(file_path)
    full_text = ""
    #loop through every page and get text
    for page_num in range(len(doc)):
        page = doc[page_num]
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text
def chunk_text(text : str, chunk_size : int = 500, overlap : int = 50)-> list[str]:
    #split text into chunks 
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start : end]
        chunks.append(chunk)
        #move the start pointer for next chunk with overlap
        start += chunk_size - overlap    
    return chunks