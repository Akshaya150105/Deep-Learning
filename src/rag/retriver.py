from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import numpy as np
from collections import defaultdict

# Initialize embedder and Pinecone client
embedder = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key="pcsk_6L2y2o_AYPKUWFRfDk1z4jkAjvwAbLPrEHy4j3is9ktFLtwqQGkK2NdL2fkZsdZMwtowKZ")
index = pc.Index("medical-conditions")

def retrieve(symptoms, top_k=5):
    """
    Retrieve the top-k most similar medical conditions from Pinecone based on symptoms across all namespaces,
    consolidating duplicate conditions and preserving both summary and overview.
    
    Args:
        symptoms (str): Comma-separated list of symptoms (e.g., "itching,fatigue,yellowish skin")
        top_k (int): Number of results to return (default: 5)
    
    Returns:
        list: List of dictionaries containing consolidated metadata of unique conditions
    """
    try:
        # Normalize input symptoms to match the joined format in upsert
        symptoms_list = [s.strip() for s in symptoms.split(",")]
        symptoms_text = ", ".join(symptoms_list)  # e.g., "itching, fatigue, yellowish skin"
        
        # Embed the symptoms query
        query_embedding = embedder.encode(symptoms_text, convert_to_numpy=True).tolist()
        
        # Define the three namespaces
        namespaces = ["csv1", "csv2", "nhs"]
        
        # Query Pinecone across all specified namespaces
        all_results = []
        for namespace in namespaces:
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            # Extract full metadata from results with a lower threshold
            namespace_results = [{
                **match.metadata,
                "namespace": namespace,
                "score": match.score
            } for match in results.matches if match.score > 0.2]
            all_results.extend(namespace_results)
        
        # Consolidate results by condition
        consolidated_results = defaultdict(lambda: {"scores": [], "sources": set(), "overviews": []})
        for item in all_results:
            condition = item.get("condition", "N/A")
            consolidated_results[condition].setdefault("condition", condition)
            
            # Normalize and deduplicate symptoms
            current_symptoms = item.get("symptoms", [])
            if isinstance(current_symptoms, (str, list)):
                if isinstance(current_symptoms, str):
                    current_symptoms = [s.strip() for s in current_symptoms.split(",") if s.strip()]
                normalized_symptoms = set()
                for sym in current_symptoms:
                    sym = sym.lower().replace("_", " ").strip()
                    if sym:  # Avoid empty strings
                        for sub_sym in sym.split(","):
                            sub_sym = sub_sym.strip()
                            if sub_sym:
                                normalized_symptoms.add(sub_sym)
                consolidated_results[condition].setdefault("symptoms", set()).update(normalized_symptoms)
            
            # Collect all overviews (for preservation)
            current_overview = item.get("overview", "")
            if current_overview and current_overview != "Not available":
                consolidated_results[condition]["overviews"].append(current_overview)
            
            # Choose the longest non-empty summary from overview or description based on namespace
            current_overview = item.get("overview", "") if item["namespace"] in ["csv2", "nhs"] else ""
            current_description = item.get("description", "") if item["namespace"] == "csv1" else ""
            current_summary = max((current_overview, "overview") if current_overview else (("", "overview")),
                                (current_description, "description") if current_description else (("", "description")),
                                key=lambda x: len(x[0]) if x[0] else 0)
            if current_summary[0]:  # Only update if there’s a valid summary
                consolidated_results[condition]["summary"] = current_summary[0]
                consolidated_results[condition]["summary_source"] = current_summary[1]
            
            # Aggregate preventions, trimming and removing duplicates
            current_preventions = item.get("preventions", "").strip()
            if current_preventions and current_preventions != "Not available":
                existing_preventions = consolidated_results[condition].get("preventions", "").split(", ")
                if isinstance(existing_preventions, str):
                    existing_preventions = [existing_preventions] if existing_preventions.strip() else []
                new_preventions = [p.strip() for p in current_preventions.split(",") if p.strip()]
                all_preventions = list(dict.fromkeys([p for p in existing_preventions + new_preventions if p]))
                consolidated_results[condition]["preventions"] = ", ".join(all_preventions) if all_preventions else "Not available"
            
            # Use the first non-empty causes or url
            current_causes = item.get("causes", "").strip()
            if not consolidated_results[condition].get("causes") and current_causes and current_causes != "Not available":
                consolidated_results[condition]["causes"] = current_causes
            current_url = item.get("url", "").strip()
            if not consolidated_results[condition].get("url") and current_url and current_url != "Not available":
                consolidated_results[condition]["url"] = current_url
            
            consolidated_results[condition]["sources"].add(item["namespace"])
            consolidated_results[condition]["scores"].append(item["score"])
        
        # Convert to list and sort by average score
        unique_results = [
            {
                "condition": data["condition"],
                "symptoms": sorted(list(data["symptoms"])),  # Sorted for readability
                "summary": data.get("summary", "Not available"),
                #"summary_source": data.get("summary_source", "Not available"),
                #"overview": data.get("overviews", ["Not available"])[0] if data.get("overviews") else "Not available",  # First overview or default
                "preventions": data.get("preventions", "Not available"),
                "causes": data.get("causes", "Not available"),
                "url": data.get("url", "Not available"),
                "sources": ", ".join(data["sources"]),
                "average_score": sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
            }
            for data in consolidated_results.values()
        ]
        unique_results.sort(key=lambda x: x["average_score"], reverse=True)
        unique_results = unique_results[:top_k]  # Limit to top_k

        print(f"Retrieved {len(unique_results)} unique conditions for symptoms: {symptoms_text}")
        if unique_results:
            for item in unique_results:
                print(f"\nCondition: {item['condition']}, Average Score: {item['average_score']:.3f}, Sources: {item['sources']}")
                for key in ["symptoms", "summary", "summary_source", "overview", "preventions", "causes", "url"]:
                    value = item.get(key, "Not available")
                    if isinstance(value, str) and len(value) > 200:
                        print(f"  {key}: {value[:200]}... (truncated)")
                    elif value != "Not available" or key in ["symptoms", "summary_source"]:
                        print(f"  {key}: {value}")
        else:
            print("No matching conditions found.")
        
        return unique_results
    
    except Exception as e:
        print(f"Error retrieving data: {e}")
        return []

# Example usage for testing
if __name__ == "__main__":
    test_symptoms = "itching,fatigue,yellowish skin"
    retrieved_conditions = retrieve(test_symptoms)