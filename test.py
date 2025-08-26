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
    data = []
    with open('items.csv', mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row["JSON_QUANTITY"] = float(row['JSON_QUANTITY']) 
            row['SELLING_PRICE'] = float(row['SELLING_PRICE'])
            data.append(row)

    with open('data/items_version2_progress.json', mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4, ensure_ascii = False)

#csv_to_json()




def generate_embeddings(contents):
    embeddings_ls = []
    client = genai.Client()
    result = client.models.embed_content(
            model = "gemini-embedding-001",
            contents = contents)
    print("generated embeddings")
    for embedding in result.embeddings:
        embeddings_ls.append(embedding.values)
    print("appended embeddings")
    return embeddings_ls

def convert_text_to_embedding():
    with open('data/items_version2.csv', mode='r', newline='', encoding='utf-8-sig') as csvfile:
        reader = list(csv.DictReader(csvfile))
        tamil_names = [r['TANGLISH_NAME'] for r in reader]

        chunk_size = 100
        chunks = [tamil_names[i:i + chunk_size] for i in range(0, len(tamil_names), chunk_size)]
        
        embeddings = [generate_embeddings(c) for c in chunks]
        embeddings = [e for e_ls in embeddings for e in e_ls]
        
        with open('data/tanglish_name_embeddings.json', mode='w', encoding='utf-8-sig') as jsonfile:
            json.dump(embeddings, jsonfile, indent=4, ensure_ascii = False)
    
def read_csv():
    with open("data/tamil_name_embeddings.json", "r", encoding="utf-8-sig") as f:
        file = json.load(f) 
        ls = []
        for i, r in enumerate(file):
            ls.append({"id" : str(i), "embedding" : r})
        with open("data/treeya_stock_emb.json", "w", encoding='utf-8') as f:
            json.dump(ls, f, ensure_ascii = False, indent = 4)
#read_csv()    
#convert_text_to_embedding()


        







'''
audio_link = ""
ogg_file_path = "audio.ogg"
async def main(audio_link, ogg_file_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(audio_link) as response:
            data = await response.content.read()
            with open(ogg_file_path, mode = "wb") as f:
                f.write(data)
    data, sr = sf.read(ogg_file_path) 
    wav_file_path = ogg_file_path[:-4] + ".wav" 
    sf.write(wav_file_path, data, sr) 
                
if __name__ == "__main__":
    asyncio.run(main(audio_link, ogg_file_path))'''
                
