import json
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from pinecone import Pinecone, ServerlessSpec
import time

# Define data folder
data_folder = Path("C:/BOOKS/SEM6/New folder/Data")

# Initialize embedder
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Pinecone client
pc = Pinecone(api_key="pcsk_6L2y2o_AYPKUWFRfDk1z4jkAjvwAbLPrEHy4j3is9ktFLtwqQGkK2NdL2fkZsdZMwtowKZ")  # Replace with your key or use environment variable

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
        time.sleep(2)  # Increased wait time
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

# Function to process and upsert data
def upsert_to_pinecone(data, namespace):
    index = get_index_object()  # Get a fresh index object for each upsert
    if not data:
        print(f"No data to upsert for namespace {namespace}")
        return []
    texts = []
    embeddings = []
    for i, item in enumerate(data):
        text = " ".join(item.get("symptoms", [])) + " " + str(item.get("description", ""))  # Ensure description is string
        texts.append({
            "id": f"{namespace}-{i}",
            "condition": item.get("condition", ""),
            "text": text,
            "url": item.get("url", ""),
            "source": namespace
        })
        embedding = embedder.encode(text, convert_to_numpy=True)
        embeddings.append(embedding)
    
    embeddings = np.array(embeddings).astype('float32').tolist()
    vectors = [
        (text["id"], embedding, {
            "condition": text["condition"],
            "text": text["text"],
            "url": text["url"],
            "source": text["source"]
        })
        for text, embedding in zip(texts, embeddings)
    ]
    try:
        index.upsert(vectors=vectors, namespace=namespace)
        print(f"Upserted {len(vectors)} vectors to namespace {namespace}")
    except Exception as e:
        print(f"Failed to upsert to namespace {namespace}: {e}")
        raise
    return texts

# Process JSON (NHS)
with open(data_folder / "nhs_conditions_all.json", "r") as f:
    json_data = json.load(f)
nhs_texts = upsert_to_pinecone(json_data, "nhs")

# Process CSV1 (sample dataset)
csv1 = pd.read_csv("C:\\BOOKS\\SEM6\\New folder\\Data\\symptoms_to_disease_7k.csv")
print("CSV1 head:\n", csv1.head())
csv1_data = []
for index, row in csv1.iterrows():
    query = row.get("Query", "").lower()
    response = row.get("Response", "")
    if "you may have" in response.lower():
        condition = response.replace("you may have", "").strip()
        # Extract symptoms from query
        symptoms_start = query.find("Patient:I may have")  
        if symptoms_start != -1:
            symptoms_part = query[symptoms_start + len("Patient:I may have"):].strip()
            symptoms = [s.strip() for s in symptoms_part.split(",") if s.strip()]
            
        else:
            symptoms = ["unspecified symptoms"]  # Fallback if symptoms not found
        csv1_data.append({
            "condition": condition,
            "symptoms": symptoms,
            "description": f"Condition identified: {condition} with symptoms: {', '.join(symptoms)}",
            "url": ""
        })
        print(f"Row {index}: Condition={condition}, Symptoms={symptoms}")  # Debug print
print(f"CSV1 data length: {len(csv1_data)}")  # Debug print
csv1_texts = upsert_to_pinecone(csv1_data, "csv1")

# Process CSV2 (new dataset with Overview)
csv2 = pd.read_csv("C:\\BOOKS\\SEM6\\New folder\\Data\\disease_symptoms_dataset.csv", low_memory=False)  # Avoid DtypeWarning
print("CSV2 head:\n", csv2.head())
csv2_data = []
for index, row in csv2.iterrows():
    condition = row.get("Disease", "").lower().strip()
    if condition:
        symptoms = str(row.get("Symptoms", "")).split(".")  # Convert to string to handle NaN
        symptoms = [s.strip() for s in symptoms if s.strip() and any(word in s.lower() for word in ["pain", "fatigue", "itching", "swelling", "fever"])]
        overview = str(row.get("Overview", ""))  # Convert to string to handle NaN
        url = row.get("Link", "")
        csv2_data.append({
            "condition": condition.title(),
            "symptoms": symptoms,
            "description": overview if overview else f"Condition identified from symptoms: {', '.join(symptoms)}",
            "url": url if url else ""
        })
csv2_texts = upsert_to_pinecone(csv2_data, "csv2")

# Save texts for reference
all_texts = {"nhs": nhs_texts, "csv1": csv1_texts, "csv2": csv2_texts}
with open(data_folder / "texts.json", "w") as f:
    json.dump(all_texts, f)