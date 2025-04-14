from transformers import pipeline

# Initialize LLM (using a lightweight model for now)
generator = pipeline("text-generation", model="distilgpt2", max_length=100)

def generate_response(retrieved_data, user_query):
    """
    Generate a natural language response based on retrieved conditions.
    
    Args:
        retrieved_data (list): List of condition metadata from Pinecone
        user_query (str): Original symptoms query
    
    Returns:
        str: Generated response
    """
    try:
        if not retrieved_data:
            return "No relevant conditions found. Please consult a doctor."
        
        # Construct context from retrieved data
        context = " ".join([f"{item['condition']}: {item['text']}" for item in retrieved_data])
        prompt = f"Based on the following medical context: {context}\nUser query: {user_query}\nResponse: "
        
        # Generate response
        response = generator(prompt, max_length=100, num_return_sequences=1)[0]['generated_text']
        return response[len(prompt):].strip()  # Remove prompt from response

    except Exception as e:
        print(f"Error generating response: {e}")
        return "Error generating response. Please try again."

# Example usage for testing
if __name__ == "__main__":
    from retriever import retrieve
    test_symptoms = "itching,fatigue,yellowish skin"
    retrieved_conditions = retrieve(test_symptoms)
    response = generate_response(retrieved_conditions, test_symptoms)
    print("Generated Response:", response)