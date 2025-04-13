import pandas as pd
import json
import re
from pathlib import Path

# Define paths
data_folder = Path("C:/BOOKS/SEM6/New folder/Data")
input_csv = data_folder / "symptoms_to_disease_7k.csv"
output_json = data_folder / "processed_csv1_data.json"

def process_csv_data():
    """Process the CSV data and extract structured information."""
    print(f"Reading CSV file: {input_csv}")
    try:
        df = pd.read_csv(input_csv)
        print(f"Successfully loaded CSV with {len(df)} rows")
        print("Column names:", df.columns.tolist())
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []
    
    # Check if the expected columns exist
    required_columns = ["Query", "Response"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"CSV is missing required columns: {missing_columns}")
        # Try to infer column names based on content
        if len(df.columns) >= 2:
            print("Attempting to use first two columns as Query and Response")
            df.columns = ["Query", "Response"] + [f"Column_{i+3}" for i in range(len(df.columns)-2)]
        else:
            print("Not enough columns in CSV")
            return []
    
    processed_data = []
    skipped_rows = 0
    
    for index, row in df.iterrows():
        try:
            # Ensure we have string values
            query = str(row["Query"]) if not pd.isna(row["Query"]) else ""
            response = str(row["Response"]) if not pd.isna(row["Response"]) else ""
            
            # Extract condition from response
            condition_match = re.search(r"You may have (.+?)(?:\.|$)", response, re.IGNORECASE)
            if not condition_match:
                skipped_rows += 1
                continue
            
            condition = condition_match.group(1).strip()
            
            # Extract symptoms directly from the "I may have" statement
            symptoms_match = re.search(r"Patient:I may have (.*?)(?=\.|$)", query, re.IGNORECASE)
            
            symptoms = []
            if symptoms_match:
                symptoms_text = symptoms_match.group(1).strip()
                symptoms = [s.strip() for s in symptoms_text.split(",") if s.strip()]
            else:
                # Try an alternative pattern if the first one fails
                alt_match = re.search(r"Patient:(.*?)(?:I may have|I am experiencing|I have|I feel) (.*?)(?=\.|$)", 
                                      query, re.IGNORECASE)
                if alt_match:
                    symptoms_text = alt_match.group(2).strip()
                    symptoms = [s.strip() for s in symptoms_text.split(",") if s.strip()]
            
            if not symptoms:
                skipped_rows += 1
                continue
            
            # Create structured data - only essential fields
            item_data = {
                "condition": condition,
                "symptoms": symptoms,
                "description": f"Medical condition: {condition}. Associated symptoms: {', '.join(symptoms)}."
            }
            
            processed_data.append(item_data)
            
            # Print progress
            if (index + 1) % 500 == 0:
                print(f"Processed {index + 1} rows, extracted {len(processed_data)} valid entries")
                
        except Exception as e:
            print(f"Error processing row {index}: {str(e)}")
            skipped_rows += 1
    
    print(f"Processing complete. Total rows: {len(df)}")
    print(f"Valid entries extracted: {len(processed_data)}")
    print(f"Skipped rows: {skipped_rows}")
    
    return processed_data

def save_to_json(data, output_path):
    """Save processed data to JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {len(data)} entries to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False

def main():
    """Main function to process CSV and save results."""
    print("Starting CSV1 data processing...")
    
    # Create data folder if it doesn't exist
    data_folder.mkdir(parents=True, exist_ok=True)
    
    # Process the CSV data
    processed_data = process_csv_data()
    
    if processed_data:
        # Save to JSON
        save_to_json(processed_data, output_json)
        print(f"\nExample of processed entry:")
        print(json.dumps(processed_data[0], indent=2))
    else:
        print("No valid data was extracted. Please check the CSV format and content.")

if __name__ == "__main__":
    main()