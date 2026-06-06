import streamlit as st
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from openai import OpenAI

api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password"
)
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="AI Document Intelligence Assistant")

st.title("📄 AI Document Intelligence Assistant")

st.write(
    "Upload documents and ask intelligent questions using Retrieval-Augmented Generation (RAG)."
)

# ----------------------------
# PDF Text Extraction
# ----------------------------
def extract_pdf_text(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


# ----------------------------
# Chunking
# ----------------------------
def create_chunks(text, chunk_size=50):
    chunks = []
    words = text.split()

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


# ----------------------------
# File Upload
# ----------------------------
uploaded_file = st.file_uploader(
    "Upload a PDF Document",
    type=["pdf"]
)

if uploaded_file:
    st.success("Document uploaded successfully!")

    text = extract_pdf_text(uploaded_file)

    st.subheader("Extracted Text")
    st.text_area(
        "Document Content",
        text[:5000],
        height=300
    )

    chunks = create_chunks(text)

    st.subheader("Document Chunks")
    st.write(f"Total Chunks Created: {len(chunks)}")

    if chunks:
        with st.expander("Preview First Chunk"):
            st.write(chunks[0])

        with st.spinner("Generating embeddings..."):
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(chunks)

        st.subheader("Embeddings Generated")
        st.success(f"Generated {len(embeddings)} embeddings successfully!")
        
        st.subheader("Vector Database Storage")

        client = chromadb.Client()

        collection = client.get_or_create_collection(
            name="document_chunks"
        )

        ids = [f"chunk_{i}" for i in range(len(chunks))]

        collection.add(
            documents=chunks,
            embeddings=embeddings.tolist(),
            ids=ids
        )

        st.success(f"Stored {len(chunks)} chunks in ChromaDB vector database!")
        # ----------------------------------
        # Question Answering
        # ----------------------------------

        st.subheader("Ask Questions About Your Document")

        user_question = st.text_input("Enter your question:")

        if user_question:

            query_embedding = model.encode(
                [user_question]
            )

            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=1
            )

            retrieved_chunk = results["documents"][0][0]

            st.subheader("Most Relevant Chunk")

            st.info(retrieved_chunk)
            st.subheader("AI-Generated Answer")

            if api_key:

                client = OpenAI(api_key=api_key)

                prompt = f"""
                Use the following document information to answer the user's question.

                Context:
                {retrieved_chunk}

                Question:
                {user_question}

                Give a concise professional answer.
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                answer = response.choices[0].message.content

                st.success(answer)

            else:
                st.warning("Enter OpenAI API Key in sidebar.")