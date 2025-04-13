import json
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from pinecone import Pinecone, ServerlessSpec
import time
import gc 

data_folder = Path("C:/BOOKS/SEM6/New folder/Data")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Pinecone client
pc = Pinecone(api_key="pcsk_6L2y2o_AYPKUWFRfDk1z4jkAjvwAbLPrEHy4j3is9ktFLtwqQGkK2NdL2fkZsdZMwtowKZ")

# Create or connect to a single index with serverless spec
index_name = "medical-conditions"

if index_name not in pc.list_indexes().names():
    print(f"Creating index {index_name}...")
    pc.create_index(
        name=index_name,
        dimension=384,  # Matches MiniLM-L6-v2 embedding size
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"  # Use a supported free-tier region
        )
    )
    # Wait for index to be ready
    while not pc.describe_index(index_name).status['ready']:
        print("Waiting for index to be ready...")
        time.sleep(2)
    print(f"Index {index_name} created and ready.")

# Function to get a fresh index object with debugging
def get_index_object():
    try:
        index = pc.Index(index_name)
        print(f"Connected to index {index_name}. Type of index: {type(index)}")
        index_desc = index.describe_index_stats()
        print(f"Index stats: {index_desc}")
        return index
    except Exception as e:
        print(f"Failed to connect to index {index_name}: {e}")
        raise

# Function to process and upsert data with better error handling
def upsert_to_pinecone(data, namespace, batch_size=50):
    index = get_index_object()
    if not data:
        print(f"No data to upsert for namespace {namespace}")
        return []
    
    texts = []
    all_vectors = []
    
    # Process items and create embeddings
    for i, item in enumerate(data):
        try:
            # Prepare text for embedding - combine symptoms and description
            symptoms_text = ", ".join(item.get("symptoms", []))
            description = str(item.get("description", ""))
            
            # Limit text size to prevent embedding issues
            max_text_length = 5000
            if len(symptoms_text) + len(description) > max_text_length:
                if len(symptoms_text) > 500:
                    symptoms_text = symptoms_text[:500]
                if len(description) > max_text_length - len(symptoms_text):
                    description = description[:max_text_length - len(symptoms_text)]
            
            text = symptoms_text + " " + description
            
            # Store item metadata
            item_id = f"{namespace}-{i}"
            item_metadata = {
                "id": item_id,
                "condition": item.get("condition", ""),
                "text": text[:1000],  # Limit metadata length
                "url": item.get("url", ""),
                "source": namespace
            }
            texts.append(item_metadata)
            
            # Create embedding with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    embedding = embedder.encode(text, convert_to_numpy=True)
                    all_vectors.append((
                        item_id,
                        embedding.tolist(),
                        {
                            "condition": item_metadata["condition"],
                            "text": item_metadata["text"],
                            "url": item_metadata["url"],
                            "source": item_metadata["source"]
                        }
                    ))
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Retry {attempt+1} for item {i} ({item.get('condition', 'unknown')}) due to: {e}")
                        time.sleep(1)
                    else:
                        print(f"Failed to embed item {i} after {max_retries} attempts: {e}")
            
            # Print progress for large datasets
            if i > 0 and i % 50 == 0:
                print(f"Processed {i}/{len(data)} items")
                
        except Exception as e:
            print(f"Error processing item {i}: {e}")
    
    # Upload vectors in batches
    if all_vectors:
        for j in range(0, len(all_vectors), batch_size):
            batch = all_vectors[j:j+batch_size]
            try:
                index.upsert(vectors=batch, namespace=namespace)
                print(f"Upserted batch {j//batch_size + 1}/{(len(all_vectors) + batch_size - 1)//batch_size} to {namespace}: {len(batch)} vectors")
            except Exception as e:
                print(f"Failed to upsert batch to namespace {namespace}: {e}")
                # Try one more time with smaller batch if it fails
                if len(batch) > 10:
                    half_size = len(batch) // 2
                    try:
                        print("Retrying with smaller batch size...")
                        index.upsert(vectors=batch[:half_size], namespace=namespace)
                        index.upsert(vectors=batch[half_size:], namespace=namespace)
                        print("Smaller batches upserted successfully")
                    except Exception as e2:
                        print(f"Failed again with smaller batch: {e2}")
    
    return texts

# -------------------- CSV2 PROCESSING FIRST --------------------
# Process CSV2 (new dataset with Overview) in batches
print("\nProcessing CSV2 data...")
try:
    csv2 = pd.read_csv(data_folder / "disease_symptoms_dataset.csv", low_memory=False)
    print("CSV2 head:\n", csv2.head())
    
    csv2_texts = []
    batch_size = 20  # Keep batching for memory management
    all_csv2_data = []  # Collect all data in one list
    
    for i in range(0, len(csv2), batch_size):
        print(f"\nProcessing CSV2 batch {i//batch_size + 1}/{(len(csv2) + batch_size - 1)//batch_size}")
        batch = csv2.iloc[i:i+batch_size]
        batch_data = []
        
        for index, row in batch.iterrows():
            try:
                condition = str(row.get("Disease", ""))
                if condition.lower() == "nan" or not condition.strip():
                    continue
                symptoms_text = str(row.get("Symptoms", ""))
                symptoms = []
                if symptoms_text.lower() != "nan" and symptoms_text.strip():
                    symptoms = [s.strip() for s in symptoms_text.split(".") 
                              if s.strip() and any(word in s.lower() for word in 
                                                 ["pain", "fatigue", "itching", "swelling", "fever"])]
                overview = str(row.get("Overview", ""))
                if overview.lower() == "nan":
                    overview = ""
                url = str(row.get("Link", ""))
                if url.lower() == "nan":
                    url = ""
                batch_data.append({
                    "condition": condition.strip().title(),
                    "symptoms": symptoms[:5],
                    "description": overview[:1000] if overview else f"Condition: {condition}",
                    "url": url
                })
            except Exception as e:
                print(f"Error processing CSV2 row {index}: {e}")
        all_csv2_data.extend(batch_data)
        gc.collect()
    
    # Upsert all csv2 data into a single namespace
    if all_csv2_data:
        csv2_texts = upsert_to_pinecone(all_csv2_data, "csv2")
    
except Exception as e:
    print(f"Error processing CSV2: {e}")
    csv2_texts = []

# -------------------- NHS PROCESSING SECOND --------------------
print("\nProcessing NHS data...")
try:
    with open(data_folder / "nhs_conditions_all.json", "r") as f:
        json_data = json.load(f)
    nhs_texts = upsert_to_pinecone(json_data, "nhs")
except Exception as e:
    print(f"Error processing NHS data: {e}")
    nhs_texts = []

# -------------------- CSV1 PROCESSING LAST --------------------
print("\nProcessing CSV1 data from JSON file...")
try:
    # Load the processed JSON file that was created by your extraction script
    processed_json_path = data_folder / "processed_csv1_data.json"
    
    with open(processed_json_path, "r", encoding="utf-8") as f:
        csv1_data = json.load(f)
    
    print(f"Loaded {len(csv1_data)} entries from processed JSON")
    
    # Add URL field if not present in your JSON structure
    for item in csv1_data:
        if "url" not in item:
            item["url"] = ""
    
    # Print a sample entry for verification
    if csv1_data:
        print("Sample entry from processed JSON:")
        print(json.dumps(csv1_data[0], indent=2))
    
    # Use the upsert function with the loaded data
    csv1_texts = upsert_to_pinecone(csv1_data, "csv1")
    
except Exception as e:
    print(f"Error processing CSV1 from JSON: {e}")
    csv1_texts = []

# Save texts for reference
print("\nSaving text data...")
all_texts = {"nhs": nhs_texts, "csv1": csv1_texts, "csv2": csv2_texts}
try:
    with open(data_folder / "texts.json", "w") as f:
        json.dump(all_texts, f)
    print(f"Successfully saved texts to {data_folder / 'texts.json'}")
except Exception as e:
    print(f"Error saving texts: {e}")

print("\nScript completed!")