import db_ops
import config

import pandas as pd

import tempfile
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

vs_id_var = "ITEM_CODE"
excel_id_var = "ITEM CODE"
excel_item_name_var = "ITEM NAME"
    
    
async def create_records(embs, item_codes):
    records = [{vs_id_var : item_codes[i], "embedding" : emb} for i, emb in enumerate(embs)]
    records_ls = [records[i:i+100] for i in range(0, len(records), 100)]
    
    url = ZILLIZ_ENDPOINT + "/v2/vectordb/entities/insert"
    headers = {
        "Authorization" : ZILLIZ_TOKEN,
        "Content-Type" : "application/json"
    }
    try:
        async with aiohttp.ClientSession() as session:
            for records_sub_ls in records_ls:
                payload = {
                    "collectionName": "treeyaa_vector_store",
                    "data" : records_sub_ls
                }
                await session.post(url, headers = headers, json = payload)
        print(f"Created records {item_codes} in vector store successfully")
    except Exception as e:
        print("Failed to create records in vector store. See the below error.\n\n", e)
    
async def delete_records(item_codes):
    url = ZILLIZ_ENDPOINT + "/v2/vectordb/entities/delete"
    headers = {
        "Authorization" : ZILLIZ_TOKEN,
        "Content-Type" : "application/json"
    }
    payload = {
        "collectionName": "treeyaa_vector_store",
        "filter": f"{vs_id_var} in {item_codes}"
        }
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, headers = headers, json = payload)
    if response.status == 200:
        print(f"Deleted {str(item_codes)} records in vector store successfully")
    else:
        print("Failed to delete records in vector store. See the below error.\n\n", response)
    
    
    
async def generate_embeddings(tamil_names : list):
    contents = [types.Content(role = "user", parts = [types.Part.from_text(text = tamil_name)]) for tamil_name in tamil_names]
    contents_ls = [contents[i:i+100] for i in range(0, len(contents), 100)]
    embs = []
    try:
        for content_sub_ls in contents_ls:
            result = await gemini.aio.models.embed_content(
                    model = "gemini-embedding-001",
                    contents = content_sub_ls)
            emb = [emb.values for emb in result.embeddings]
            embs += emb
        print("Successfully generated EMBEDDINGS")
        return embs
    except Exception as e:
        print("Failed to GENERATE EMBEDDINGS. Below is the error:\n\n", e)
    
async def download_stock(link, file_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                data = await response.content.read()
                async with aiofiles.open(file_path, mode = "wb") as f:
                    await f.write(data)
        print("Downloaded the stock excel file successfully.")
    except Exception as e:
        print(f"Failed to download the stock excel file. Below is the error:\n\n{e}")

async def generate_tamil_names(tanglish_names):
    contents = json.dumps({"items" : tanglish_names})
    try:
        response = await gemini.aio.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_2,
        )
        response = response.text
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
        "collectionName" : "treeyaa_vector_store",
        "outputFields" : ["ITEM_CODE"],
        "limit" : 1000
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, headers = headers, json = payload)
        res_obj = await response.json()
    res_obj = res_obj['data']
    ids = [dic[vs_id_var] for dic in res_obj]
    return ids
    
async def upload_stock(link):
    with tempfile.TemporaryDirectory() as dir:
        file_path = os.path.join(dir, "stock.xlsx")
        await download_stock(link, file_path)
        df = pd.read_excel(file_path, sheet_name = "OG", engine = "openpyxl")
        df[excel_id_var] = df[excel_id_var].astype(str)
        
        vs_item_codes = await get_vector_store_ids()
        excel_item_codes = df[excel_id_var].to_list()
        to_insert_item_codes = [item_code for item_code in excel_item_codes if item_code not in vs_item_codes]
        to_delete_item_codes = [item_code for item_code in vs_item_codes if item_code not in excel_item_codes]
        print("Excel item codes: ", excel_item_codes)
        print("vs_item_codes: ", vs_item_codes)
        print("to_insert_item_codes: ", to_insert_item_codes)
        print("to_delete_item_codes: ", to_delete_item_codes)
        
        if to_insert_item_codes:
            tanglish_names = df.loc[df[excel_id_var].isin(to_insert_item_codes), excel_item_name_var].tolist()
            tamil_names = await generate_tamil_names(tanglish_names)
            embs = await generate_embeddings(tamil_names)
            await create_records(embs, to_insert_item_codes)
            
            to_insert_items = df[df[excel_id_var].isin(to_insert_item_codes)].to_dict(orient = 'records')
            insert_input = {"to_insert_items" : to_insert_items, "tamil_names" : tamil_names}
        else:
            insert_input = None
            print("New ids not found so I didn't update the vector store")
            
        if to_delete_item_codes:
            await delete_records(to_delete_item_codes)
        else:
            print("No record is deleted")
            
        update_input = df[~df[excel_id_var].isin(to_insert_item_codes)].to_dict(orient = 'records')
        update_codes = df.loc[~df[excel_id_var].isin(to_insert_item_codes), excel_id_var].tolist()
        await db_ops.upload_stock.run(insert_input, to_delete_item_codes, update_input, update_codes)
        