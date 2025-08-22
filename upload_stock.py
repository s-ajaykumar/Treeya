import db_ops
import config

import pandas as pd
from googletrans import Translator

from deep_translator import GoogleTranslator


import tempfile
import asyncio
import os
import aiohttp
import aiofiles
import json

from google import genai


gemini = genai.Client()


    
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

async def generate_tamil_names(tanglish_names: list):
    contents = json.dumps({"items" : tanglish_names.to_list()})
    response = await gemini.aio.models.generate_content(
        model = config.ttt.model,
        contents = contents,
        config = config.ttt.config_2,
    )
    response = response.text
    response = json.loads(response)
    return response['items']
    for name in tanglish_names:
        result = await translator.translate(name, src = "en", dest = "ta").text
        tamil_names.append(result)
    translator = Translator()
    tamil_names = [translator.translate(name, src = "en", dest = "ta").text for name in tanglish_names]
    return tamil_names

async def remove_whitespaces(df):
    for c in df.columns:
        if c == "QUANTITY" or c == "SELLING_PRICE":
            continue
        df[c] = df[c].str.strip()
    return df

async def convert_quantity_type_into_float(df):
    df['QUANTITY'] = df['QUANTITY'].astype(float)
    df['SELLING_PRICE'] = df['SELLING_PRICE'].astype(float)
    return df

async def main(link):
    with tempfile.TemporaryDirectory() as dir:
        file_path = os.path.join(dir, "stock.xlsx")
        await download_stock(link, file_path)
        df = pd.read_excel(file_path, sheet_name = "OG", engine="openpyxl")
        df = await remove_whitespaces(df)
        df = await convert_quantity_type_into_float(df)
        df['TANGLISH_NAME'] = [name.upper() for name in df['TANGLISH_NAME']]
        df['TAMIL_NAME'] = await generate_tamil_names(df['TANGLISH_NAME'])
        with tempfile.TemporaryDirectory() as dir2:
            file_path = os.path.join(dir2, "stock.csv")
            df.to_csv(file_path, index = False, encoding = "utf-8-sig")
            await db_ops.create_entities(df)