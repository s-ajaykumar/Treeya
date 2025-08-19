from azure.data.tables.aio import TableClient

from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import UpdateMode

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



async def get_entity(partition_key, row_key):
    return await items_table.get_entity(partition_key = partition_key, row_key = row_key)
    
    
async def get_stock_db():
    items = []
    queried_entities = items_table.query_entities(query_filter = "", select=["TAMIL_NAME", "TANGLISH_NAME", "QUANTITY", "QUANTITY_TYPE", "SELLING_PRICE", "CATEGORY"])
    async for entity in queried_entities:
        items.append(entity)
    return items


async def get_user_in_process_data(partition_key, row_key = "conversations"):
    try:
        entity = await users_in_process_table.get_entity(partition_key = partition_key, row_key = row_key)
        return json.loads(entity['conversations'])  # -> List of conversations
    except ResourceNotFoundError:
        return None
    
    
async def delete_user_in_process(partition_key, row_key = "conversations"):
    try:
        await users_in_process_table.delete_entity(row_key = row_key, partition_key = partition_key)
        return json.dumps({"status" : "success", "data" : f"Deleted user in process[{partition_key}] successfully"})
    except:
        return json.dumps({"status" : "failure", "data" : f"failed to delete user in process[{partition_key}]"})
    
    
async def update_user_in_process_data(partition_key, conversations):
    entity = {
            'PartitionKey': partition_key,
            'RowKey': 'conversations',
            'conversations' : conversations
            }
    try:
        await users_in_process_table.upsert_entity(mode = UpdateMode.REPLACE, entity = entity)
        return f"Updated user in process data for {partition_key} successfully"
    except Exception as e:
        return f"Failed to update user in process data for {partition_key}. Below is the error:\n\n{e}"
    
    
async def create_conversations(user_id, conversations):
    row_key = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    partition_key = user_id
   
    
async def update_stock(items):
    try:
        for item in items:
            partition_key = item['TANGLISH_NAME']
            row_key = 'item'
            entity = await get_entity(partition_key, row_key)
            updated_quantity = entity['QUANTITY'] - item['QUANTITY']
            entity['QUANTITY'] = updated_quantity
            await items_table.update_entity(mode = UpdateMode.REPLACE, entity = entity)
        result = json.dumps({"status" : "success", "data" : "Updated the stock successfully."})
        print(result)
        return result
    except Exception as e:
        result = json.dumps({"status" : "failure", "data" : f"Failed to update the stock. See the error below:\n\n{e}"})
        print(result)
        return result
        
    
async def upload_stock_db(link):
    pass




if __name__ == "__main__":
    asyncio.run(get_stock_db())














'''# CREATE entities
async def create_entities():
    with open('items.csv', mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        i = 1
        for row in reader:
            entity = {
                'PartitionKey': row['TANGLISH_NAME'].strip(),
                'RowKey': 'item',
                'TANGLISH_NAME' : row['TANGLISH_NAME'].strip(),
                'TAMIL_NAME': row['TAMIL_NAME'].strip(),
                'QUANTITY': float(row['QUANTITY']),
                'SELLING_PRICE': float(row['SELLING_PRICE']),
                'QUANTITY_TYPE': row['QUANTITY_TYPE'].strip(),
                'CATEGORY': row['CATEGORY'].strip()
            }
            await items_table.create_entity(entity = entity)
            print(i)
            i += 1
        
if __name__ == "__main__":
    asyncio.run(create_entities())'''






