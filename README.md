# Medical Symptoms Prediction Project

## Overview
The Medical Conditions Project is a prototype system designed to retrieve and generate responses about medical conditions based on user-provided symptoms using Retrieval-Augmented Generation (RAG). It processes datasets (e.g., NHS conditions, symptom-disease mappings, and disease-symptom data), embeds them into a Pinecone vector database, and integrates with a language model to provide context-aware responses. The project includes a React frontend, a FastAPI backend, and initial RAG components.

## Features
- **Data Processing**: Ingests and embeds medical condition data into Pinecone.
- **Frontend**: A React-based UI for inputting symptoms and displaying results.
- **Backend**: A FastAPI API with `/query` and `/health` endpoints.
- **RAG**: Partial implementation with a retriever (Pinecone queries) and generator (LLM responses) under development.
## Screenshots
![image](https://github.com/user-attachments/assets/f16a1667-38de-41d5-abcc-a5479dda46a0)
![image](https://github.com/user-attachments/assets/3486fe6e-747a-4d51-8f63-6bac7968f4e8)
![image](https://github.com/user-attachments/assets/03b0a186-fda4-4a20-a191-1ed80a48a480)
![image](https://github.com/user-attachments/assets/3c46b094-c705-40fd-9e6d-c85a2cd138a0)





## Prerequisites
- **Python 3.10+**
- **Node.js 14+**
- **Pinecone API Key** 

