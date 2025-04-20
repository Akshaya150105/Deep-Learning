from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
from rag.retriver import retrieve  
import logging
import re
from rapidfuzz import fuzz
import random
from difflib import get_close_matches


# Initialize Mistral model and tokenizer
model_name = "mistralai/Mistral-7B-Instruct-v0.2"
hf_token = "use_your_key"  

# Configure 4-bit quantization
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        token=hf_token,
        quantization_config=quantization_config,
        device_map="auto"
    )
except Exception as e:
    logging.error(f"Failed to load model or tokenizer: {e}")
    raise RuntimeError("Could not load Mistral model. Ensure your Hugging Face token is valid and you have access to the model.")

logging.basicConfig(level=logging.INFO)

# Store last condition for follow-up queries
last_condition = None

# Non-symptom phrases and responses
ACKNOWLEDGE_PHRASES = [
    "thank you", "thanks", "okay", "ok", "got it", "alright", "cool",
    "appreciate it", "great", "good", "nice", "ty", "thx"
]
FAREWELL_PHRASES = [
    "bye", "goodbye", "see you", "see ya", "later", "take care",
    "cya", "farewell"
]
ACKNOWLEDGE_RESPONSES = [
    "You're welcome! {condition_prompt}",
    "No problem! {condition_prompt}",
    "Glad to help! {condition_prompt}",
    "Happy to be here for you! {condition_prompt}",
    "Anytime! {condition_prompt}"
]
FAREWELL_RESPONSES = [
    "Take care and feel better soon!",
    "Bye for now, hope you’re feeling better!",
    "See you later, rest up!",
    "Thanks for chatting, take it easy!",
    "Wishing you a speedy recovery!"
]
def fuzzy_match(query_words, keywords, cutoff=0.8):
    for word in query_words:
        if get_close_matches(word, keywords, n=1, cutoff=cutoff):
            return True
    return False

def generate_response(user_query, is_follow_up=False):
    """
    Generate a conversational response based on medical conditions or follow-up queries using Mistral-7B-Instruct.

    Args:
        user_query (str): User's query (e.g., "I have body ache." or "How do I prevent it?")
        is_follow_up (bool): If True, treat as a follow-up query about the last condition

    Returns:
        str: Conversational response with explanation and follow-up prompts
    """
    global last_condition
    logging.info(f"Current last_condition before processing: {last_condition}")

    try:
        # Normalize query
        query_lower = user_query.lower().strip()

        # Detect non-symptom queries
        is_acknowledge = any(fuzz.partial_ratio(query_lower, phrase) > 80 for phrase in ACKNOWLEDGE_PHRASES)
        is_farewell = any(fuzz.partial_ratio(query_lower, phrase) > 80 for phrase in FAREWELL_PHRASES)

        if is_farewell:
            if last_condition:
                logging.info(f"Resetting last_condition: {last_condition}")
                last_condition = None
            return random.choice(FAREWELL_RESPONSES)
        elif is_acknowledge:
            if last_condition:
                condition_prompt = (
                    f"I'm here to help with {last_condition['condition']}. "
                    f"Want to know how to prevent it, what causes it, or about other symptoms?"
                )
                return random.choice(ACKNOWLEDGE_RESPONSES).format(condition_prompt=condition_prompt)
            return random.choice([
                "You're welcome! Got any symptoms or questions?",
                "No worries! Tell me if you’re feeling anything!",
                "Happy to chat! Any health questions?"
            ])

        # Check for follow-up queries
        follow_up_type = None
        if is_follow_up or last_condition:
            query_words = query_lower.split() 
            if fuzzy_match(query_words, ["prevent", "prevention", "avoid", "stop"]):
                follow_up_type = "prevention"
            elif fuzzy_match(query_words, ["cause", "causes", "caused", "why", "how", "how did"]):
                follow_up_type = "causes"
            elif fuzzy_match(query_words, ["symptom", "symptoms", "feel", "feeling"]):
                follow_up_type = "symptoms"

        # Handle follow-up queries
        if follow_up_type and last_condition:
            logging.info(f"Handling follow-up for {last_condition['condition']}, type: {follow_up_type}")
            if follow_up_type == "prevention":
                prevention = last_condition.get("preventions", "N/A")
                if prevention=="Not available":
                    return(f"No prevention Available in my db")
                else:
                    return (
                    f"To help prevent {last_condition['condition']}, you can {prevention.lower()}" 
                    )
            elif follow_up_type == "causes":
                causes = last_condition.get("causes", "N/A")
                if causes=="Not available":
                    return (
                    f"No condition Available"
                    )
                else:
                    return (
                    f"{last_condition['condition']} is caused by {causes.lower()}")

            elif follow_up_type == "symptoms":
                symptoms = last_condition.get("symptoms", [])
                return (
                    f"With {last_condition['condition']}, you might feel {', '.join(symptoms) or 'aches, fever, or chills'}. "
                    f"Rest helps a lot. Want to know how to prevent it or what causes it?"
                )

        # New symptom query: retrieve conditions
        retrieved_data = retrieve(user_query)
        logging.info(f"Retrieved data: {retrieved_data}")
        if not retrieved_data or not retrieved_data[0].get("condition"):
            last_condition = None
            logging.info("No conditions found, resetting last_condition")
            return (
                "I couldn’t find any conditions matching that. Could you share more symptoms? "
                "I’m here to help figure it out!"
            )

        # Extract top condition
        top_condition = retrieved_data[0]
        last_condition = top_condition
        logging.info(f"Set last_condition: {last_condition}")
        symptoms_list = [s.strip() for s in user_query.split(",")]

        # Construct context with all fields
        context = (
            f"Condition: {top_condition.get('condition', 'Unknown')}\n"
            f"Matched Symptoms: {', '.join(top_condition.get('symptoms', []))}\n"
            f"Summary: {top_condition.get('summary', 'Not available')}\n"
            f"Overview: {top_condition.get('overview', 'Not available')}\n"
            f"Preventions: {top_condition.get('preventions', 'Not available')}\n"
            f"Causes: {top_condition.get('causes', 'Not available')}\n"
        )

        # Build conversational prompt with all available data
        prompt = (
            f"<s>[INST] The user says: '{user_query}'. Respond like a caring friend, starting with empathy like 'I’m sorry you’re feeling rough!' "
            f"Explain the condition in simple words, like what it is and how it feels, using the summary and overview. "
            f"Include preventions and causes if available. Keep it short, avoid big medical words, and sound reassuring, "
            f"like 'Most people get better with rest!' End with a question like 'Want to know how to prevent it or what causes it?' "
            f"Here’s the info:\n\n{context}[/INST] </s>"
        )

        # Set pad token
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
            model.config.pad_token_id = tokenizer.pad_token_id

        # Clear GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Tokenize
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to("cuda")

        # Generate
        outputs = model.generate(
            **inputs,
            max_new_tokens=600,
            do_sample=False,
            temperature=0.6,
            top_p=0.8,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3
        )

        # Decode and trim
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        logging.info(f"Prompt: {prompt}")
        logging.info(f"Raw generated text: {generated_text}")

        # Remove prompt
        if "[INST]" in generated_text:
            generated_text = generated_text.split("[/INST]")[-1].strip()
        generated_text = generated_text.split("< / FREETEXT >")[0].strip()

        # Fallback for short responses
        if len(generated_text) < 20 or not generated_text.strip():
            return (
                f"Hey, it looks like {top_condition['condition']} might match your symptoms ({user_query}). "
                "Want to know more about it?"
            )

        # Add follow-up prompt
        if not re.search(r"(want to know|curious|anything else)", generated_text.lower()):
            generated_text += " Want to know how to prevent it, what causes it, or other symptoms?"

        return generated_text

    except Exception as e:
        logging.error(f"Error during generation: {e}")
        return "Oops, something went wrong. Try again or chat with a doctor!"

# Interactive testing loop
if __name__ == "__main__":
    test_symptoms = "I have body ache."
    try:
        response = generate_response(test_symptoms)
        print("Generated Response:", response)

        while True:
            follow_up = input("Ask a follow-up question (or type 'exit' to stop): ")
            if follow_up.lower() == "exit":
                break
            response = generate_response(follow_up, is_follow_up=True)
            print("Generated Response:", response)

    except Exception as e:
        logging.error(f"Error in main: {e}")
        print("Failed to retrieve conditions or generate response. Check retriever.py.")
