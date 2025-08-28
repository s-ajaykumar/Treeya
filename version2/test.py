import json
import csv
import aiohttp
import asyncio
import soundfile as sf
from google import genai
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


def csv_to_json():
    data = {}
    with open('data/items.csv', mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            row["JSON_QUANTITY"] = float(row['JSON_QUANTITY']) 
            row['SELLING_PRICE'] = float(row['SELLING_PRICE'])
            data[str(i)] = row

    with open('data/items.json', mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4, ensure_ascii = False)
#csv_to_json()




    
    