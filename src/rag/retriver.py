from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import numpy as np
from collections import defaultdict
import re

# Initialize embedder and Pinecone client
embedder = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key="use_your_key")
index = pc.Index("medical-conditions")

def normalize_symptoms(symptom_list):
    """Normalize a list of symptoms by removing noise and handling common variations."""
    normalized = []
    for sym in symptom_list:
        sym = sym.lower().strip()
        # Remove extra phrases and normalize
        sym = re.sub(r'\s+(all over my body|recently)\b', '', sym)
        sym = re.sub(r'\s+', ' ', sym)  # Normalize whitespace
        sym = sym.strip()
        if sym:
            normalized.append(sym)
    return normalized

def retrieve(symptoms, top_k=10):
    """
    Retrieve the top-k most similar medical conditions from Pinecone based on symptoms across all namespaces,
    consolidating duplicate conditions and preserving metadata from all sources.
    
    Args:
        symptoms (str): User input (e.g., "itching,fatigue,yellowish skin" or "I have itching,fatigue and yellowish skin")
        top_k (int): Number of results to return (default: 10)
    
    Returns:
        list: List of dictionaries containing consolidated metadata of unique conditions
    """
    try:
        # Preprocess input to extract symptoms
        symptoms = symptoms.lower().strip()
        # Remove common leading phrases
        symptoms = re.sub(r'^(i have|i am|having|with)\s*', '', symptoms)
        # Replace " and " or " with " with comma for consistent splitting
        symptoms = symptoms.replace(' and ', ',').replace(' with ', ',')
        # Split into symptoms list and normalize
        symptoms_list = [s.strip() for s in symptoms.split(",") if s.strip()]
        symptoms_list = normalize_symptoms(symptoms_list)
        symptoms_text = ", ".join(symptoms_list)
        
        print(f"Processed symptoms: {symptoms_list}")  # Debug print
        
        # Embed the symptoms query
        query_embedding = embedder.encode(symptoms_text, convert_to_numpy=True).tolist()
        
        # Define the namespaces
        namespaces = ["csv2","csv1","nhs"]
        
        # Query Pinecone across all specified namespaces
        all_results = []
        for namespace in namespaces:
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            # Extract full metadata from results with a moderate threshold
            namespace_results = [{
                **match.metadata,
                "namespace": namespace,
                "score": match.score
            } for match in results.matches if match.score > 0.3]  # Increased threshold to 0.3
            all_results.extend(namespace_results)
        
        # Debug - Check raw data coming in
        print(f"Total retrieved items: {len(all_results)}")
        for item in all_results[:3]:  # Show first 3 items for debugging
            condition = item.get("condition", "N/A")
            print(f"Raw data for {condition} from {item['namespace']}:")
            print(f"  Causes: {item.get('causes', 'None')}")
            print(f"  Preventions: {item.get('preventions', 'None')}")
        
        # Initialize consolidated results with proper default values
        consolidated_results = defaultdict(lambda: {
            "scores": [], 
            "sources": set(),
            "causes": "Not available",
            "preventions": "Not available",
            "symptoms": set(),
            "summary": "Not available",
            "url": "Not available"
        })
        
        # Consolidate results by condition
        for item in all_results:
            condition = item.get("condition", "N/A")
            data = consolidated_results[condition]
            
            # Aggregate all metadata fields
            for key in ["symptoms", "summary", "preventions", "causes", "url"]:
                current_value = item.get(key, "Not available")
                
                # Only process if we have actual data
                if current_value != "Not available" and current_value:
                    if key == "symptoms":
                        # Normalize and deduplicate symptoms
                        if isinstance(current_value, str):
                            current_value = [s.strip() for s in current_value.split(",") if s.strip()]
                        normalized = set()
                        for sym in current_value:
                            sym = sym.lower().replace("_", " ").strip()
                            sym = re.sub(r'\s+(all over my body|recently)\b', '', sym)
                            if sym:
                                normalized.add(sym)
                        data["symptoms"].update(normalized)
                    
                    elif key in ["preventions", "causes"]:
                        # Get existing value properly
                        existing_data = data.get(key, "Not available")
                        if existing_data != "Not available":
                            existing_items = [e.strip() for e in existing_data.split(",") if e.strip()]
                        else:
                            existing_items = []
                        
                        # Process new values
                        new_items = [v.strip() for v in current_value.split(",") if v.strip()]
                        
                        # Combine and deduplicate
                        all_items = list(dict.fromkeys(existing_items + new_items))
                        if all_items:
                            data[key] = ", ".join(all_items)
                    
                    else:  # summary, url
                        # Use the longest non-empty value
                        existing = data.get(key, "Not available")
                        if existing == "Not available" or (len(current_value) > len(existing)):
                            data[key] = current_value
            
            data["condition"] = condition
            data["sources"].add(item["namespace"])
            data["scores"].append(item["score"])
        
        # Convert to list and sort by average score
        unique_results = [
            {
                "condition": data["condition"],
                "symptoms": sorted(list(data.get("symptoms", []))),
                "summary": data.get("summary", "Not available"),
                "preventions": data.get("preventions", "Not available"),
                "causes": data.get("causes", "Not available"),
                "url": data.get("url", "Not available"),
                "sources": ", ".join(data["sources"]),
                "average_score": sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
            }
            for data in consolidated_results.values()
        ]
        unique_results.sort(key=lambda x: x["average_score"], reverse=True)
        unique_results = unique_results[:top_k]

        print(f"Retrieved {len(unique_results)} unique conditions for symptoms: {symptoms_text}")
        if unique_results:
            for item in unique_results:
                print(f"\nCondition: {item['condition']}, Average Score: {item['average_score']:.3f}, Sources: {item['sources']}")
                print(f"  Causes: {item.get('causes', 'Not available')}")
                print(f"  Preventions: {item.get('preventions', 'Not available')}")
        else:
            print("No matching conditions found.")
        
        return unique_results
    
    except Exception as e:
        print(f"Error retrieving data: {e}")
        import traceback
        traceback.print_exc()
        return []

# Example usage for testing
if __name__ == "__main__":
    test_symptoms = "I have itching,fatigue and yellowish skin"
    retrieved_conditions = retrieve(test_symptoms)
