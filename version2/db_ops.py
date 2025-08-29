from azure.data.tables.aio import TableClient
from azure.data.tables.aio import TableServiceClient

from azure.core.exceptions import ResourceNotFoundError
from azure.core.exceptions import ResourceExistsError
from azure.data.tables import UpdateMode

from typing import Any, List, Mapping, Tuple, Union
from azure.data.tables import TableEntity, TransactionOperation
from azure.data.tables import TableTransactionError

EntityType = Union[TableEntity, Mapping[str, Any]]
OperationType = Union[TransactionOperation, str]
TransactionOperationType = Union[Tuple[OperationType, EntityType], Tuple[OperationType, EntityType, Mapping[str, Any]]]

import time
import json
from dotenv import load_dotenv
import os
import csv
import asyncio

load_dotenv()

CONNECTION_STRING = os.environ["AZURE_TABLE_STORAGE_CONNECTION_STRING"]
items_table = TableClient.from_connection_string(CONNECTION_STRING, table_name = "items")
users_in_process_table = TableClient.from_connection_string(CONNECTION_STRING, table_name = "usersInProcess")



'''async def get_entity(partition_key, row_key):
    return await items_table.get_entity(partition_key = partition_key, row_key = row_key)'''
    
    
async def get_stock_db():
    items = []
    try:
        queried_entities = items_table.query_entities(query_filter = "", select=["TAMIL_NAME", "TANGLISH_NAME", "JSON_QUANTITY", "JSON_QUANTITY_TYPE", "SELLING_PRICE", "CATEGORY"])
        async for entity in queried_entities:
            items.append(entity)
        print("Fetched STOCK DB successfully.")
        return items
    except Exception as e:
        print("Failed to fetch STOCK DB. Below is the error:\n", e)


async def get_user_in_process_data(partition_key):
    try:
        filter_query = f"PartitionKey eq '{partition_key}'"
        entities = []
        async for entity in users_in_process_table.list_entities(filter = filter_query):
            entities.append(entity['data'])
        return entities
    except ResourceNotFoundError:
        return None
    except Exception as e:
        print("Failed to fetch user_in_process_DB. Below is the error:\n", e)
    
    
async def delete_user_in_process(partition_key):
    entities = await get_user_in_process_data(partition_key)
    length = len(entities)
    try:
        entities = []
        for i in range(length):
            entity = {
                "PartitionKey" : partition_key,
                "RowKey" : str(i)
            }
            entities.append(("delete", entity))
            if i+1 == 100 or i == length-1:
                operations: List[TransactionOperationType] = entities
                try:
                    await users_in_process_table.submit_transaction(operations)
                    entities = []
                except TableTransactionError as e:
                    print(f"Failed to delete user in process data for {partition_key}. Below is the error:\n\n{e}")
        print(f"Deleted user in process data for {partition_key} successfully")
        return json.dumps({"status" : "success", "data" : f"Deleted user in process[{partition_key}] successfully"})
    except:
        return json.dumps({"status" : "failure", "data" : f"failed to delete user in process[{partition_key}]"})
    
    
async def update_user_in_process_data(user_id, contents):
    length = len(contents)-1
    entities = []
    for i, content in enumerate(contents):
        entity = {
            "PartitionKey" : user_id,
            "RowKey" : str(i),
            "data" : content
        }
        entities.append(("update_replace", entity))
        if (i+1) % 100 == 0 or i == length:
            operations: List[TransactionOperationType] = entities
            try:
                await users_in_process_table.submit_transaction(operations)
                entities = []
                
            except TableTransactionError as e:
                print(f"Failed to update user in process data for {user_id}. Below is the error:\n\n{e}")
    print(f"Updated user in process data for {user_id} successfully")
        
        
   
    
'''async def update_stock(items, ignore_order):
    print(items)
    if ignore_order == True:
        result = json.dumps({"status" : "success", "data" : "It's a TEST number. I won't update the stock."})
        print(result)
        return result
    else:
        entities = []
        for item in items:
            partition_key = 'items'
            row_key = item['TANGLISH_NAME']
            entity = await get_entity(partition_key, row_key)
            updated_quantity = entity['JSON_QUANTITY'] - item['USER_PROVIDED_QUANTITY']
            entity['JSON_QUANTITY'] = updated_quantity
            entities.append(("update", entity, {"mode": "replace"}))
            
        operations: List[TransactionOperationType] = entities
        try:
            await items_table.submit_transaction(operations)
            result = json.dumps({"status" : "success", "data" : "Updated the stock successfully."})
            print(result)
            return result
        except TableTransactionError as e:
            result = json.dumps({"status" : "failure", "data" : f"Failed to update the stock. See the error below:\n\n{e}"})
            print(result)
            return result'''
        
    
async def del_and_create_table():
    async for entity in items_table.list_entities():
        await items_table.delete_entity(row_key = entity['RowKey'], partition_key = entity['PartitionKey'])
    print("Items entities deleted")
    '''global items_table
    async with TableServiceClient.from_connection_string(CONNECTION_STRING) as table_service_client:
        try:
            table_deleted = await table_service_client.delete_table(table_name = "items")
            print(f"Deleted items table")
        except Exception as e:
            print(f"Failed to delete items table. See the error below:")
            print(e)
            
        while True:
            tables = [t.name async for t in table_service_client.list_tables()]
            if "items" not in tables:
                break
            print("Waiting for table to be deleted...")
            await asyncio.sleep(2)  
            
        try:
            await table_service_client.create_table(table_name = "items")
            print(f"Created table items successfully!")
        except ResourceExistsError:
            print("Table already exists")
    items_table = TableClient.from_connection_string(CONNECTION_STRING, table_name = "items")'''
            
            
async def create_entities(df):
    await del_and_create_table()
    records = df.to_dict(orient = "records")
    print("RECORDS:\n\n",records[0])
    length = len(records)-1
    entities = []
    for i, record in enumerate(records):
        '''entity = {
            "PartitionKey": "items",            
            "RowKey": record['TANGLISH_NAME'],         
            **record                             
        }'''
        record["PartitionKey"] =  "items"
        record["RowKey"] = record['TANGLISH_NAME']
        entities.append(("create", record))
        if (i+1) % 100 == 0 or i == length:
            operations: List[TransactionOperationType] = entities
            try:
                await items_table.submit_transaction(operations)
                print("Uploaded batch")
                entities = []
                
            except TableTransactionError as e:
                print("Failed to upload stock db. Below is the error:")
                print(f"Error: {e}")
    print("Uploaded stock db successfully")




if __name__ == "__main__":
    asyncio.run(delete_user_in_process("ajay"))




'''async def create_entities():
    with open('data/items_processed.csv', mode='r', newline='', encoding='utf-8-sig') as csvfile:
        reader = list(csv.DictReader(csvfile))
        entities = []
        for i, row in enumerate(reader):
            entity = {
                'PartitionKey': 'items',
                'RowKey': row['TANGLISH_NAME'].strip(),
                'TANGLISH_NAME' : row['TANGLISH_NAME'].strip(),
                'TAMIL_NAME': row['TAMIL_NAME'].strip(),
                'JSON_QUANTITY': float(row['JSON_QUANTITY']),
                'JSON_QUANTITY_TYPE': row['JSON_QUANTITY_TYPE'].strip(),
                'SELLING_PRICE': float(row['SELLING_PRICE']),
                'CATEGORY': row['CATEGORY'].strip()
            }
            entities.append(("create", entity))
            if len(entities) == 100 or i == len(reader)-1:
                operations: List[TransactionOperationType] = entities
                try:
                    await items_table.submit_transaction(operations)
                    print("Uploaded batch")
                    entities = []
                    if i == len(reader)-1:
                        print("Last item added")
                        break
                    
                except TableTransactionError as e:
                    print("There was an error with the transaction operation")
                    print(f"Error: {e}")
asyncio.run(create_entities())'''
                    
                    
                    
'''from google import genai
from google.genai import types
import config
import pandas as pd
gemini = genai.Client()







async def generate_tamil_names(tanglish_names: list):
    contents = json.dumps({"items" : tanglish_names.to_list()}, ensure_ascii = False)
    print(str(tanglish_names.to_list()))
    print("generating tamil names...")
    response = await gemini.aio.models.generate_content(
        model = config.ttt.model,
        contents = contents,
        config = config.ttt.config_2,
    )
    response = response.text
    response = json.loads(response)
    return response['items']

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

async def main():
    with open("data/items.json", "r") as f:
        obj = json.load(f)
        tamil_names = obj['items']
    df = pd.read_csv("data/items.csv")
    df = await remove_whitespaces(df)
    df = await convert_quantity_type_into_float(df)
    df['TANGLISH_NAME'] = [name.upper() for name in df['TANGLISH_NAME']]
    df['TAMIL_NAME'] = tamil_names
    df.to_csv("data/items_processed.csv", index = False, encoding = "utf-8-sig")
        
asyncio.run(main())'''