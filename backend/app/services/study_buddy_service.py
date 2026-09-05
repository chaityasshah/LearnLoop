import os
import glob
from pathlib import Path
from typing import List, Optional, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

class StudyBuddyService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.retriever = None
        self.vectorstore = None

        if self.api_key:
            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=self.api_key,
                temperature=0.7
            )
        else:
            self.llm = None
            
    def initialize_vectorstore(self, data_dir: str):
        if not os.path.exists(data_dir):
            return
            
        all_documents = []
        for file_path in glob.glob(os.path.join(data_dir, "**/*.*"), recursive=True):
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                all_documents.extend(loader.load())
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
                all_documents.extend(loader.load())
                
        if not all_documents:
            return
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=200,
            length_function=len
        )
        splits = text_splitter.split_documents(all_documents)
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.vectorstore = FAISS.from_documents(splits, embeddings)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})

    def format_chat_history(self, chat_history: List[Any]) -> str:
        formatted = []
        for msg in chat_history:
            if msg["role"] == "user":
                formatted.append(f"Human: {msg['content']}")
            elif msg["role"] == "assistant":
                formatted.append(f"Assistant: {msg['content']}")
        return "\n".join(formatted)

    def format_docs(self, docs) -> str:
        return "\n\n".join(doc.page_content for doc in docs)

    def generate_response(self, question: str, topic: str, difficulty: str, history: List[Any]) -> dict:
        if not self.llm:
            return {
                "answer": "Study Buddy is currently unavailable (API key missing).",
                "sources": []
            }

        # Adapt the prompt to include the LearnLoop topic and difficulty context
        template = """You are a helpful AI assistant for IIIT Sri City students. 
The student is currently working on the topic: {topic} at a {difficulty} level.
Answer the question using the context from documents if relevant, otherwise use your general knowledge.
Be friendly, professional, and detailed.

Context from documents:
{context}

Chat History:
{chat_history}

Current Question: {question}

Answer:"""

        prompt_template = ChatPromptTemplate.from_template(template)
        
        context = ""
        sources = []
        if self.retriever:
            retrieved_docs = self.retriever.invoke(question)
            context = self.format_docs(retrieved_docs)
            for doc in retrieved_docs:
                if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                    sources.append(Path(doc.metadata['source']).name)
        
        chat_history_text = self.format_chat_history(history[-6:])
        
        rag_chain = (
            {
                "context": lambda x: context,
                "chat_history": lambda x: chat_history_text,
                "topic": lambda x: topic,
                "difficulty": lambda x: difficulty,
                "question": RunnablePassthrough()
            }
            | prompt_template
            | self.llm
            | StrOutputParser()
        )
        
        answer = rag_chain.invoke(question)
        
        return {
            "answer": answer,
            "sources": list(set(sources))
        }

# Singleton instance
study_buddy_service = StudyBuddyService()
study_buddy_service.initialize_vectorstore(os.path.join(os.path.dirname(__file__), "..", "..", "data", "study_materials"))
