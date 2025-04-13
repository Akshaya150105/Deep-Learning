from datasets import load_dataset
import pandas as pd
dataset = load_dataset("Shaheer14326/Disease_Symptoms_Dataset")

train_data = dataset["train"]
df = pd.DataFrame(train_data)
df.to_csv("disease_symptoms_dataset.csv", index=False)
