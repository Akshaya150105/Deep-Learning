from retriver import retrieve
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM,
    pipeline
)
import torch

# Load the FLAN-T5 model (instruction-tuned, no [INST] format)
model_name = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

def generate(symptom_query, top_k=1):
    symptom_query = symptom_query.strip()
    retrieved_info = retrieve(symptom_query, top_k=top_k)

    if not retrieved_info:
        return "Sorry, I couldn't find any medical conditions matching your symptoms."

    context_chunks = []
    for item in retrieved_info:
        chunk = f"""
        Condition: {item['condition']}
        Symptoms: {', '.join(item['symptoms'])}
        Summary: {item['summary']}
        Preventions: {item['preventions']}
        Causes: {item['causes']}
        """
        context_chunks.append(chunk.strip())

    context = "\n\n".join(context_chunks)

    prompt = f"""You are a helpful medical assistant. Use the following data to explain what might be causing the symptoms: {symptom_query}.\n\n{context}\n\nProvide a concise, professional explanation."""

    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    output = model.generate(**inputs, max_new_tokens=300, do_sample=True, temperature=0.7)
    result = tokenizer.decode(output[0], skip_special_tokens=True)

    return result.strip()

# Example usage
if __name__ == "__main__":
    symptoms = "itching, fatigue, yellowish skin"
    answer = generate(symptoms)
    print("\nGenerated Answer:\n", answer)
