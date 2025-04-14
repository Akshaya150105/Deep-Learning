import json


'''print(f"Original total entries: {len(data)}")

# Step 2: Filter out entries where 'symptoms' is [] or missing
filtered_data = [item for item in data if item.get("symptoms") not in ([], None)]

print(f"Filtered total entries: {len(filtered_data)}")

# Step 3: Overwrite the original file with filtered data
with open("nhs_conditions_all.json", "w") as f:
    json.dump(filtered_data, f, indent=2)

print("Original file updated successfully.")'''


import json
import re

# Step 1: Load the original file
with open("nhs_conditions_all_clean.json", "r") as f:
    data = json.load(f)

nhs_texts = []
nhs_data = []

for i, item in enumerate(data):
    try:
        condition = item.get("condition", "").strip()
        if not condition:
            continue

        # Clean symptoms list
        symptoms = item.get("symptoms", [])
        cleaned_symptoms = []
        for symptom in symptoms:
            symptom_str = str(symptom).strip()
            # Filter out URLs (starts with http or contains www)
            if not (symptom_str.lower().startswith("http") or "www" in symptom_str.lower()):
                # Normalize special characters and remove empty entries
                cleaned_symptom = symptom_str.replace("\u00e2\u20ac\u201c", " ").strip()
                if cleaned_symptom:
                    cleaned_symptoms.append(cleaned_symptom)
        
        # Skip if no valid symptoms after cleaning
        if not cleaned_symptoms:
            continue

        overview = item.get("overview", "")
        cleaned_overview = ""
        if overview:
            overview_str = str(overview).strip()
            # Filter out URLs (starts with http or contains www)
            if not (overview_str.lower().startswith("http") or "www" in overview_str.lower()):
                # Normalize special characters and remove empty entries
                cleaned_overview = overview_str.replace("\u00e2\u20ac\u2122", " ").strip()

        url = item.get("url", "")


        nhs_data.append({
            "condition": condition,
            "symptoms": cleaned_symptoms[:5],  # Limit to 5 for consistency (optional)
            "overview": cleaned_overview,
            "url": url
        })
    except Exception as e:
        print(f"Error processing NHS item {i}: {e}")

print(f"Filtered total entries: {len(nhs_data)}")

# Save cleaned data back to nhs_conditions_all_clean.json
with open("nhs_conditions_all_clean.json", "w") as f:
    json.dump(nhs_data, f, indent=4)
print(f"Cleaned NHS data saved to nhs_conditions_all_clean.json")