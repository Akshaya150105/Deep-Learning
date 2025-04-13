from datasets import load_dataset

dataset = load_dataset("fhai50032/Symptoms_to_disease_7k")
train_data = dataset["train"]
print(train_data[0])
import pandas as pd

df = pd.DataFrame(train_data)
df.to_csv("symptoms_to_disease_7k.csv", index=False)
