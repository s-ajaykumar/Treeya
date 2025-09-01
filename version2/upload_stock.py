import db_ops
import config

import pandas as pd

import tempfile
import asyncio
import os
import aiohttp
import aiofiles
import json
from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

gemini = genai.Client()
ZILLIZ_ENDPOINT = os.environ['ZILLIZ_ENDPOINT']
ZILLIZ_TOKEN = os.environ['ZILLIZ_TOKEN']


    
async def create_records(records, item_codes):
    url = ZILLIZ_ENDPOINT + "/v2/vectordb/entities/insert"
    headers = {
        "Authorization" : ZILLIZ_TOKEN,
        "Content-Type" : "application/json"
    }
    payload = {
        "collectionName": "treeyaa_stock_db_version2",
        "data" : records
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, headers = headers, json = payload)
    if response.status == 200:
        print(f"Created records {item_codes} in vector store successfully")
    else:
        print("Failed to create records in vector store. See the below error.\n\n", response)
    
async def delete_records(item_codes):
    url = ZILLIZ_ENDPOINT + "/v2/vectordb/entities/delete"
    headers = {
        "Authorization" : ZILLIZ_TOKEN,
        "Content-Type" : "application/json"
    }
    payload = {
        "collectionName": "treeyaa_stock_db_version2",
        "filter": f"ITEM_CODE in {item_codes}"
        }
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, headers = headers, json = payload)
    if response.status == 200:
        print(f"Deleted {str(item_codes)} records in vector store successfully")
    else:
        print("Failed to delete records in vector store. See the below error.\n\n", response)
    
    
    
async def generate_embeddings(tamil_names : list):
    contents = [types.Content(role = "user", parts = [types.Part.from_text(text = tamil_name)]) for tamil_name in tamil_names]
    try:
        result = await gemini.aio.models.embed_content(
                model = "gemini-embedding-001",
                contents = contents)
        emb = [emb.values for emb in result.embeddings]
        print("Successfully generated EMBEDDINGS")
        return emb
    except Exception as e:
        print("Failed to GENERATE EMBEDDINGS")
    
async def download_stock(link, file_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                print(response.content_type)
                data = await response.content.read()
                async with aiofiles.open(file_path, mode = "wb") as f:
                    await f.write(data)
        print("Downloaded the stock excel file successfully.")
    except Exception as e:
        print(f"Failed to download the stock excel file. Below is the error:\n\n{e}")

async def generate_tamil_names(tanglish_names):
    print(tanglish_names)
    contents = json.dumps({"items" : tanglish_names})
    try:
        response = await gemini.aio.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_2,
        )
        response = response.text
        print(response)
        response = json.loads(response)
        print("Generated TAMIL names successfully")
        return response['items']
    except Exception as e:
        print("Failed to generate TAMIL names. Below is the error:\n\n", e)

async def remove_whitespaces(df):
    for c in df.columns:
        if c == "JSON_QUANTITY" or c == "SELLING_PRICE":
            continue
        df[c] = df[c].str.strip()
    return df

async def convert_quantity_type_into_float(df):
    df['JSON_QUANTITY'] = df['JSON_QUANTITY'].astype(float)
    df['SELLING_PRICE'] = df['SELLING_PRICE'].astype(float)
    return df

async def get_vector_store_ids():
    url = ZILLIZ_ENDPOINT + "/v2/vectordb/entities/query"
    headers = {
        "Authorization" : ZILLIZ_TOKEN,
        "Content-Type" : "application/json"
    }
    payload = {
        "collectionName": "treeyaa_stock_db_version2",
        "filter": "",
        "output_fields" : ["ITEM_CODE"]
        }
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, headers = headers, json = payload)
        res_obj = await response.json()
    res_obj = res_obj['data']
    ids = [dic['ITEM_CODE'] for dic in res_obj]
    return ids
    
async def upload_stock(link):
    with tempfile.TemporaryDirectory() as dir:
        file_path = os.path.join(dir, "stock.xlsx")
        await download_stock(link, file_path)
        df = pd.read_excel(file_path, sheet_name = "OG", engine = "openpyxl")
        vs_ids = await get_vector_store_ids()
        to_update_item_codes = [id for id in df['ITEM CODE'] if id not in vs_ids]
        to_delete_item_codes = [id for id in vs_ids if id not in df['ITEM CODE']]
        print(to_delete_item_codes)
        if to_update_item_codes:
            tanglish_names = df.loc[df['ITEM CODE'].isin(to_update_item_codes), 'ITEM NAME'].tolist()
            tamil_names = await generate_tamil_names(tanglish_names)
            embs = await generate_embeddings(tamil_names)
            records = [{"ITEM CODE" : to_update_item_codes[i], "embedding" : emb} for i, emb in enumerate(embs)]
            await create_records(records, to_update_item_codes)
        else:
            print("New ids not found so I didn't update the vector store")
        '''if to_delete_item_codes:
            await delete_records(to_delete_item_codes)
        else:
            print("No record is deleted")'''
        