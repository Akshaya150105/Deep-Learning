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
            # Clean and join symptoms for embedding
            symptoms = item.get("symptoms", [])
            
            # Join cleaned symptoms into a single string for embedding
            symptoms_text = ", ".join(symptoms) if symptoms else item.get("condition", "")
            
            # Store item metadata with all available fields
            item_id = f"{namespace}-{i}"
            item_metadata = {
                "id": item_id,
                "condition": item.get("condition", ""),
                "symptoms": symptoms,  # Keep as list in metadata
                "overview": item.get("overview", ""),
                "url": item.get("url", ""),
                "source": namespace
            }
            texts.append(item_metadata)
            
            # Create embedding with retry logic using symptoms_text
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    embedding = embedder.encode(symptoms_text, convert_to_numpy=True)
                    all_vectors.append((
                        item_id,
                        embedding.tolist(),
                        {
                            "condition": item_metadata["condition"],
                            "symptoms": item_metadata["symptoms"],
                            "overview": item_metadata["overview"],
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

print("\nProcessing NHS data...")
try:
    with open(data_folder / "nhs_conditions_all_clean.json", "r") as f:
        json_data = json.load(f)
    nhs_texts = upsert_to_pinecone(json_data, "nhs")
except Exception as e:
    print(f"Error processing NHS data: {e}")
    nhs_texts = []