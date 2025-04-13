import json
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from pinecone import Pinecone, ServerlessSpec
import time
import gc
pc = Pinecone(api_key="pcsk_6L2y2o_AYPKUWFRfDk1z4jkAjvwAbLPrEHy4j3is9ktFLtwqQGkK2NdL2fkZsdZMwtowKZ")
index_name = "medical-conditions"
if index_name in pc.list_indexes().names():
    print(f"Deleting existing index {index_name}...")
    pc.delete_index(index_name)
    time.sleep(2)