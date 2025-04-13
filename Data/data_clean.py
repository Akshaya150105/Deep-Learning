import json

# Step 1: Load the original file
with open("nhs_conditions_all.json", "r") as f:
    data = json.load(f)

print(f"Original total entries: {len(data)}")

# Step 2: Filter out entries where 'symptoms' is [] or missing
filtered_data = [item for item in data if item.get("symptoms") not in ([], None)]

print(f"Filtered total entries: {len(filtered_data)}")

# Step 3: Overwrite the original file with filtered data
with open("nhs_conditions_all.json", "w") as f:
    json.dump(filtered_data, f, indent=2)

print("Original file updated successfully.")
