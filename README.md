# Medical Symptoms Prediction Chatbot

## Overview
The project implements a Retrieval-Augmented Generation (RAG) system designed to assist users by retrieving relevant medical conditions based on symptoms and generating natural, reassuring responses with advice. The system leverages Pinecone for vector-based retrieval, Sentence Transformers for embeddings, and Mistral-7B-Insfruct-v0.2 for generating human-like responses. It is tailored for preliminary health guidance purposes, with a strong emphasis on encouraging professional medical consultation. 

      Retrieve the top matching medical conditions from a knowledge base using symptom inputs. 
      Generate conversational, empathetic responses with medical advice and next steps. 
      Ensure scalability and accuracy through vector search and domain-specific language modeling. 
     

## Features
- **Data Processing**: Ingests and embeds medical condition data into Pinecone.
- **Frontend**: A React-based UI for inputting symptoms and displaying results.
- **Backend**: A FastAPI API with `/query` and `/health` endpoints.
- **RAG**: Partial implementation with a retriever (Pinecone queries) and generator (LLM responses).
## Screenshots
![image](https://github.com/user-attachments/assets/f16a1667-38de-41d5-abcc-a5479dda46a0)
This is Home Page
![image](https://github.com/user-attachments/assets/3486fe6e-747a-4d51-8f63-6bac7968f4e8)
Gives the causes
![image](https://github.com/user-attachments/assets/03b0a186-fda4-4a20-a191-1ed80a48a480)
Gives the prevention
![image](https://github.com/user-attachments/assets/3c46b094-c705-40fd-9e6d-c85a2cd138a0)

Provides a conversational response.



## Prerequisites
- **Python 3.10+**
- **Node.js 14+**
- **Pinecone API Key** 

