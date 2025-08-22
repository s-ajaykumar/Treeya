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
   
    
async def update_stock(items, ignore_order):
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
            updated_quantity = entity['QUANTITY'] - item['QUANTITY']
            entity['QUANTITY'] = updated_quantity
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
            return result
        
    
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








'''async def create_entities():
    with open('data/items.csv', mode='r', newline='', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            entities = []
            for i, row in enumerate(reader):
                entity = {
                    'PartitionKey': 'items',
                    'RowKey': row['TANGLISH_NAME'].strip(),
                    'TANGLISH_NAME' : row['TANGLISH_NAME'].strip(),
                    'TAMIL_NAME': row['TAMIL_NAME'].strip(),
                    'QUANTITY': float(row['QUANTITY']),
                    'SELLING_PRICE': float(row['SELLING_PRICE']),
                    'QUANTITY_TYPE': row['QUANTITY_TYPE'].strip(),
                    'CATEGORY': row['CATEGORY'].strip()
                }
                try:
                    await items_table.create_entity(entity = entity)
                except Exception as e:
                    print(entity['RowKey'], "---", e)
                entities.append(("create", entity))
                if len(entities) == 100 or i == len(reader)-1:
                    operations: List[TransactionOperationType] = entities
                    try:
                        await items_table.submit_transaction(operations)
                        print("Uploaded batch")
                        entities = []
                        
                    except TableTransactionError as e:
                        print("There was an error with the transaction operation")
                        print(f"Error: {e}")
asyncio.run(create_entities())'''
                    