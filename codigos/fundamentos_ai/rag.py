import os
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Mock Python documentation data
python_docs = [
    {
        "title": "List Methods",
        "content": "Python lists have several built-in methods: append() adds an element to the end, extend() adds elements from another iterable, insert() adds an element at a specific position, remove() removes the first occurrence of a value, pop() removes an element at a specific position and returns it, clear() removes all elements, index() returns the index of the first occurrence of a value, count() returns the number of occurrences of a value, sort() sorts the list in place, and reverse() reverses the list in place."
    },
    {
        "title": "Dictionary Methods",
        "content": "Python dictionaries have several useful methods: keys() returns a view of all keys, values() returns a view of all values, items() returns a view of all key-value pairs, get() returns the value for a key or a default value if the key doesn't exist, pop() removes a key and returns its value, update() updates the dictionary with key-value pairs from another dictionary or iterable, and clear() removes all items."
    },
    {
        "title": "String Methods",
        "content": "Python strings have many methods for manipulation: upper() returns the string in uppercase, lower() returns the string in lowercase, strip() removes whitespace from the beginning and end, split() splits the string into a list based on a separator, join() joins elements of an iterable with the string as a separator, replace() replaces occurrences of a substring, and find() returns the index of the first occurrence of a substring."
    },
    {
        "title": "File Operations",
        "content": "Python provides functions for file operations: open() opens a file and returns a file object, read() reads the entire file content, readline() reads a single line, readlines() reads all lines into a list, write() writes a string to the file, writelines() writes a list of strings to the file, and close() closes the file."
    },
    {
        "title": "Exception Handling",
        "content": "Python uses try-except blocks for exception handling. The try block contains code that might raise an exception, and the except block contains code that handles the exception. You can catch specific exceptions or use a general except clause. The finally block contains code that always executes, regardless of whether an exception occurred."
    }
]

class RAGSystem:
    def __init__(self, documents: List[Dict[str, str]]):
        """Initialize the RAG system with documents."""
        self.documents = documents
        self.embeddings = {}
        self.generate_embeddings()
    
    def generate_embeddings(self):
        """Generate embeddings for all documents."""
        print("Generating embeddings for documents...")
        for i, doc in enumerate(self.documents):
            # Combine title and content for embedding
            text = f"{doc['title']}: {doc['content']}"
            
            # Get embedding from OpenAI
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            
            # Store the embedding
            self.embeddings[i] = response.data[0].embedding
            
        print(f"Generated embeddings for {len(self.documents)} documents")
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query."""
        response = client.embeddings.create(
            input=query,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    
    def calculate_similarity(self, query_embedding: List[float], doc_embedding: List[float]) -> float:
        """Calculate cosine similarity between query and document embeddings."""
        dot_product = np.dot(query_embedding, doc_embedding)
        query_norm = np.linalg.norm(query_embedding)
        doc_norm = np.linalg.norm(doc_embedding)
        return dot_product / (query_norm * doc_norm)
    
    def retrieve_relevant_docs(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieve the most relevant documents for a query."""
        query_embedding = self.get_query_embedding(query)
        
        # Calculate similarity scores
        similarities = []
        for doc_id, doc_embedding in self.embeddings.items():
            similarity = self.calculate_similarity(query_embedding, doc_embedding)
            similarities.append((doc_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k documents with their similarity scores
        result = []
        for doc_id, similarity in similarities[:top_k]:
            result.append({
                "document": self.documents[doc_id],
                "similarity": similarity
            })
        
        return result
    
    def answer_query(self, query: str) -> str:
        """Answer a query using RAG."""
        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_docs(query)
        
        # Construct prompt with retrieved context
        context = ""
        for i, doc in enumerate(relevant_docs):
            context += f"Document {i+1} ({doc['document']['title']}): {doc['document']['content']}\n\n"
        
        prompt = f"""You are a helpful assistant that answers questions about Python programming.
Use the following retrieved documents to answer the user's question.
If you don't know the answer based on these documents, say so.

{context}

User question: {query}

Answer:"""
        
        # Generate answer using OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Python documentation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content

# Demo function
def rag_demo():
    # Initialize RAG system with mock Python documentation
    rag = RAGSystem(python_docs)
    
    # Example queries
    queries = [
        "How do I add elements to a list in Python?",
        "What's the difference between append and extend in Python lists?",
        "How can I handle exceptions in Python?",
        "How do I read a file line by line in Python?"
    ]
    
    # Process each query
    for i, query in enumerate(queries):
        print(f"\n{'='*50}")
        print(f"QUERY {i+1}: {query}")
        print(f"{'='*50}")
        
        # Get relevant documents
        relevant_docs = rag.retrieve_relevant_docs(query)
        
        print("\nRETRIEVED DOCUMENTS:")
        for j, doc in enumerate(relevant_docs):
            print(f"\nDocument {j+1}: {doc['document']['title']}")
            print(f"Similarity Score: {doc['similarity']:.4f}")
            print(f"Content Preview: {doc['document']['content'][:100]}...")
        
        # Get answer
        answer = rag.answer_query(query)
        
        print("\nGENERATED ANSWER:")
        print(answer)

if __name__ == "__main__":
    rag_demo()
