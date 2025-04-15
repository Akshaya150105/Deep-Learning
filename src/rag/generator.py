from transformers import pipeline

# Initialize LLM (using a lightweight model)
generator = pipeline("text-generation", model="distilgpt2", max_length=150)

def generate_response(retrieved_data, user_query):
    """
    Generate a natural language response based on retrieved medical conditions.
    
    Args:
        retrieved_data (list): List of condition dictionaries from retriever.py
        user_query (str): Original symptoms query (e.g., "itching,fatigue,yellowish skin")
    
    Returns:
        str: Generated response with medical advice and next steps
    """
    try:
        if not retrieved_data or not retrieved_data[0].get("condition"):
            return "No relevant conditions found for your symptoms. Please consult a healthcare professional."

        # Extract top condition for detailed response
        top_condition = retrieved_data[0]
        symptoms_list = user_query.split(",")
        
        # Construct context from top condition
        context = (
            f"Condition: {top_condition['condition']}\n"
            f"Matched Symptoms: {', '.join(top_condition['symptoms'])}\n"
            f"Summary: {top_condition['summary']}\n"
        )
        if top_condition["overview"] != "Not available":
            context += f"Overview: {top_condition['overview']}\n"
        if top_condition["preventions"] != "Not available":
            context += f"Preventions: {top_condition['preventions']}\n"
        if top_condition["url"] != "Not available":
            context += f"More Info: {top_condition['url']}\n"

        # Build prompt with user query and context
        prompt = (
            f"Based on the following medical context: {context}\n"
            f"User query: I am experiencing {', '.join(symptoms_list)}.\n"
            f"Provide a concise, helpful response with advice and next steps for the user. Ensure the tone is professional yet reassuring."
        )

        # Generate response
        response = generator(prompt, max_length=150, num_return_sequences=1, truncation=True)[0]['generated_text']
        generated_text = response[len(prompt):].strip()  # Remove prompt from response
        
        # Ensure response is meaningful; fallback if too short
        if len(generated_text.split()) < 3:
            return f"Based on your symptoms ({user_query}), {top_condition['condition']} is a possible condition. Please consult a doctor for a proper diagnosis."
        
        return generated_text

    except Exception as e:
        print(f"Error generating response: {e}")
        return "Error generating response. Please try again or consult a healthcare professional."

# Example usage for testing
if __name__ == "__main__":
    from retriver import retrieve
    test_symptoms = "itching,fatigue,yellowish skin"
    retrieved_conditions = retrieve(test_symptoms)
    response = generate_response(retrieved_conditions, test_symptoms)
    print("Generated Response:", response)