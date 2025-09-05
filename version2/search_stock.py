import db_ops

import json
import time
import aiohttp
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
ZILLIZ_ENDPOINT = os.environ['ZILLIZ_ENDPOINT']
ZILLIZ_TOKEN = os.environ['ZILLIZ_TOKEN']
client = genai.Client()



async def generate_embeddings(items):
    contents = [types.Content(role = "user", parts = [types.Part.from_text(text = item)]) for item in items]
    try:
        result = await client.aio.models.embed_content(
                model = "gemini-embedding-001",
                contents = contents)
        emb = [emb.values for emb in result.embeddings]
        return emb
    except Exception as e:
        return {"status" : "failure", "data" : f"Failed to GENERATE EMBEDDINGS{e}"}
   

async def search_stock(item_names):
    search_result = []
    final_result = []
    emb = await generate_embeddings(item_names)
    if type(emb) == dict:
        return json.dumps(emb)
    async with aiohttp.ClientSession() as session:
        t1 = time.time()
        for e in emb:
            url = ZILLIZ_ENDPOINT + "/v2/vectordb/entities/search"
            headers = {
                "Authorization" : ZILLIZ_TOKEN,
                "Content-Type" : "application/json"
            }
            payload = {
                "collectionName": "treeyaa_vector_store",
                "data": [e],
                "searchParams" : {
                    "params" : {
                        "radius" : 0.75
                    }
                },
                "annsField": "embedding",
                "limit": 50,
                "outputFields": [
                    "ITEM_CODE"
                ]
            }
            response = await session.post(url, headers = headers, json = payload)
            search_result.append(await response.json())
        t2 = time.time()
        print(f"Time taken: Search Embeddings: {(t2-t1)*1000:2f} ms")
        
    t1 = time.time()
    for ix, result in enumerate(search_result):
        item_codes = [res['ITEM_CODE'] for res in result['data']]
        fetched_items = await db_ops.get_items(item_codes)
        final_result.append({"query" : item_names[ix], "search_result" : fetched_items})
    t2 = time.time()
    print(f"Time taken: Fetch Items From AzureDB: {(t2-t1)*1000:2f} ms")
    final_result = json.dumps(final_result, ensure_ascii = False)
    return final_result
    



'''def upload_data_zilliz():
    with open("data/tamil_name_embeddings.json", "r", encoding = "utf-8-sig") as f, \
        open("data/items.json", "r", encoding = "utf-8-sig") as f3,\
        open("data/treeyaa_stock.json", "w", encoding = "utf-8") as f2:
        data = json.load(f)
        data2 = json.load(f3)
        ls = []
        for i, d in enumerate(data):
            ls.append({"id" : str(i), "embedding" : d})
        json.dump(ls, f2, ensure_ascii = False, indent = 1)

        
    with open("data/treeyaa_stock.json", "r") as f:
        file = json.load(f)
        
    file = [file[i:i+100] for i in range(0, len(file), 100)]
    
    url = ZILLIZ_ENDPOINT + "/v2/vectordb/entities/insert"
    headers = {
        "Authorization" : ZILLIZ_TOKEN,
        "Content-Type" : "application/json"
    }

    for j in file:
        payload = {
            "collectionName" : "treeyaa_stock_db",
            "data" : j
        }
        response = requests.post(url, headers = headers, json = payload)
        print(response.status_code, response.json())

#upload_data_zilliz()'''

