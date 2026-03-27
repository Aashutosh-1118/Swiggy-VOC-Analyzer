import streamlit as st
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# 1. Setup & Environment
load_dotenv()

# Professional Swiggy Orange branding
st.set_page_config(page_title="Swiggy VoC Engine", layout="wide")

# Custom CSS to change the header color to Swiggy Orange
st.markdown("""
    <style>
    /* Force the main title size */
    .main-title {
        color: #FC8019 !important; 
        font-size: 65px !important; /* Massive font */
        font-weight: 900 !important;
        line-height: 1.1 !important;
        margin-bottom: 5px !important;
        display: block !important;
    }
    /* Force the subtitle size */
    .sub-title {
        color: #686b78 !important;
        font-size: 26px !important;
        font-weight: 500 !important;
        margin-top: 0px !important;
        margin-bottom: 40px !important;
        display: block !important;
    }
    /* Remove the default extra padding at the top of Streamlit */
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# The HTML markers
st.markdown('<span class="main-title">Swiggy Voice of Customer Engine</span>', unsafe_allow_html=True)
st.markdown('<span class="sub-title">AI-Powered Root Cause Analysis & Product Insights</span>', unsafe_allow_html=True)
st.markdown("---")

@st.cache_resource
def load_components():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    llm = ChatGroq(temperature=0.1, model_name="llama-3.3-70b-versatile")
    return vectorstore, llm

if not os.path.exists("./chroma_db"):
    st.error("Please run build_vector_db.py first!")
    st.stop()

vectorstore, llm = load_components()

query = st.text_input("Analyze a complaint (e.g., 'delivery partner behavior' or 'refund issues'):")

if query:
    with st.spinner("Generating PM analysis..."):
        # Retrieve relevant reviews
        docs = vectorstore.similarity_search(query, k=10)
        context_text = "\n\n".join([f"User {d.metadata['user']}: {d.page_content}" for d in docs])

        # Analysis Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Senior Product Manager at Swiggy. Analyze the following reviews and provide a root cause and a solution."),
            ("human", "Reviews:\n{context}\n\nQuestion: {question}")
        ])

        chain = prompt | llm
        response = chain.invoke({"context": context_text, "question": query})

        # Display Result
        st.markdown("### 📊 AI Analysis")
        # .content ensures we see the text, not the object
        st.info(response.content)

        with st.expander("View Source Reviews"):
            for d in docs:
                st.write(f"**{d.metadata['user']}** ({d.metadata['score']} stars): {d.page_content}")