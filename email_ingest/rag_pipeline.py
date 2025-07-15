from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def chunk_text(text, chunk_size=500):
    # Simple chunking by words
    words = text.split()
    return [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def build_rag_index(attachments, parse_attachment_func):
    """
    attachments: list of dicts with 'filename', 'data', 'doc_type'
    parse_attachment_func: function to extract text from attachment
    Returns: list of dicts with 'chunk', 'embedding', 'doc_type', 'filename'
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    rag_chunks = []
    for att in attachments:
        text = parse_attachment_func(att)
        doc_type = att.get('doc_type', 'Unknown')
        filename = att.get('filename', '')
        for chunk in chunk_text(text):
            embedding = model.encode(chunk)
            rag_chunks.append({'chunk': chunk, 'embedding': embedding, 'doc_type': doc_type, 'filename': filename})
    return rag_chunks

def retrieve_relevant_chunks(rag_chunks, query, top_n=3):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode(query)
    embeddings = np.array([c['embedding'] for c in rag_chunks])
    sims = cosine_similarity([query_embedding], embeddings)[0]
    top_indices = sims.argsort()[-top_n:][::-1]
    return [rag_chunks[i]['chunk'] for i in top_indices]

def prepare_gemini_prompt(relevant_chunks, query):
    context = '\n\n'.join(relevant_chunks)
    prompt = f"Given the following documents:\n{context}\n\n{query}\nPlease answer as structured data."
    return prompt 