from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import numpy as np

# Initialize embedder and Pinecone client
embedder = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key="pcsk_6L2y2o_AYPKUWFRfDk1z4jkAjvwAbLPrEHy4j3is9ktFLtwqQGkK2NdL2fkZsdZMwtowKZ")
index = pc.Index("medical-conditions")

def retrieve(symptoms, top_k=5):
    """
    Retrieve the top-k most similar medical conditions from Pinecone based on symptoms.
    
    Args:
        symptoms (str): Comma-separated list of symptoms (e.g., "itching,fatigue,yellowish skin")
        top_k (int): Number of results to return (default: 5)
    
    Returns:
        list: List of dictionaries containing metadata of matching conditions
    """
    try:
        # Embed the symptoms query
        query_embedding = embedder.encode(symptoms, convert_to_numpy=True).tolist()
        
        # Query Pinecone
        results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
        
        # Extract metadata from results
        retrieved_data = [match.metadata for match in results.matches]
        
        print(f"Retrieved {len(retrieved_data)} conditions for symptoms: {symptoms}")
        for item in retrieved_data:
            print(f"Condition: {item['condition']}, Text: {item['text'][:100]}...")
        
        return retrieved_data
    
    except Exception as e:
        print(f"Error retrieving data: {e}")
        return []

# Example usage for testing
if __name__ == "__main__":
   
    test_symptoms = "itching,fatigue,yellowish skin"
    retrieved_conditions = retrieve(test_symptoms)