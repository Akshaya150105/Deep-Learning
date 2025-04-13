from transformers import pipeline

# Initialize LLM
generator = pipeline("text-generation", model="distilgpt2")

def generate_response(retrieved_data, user_query):
    context = " ".join([item["text"] for item in retrieved_data])
    prompt = f"Based on the following medical context: {context}\nUser query: {user_query}\nResponse:"
    response = generator(prompt, max_length=100, num_return_sequences=1)[0]['generated_text']
    return response

# Example usage
if __name__ == "__main__":
    symptoms = "itching, fatigue, yellowish skin"
    retrieved_data = retrieve(symptoms)
    response = generate_response(retrieved_data, symptoms)
    print("Generated Response:", response)