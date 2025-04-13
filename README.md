# Medical Symptoms Prediction Project

## Overview
The Medical Conditions Project is a prototype system designed to retrieve and generate responses about medical conditions based on user-provided symptoms using Retrieval-Augmented Generation (RAG). It processes datasets (e.g., NHS conditions, symptom-disease mappings, and disease-symptom data), embeds them into a Pinecone vector database, and integrates with a language model to provide context-aware responses. The project includes a React frontend, a FastAPI backend, and initial RAG components.

## Features
- **Data Processing**: Ingests and embeds medical condition data into Pinecone.
- **Frontend**: A React-based UI for inputting symptoms and displaying results.
- **Backend**: A FastAPI API with `/query` and `/health` endpoints.
- **RAG**: Partial implementation with a retriever (Pinecone queries) and generator (LLM responses) under development.

## Prerequisites
- **Python 3.10+**
- **Node.js 14+**
- **Pinecone API Key** 

