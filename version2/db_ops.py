from azure.data.tables.aio import TableClient

from azure.core.exceptions import ResourceNotFoundError

from typing import Any, List, Mapping, Tuple, Union
from azure.data.tables import TableEntity, TransactionOperation
from azure.data.tables import TableTransactionError

EntityType = Union[TableEntity, Mapping[str, Any]]
OperationType = Union[TransactionOperation, str]
TransactionOperationType = Union[Tuple[OperationType, EntityType], Tuple[OperationType, EntityType, Mapping[str, Any]]]

import json
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

load_dotenv()

CONNECTION_STRING = os.environ["AZURE_TABLE_STORAGE_CONNECTION_STRING"]
items_table = TableClient.from_connection_string(CONNECTION_STRING, table_name = "items")
users_in_process_table = TableClient.from_connection_string(CONNECTION_STRING, table_name = "usersInProcess")
    
    
async def get_items(item_codes, partition_key = "items"):
    items = []
    try:
        for item_code in item_codes:
            entity = await items_table.get_entity(partition_key = partition_key, row_key = item_code, select = ["RowKey", "TAMIL_NAME", "TANGLISH_NAME", "JSON_QUANTITY", "JSON_QUANTITY_TYPE", "SELLING_PRICE", "CATEGORY"])
            items.append(entity)
        return items
    except Exception as e:
        print("Failed to fetch items from Azure Table Storage. Below is the error:\n", e)


async def get_user_in_process_data(partition_key):
    try:
        filter_query = f"PartitionKey eq '{partition_key}'"
        entities = []
        async for entity in users_in_process_table.query_entities(
            query_filter = filter_query
        ):
            entities.append(entity['data']) 
        entities_length = len(entities)
        return entities, entities_length
    except ResourceNotFoundError:
        return None, None
    except Exception as e:
        print("Failed to fetch user_in_process_DB. Below is the error:\n", e)
    
    
async def get_user_in_process_row_keys(partition_key):
    try:
        filter_query = f"PartitionKey eq '{partition_key}'"
        row_keys = []
        async for entity in users_in_process_table.query_entities(
            query_filter = filter_query
        ):
            row_keys.append(entity['RowKey'])   
        return row_keys
    except Exception as e:
        print("Failed to get_user_in_process_row_keys. Below is the error:\n", e)
        
async def delete_user_in_process(partition_key):
    row_keys = await get_user_in_process_row_keys(partition_key)
    try:
        entities = []
        for row_key in row_keys:
            entity = {
                "PartitionKey" : partition_key,
                "RowKey" : row_key
            }
            entities.append(("delete", entity))
        entity_ls = [entities[i:i+100] for i in range(0, len(entities), 100)]
        
        for entity_sub_ls in entity_ls:
            operations: List[TransactionOperationType] = entity_sub_ls
            try:
                await users_in_process_table.submit_transaction(operations)
            except TableTransactionError as e:
                print(f"Failed to delete user in process data for {partition_key}. Below is the error:\n\n{e}")
        print(f"Deleted user in process data for {partition_key} successfully")
        return json.dumps({"status" : "success", "data" : f"Deleted user in process[{partition_key}] successfully"})
    except:
        return json.dumps({"status" : "failure", "data" : f"failed to delete user in process[{partition_key}]"})
    
    
async def update_user_in_process_data(user_id, contents, entities_length):
    entities = []
    contents = contents[entities_length:] # Ignore previous contents
    for i, content in enumerate(contents):
        entity = {
            "PartitionKey" : user_id,
            "RowKey" : datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + f"-{i:03d}",
            "data" : content
        }
        entities.append(("create", entity))
        
    entity_ls = [entities[i:i+100] for i in range(0, len(entities), 100)]
    for entity_sub_ls in entity_ls:
        operations: List[TransactionOperationType] = entity_sub_ls
        try:
            await users_in_process_table.submit_transaction(operations)  
        except TableTransactionError as e:
            print(f"Failed to update user in process data for {user_id}. Below is the error:\n\n{e}")
    print(f"Updated user in process data for {user_id} successfully")
        
        
   
  
class UPLOAD_STOCK():
    async def delete_items(self, to_delete_item_codes, partition_key = "items"):
        entities = []
        for j, item_code in enumerate(to_delete_item_codes):
            entity = {
                "PartitionKey" : partition_key,
                "RowKey" : item_code
            }
            entities.append(("delete", entity))
        entities = [entities[i:i+100] for i in range(0, len(entities), 100)]
        try:
            for entity_ls in entities:
                operations: List[TransactionOperationType] = entity_ls
                await items_table.submit_transaction(operations)
            print(f"Deleted items: {str(to_delete_item_codes)} in items table successfully")
        except TableTransactionError as e:
            print(f"Failed to delete items: {str(to_delete_item_codes)} in items table. Below is the error:\n\n{e}")
    
       
    async def insert_items(self, insert_input, partition_key = "items"):
        to_insert_items = insert_input['to_insert_items']
        tamil_names = insert_input['tamil_names']
        
        TANGLISH_NAME = "ITEM NAME"
        CATEGORY = "GROUP NAME"	
        JSON_QUANTITY_TYPE = "UNIT NAME"
        JSON_QUANTITY = "STOCKS"
        SELLING_PRICE = "PRICE"
        
        entities = []
        for i, item in enumerate(to_insert_items):
            entity = {
                "PartitionKey"      : partition_key,
                "RowKey"            : item['ITEM CODE'],
                "TANGLISH_NAME"     : item[TANGLISH_NAME].upper().strip(),
                "TAMIL_NAME"        : tamil_names[i].strip(),
                "JSON_QUANTITY"     : item[JSON_QUANTITY],
                "JSON_QUANTITY_TYPE": item[JSON_QUANTITY_TYPE].strip(),
                "SELLING_PRICE"     : item[SELLING_PRICE],
                "CATEGORY"          : item[CATEGORY].strip(),
            }
            entities.append(("create", entity))
        entities = [entities[i:i+100] for i in range(0, len(entities), 100)]
        try:
            for entity_ls in entities:
                operations: List[TransactionOperationType] = entity_ls
                await items_table.submit_transaction(operations)
            print(f"Created items in items table successfully")
        except TableTransactionError as e:
            print(f"Failed to create items in items table. Below is the error:\n\n{e}")
            
    
    async def update_items(self, update_input, update_codes, partition_key = "items"):
        TANGLISH_NAME = "ITEM NAME"
        TAMIL_NAME = "TAMIL_NAME"
        CATEGORY = "GROUP NAME"	
        JSON_QUANTITY_TYPE = "UNIT NAME"
        JSON_QUANTITY = "STOCKS"
        SELLING_PRICE = "PRICE"
        try:
            entities = items_table.query_entities(
                query_filter=f"PartitionKey eq '{partition_key}'",
                select=["RowKey", "TAMIL_NAME"]
            )
            tamil_names_dic = {}
            async for e in entities:
                if e["RowKey"] in update_codes:
                    tamil_names_dic[e["RowKey"]] = e["TAMIL_NAME"]
        except Exception as e:
            print("Failed to update items in items table. Below is the error:\n\n", e)
            
        entities = []
        for i, item in enumerate(update_input):
            entity = {
                "PartitionKey"      : partition_key,
                "RowKey"            : item['ITEM CODE'],
                "TANGLISH_NAME"     : item[TANGLISH_NAME].upper().strip(),
                "TAMIL_NAME"        : tamil_names_dic[item['ITEM CODE']],
                "JSON_QUANTITY"     : item[JSON_QUANTITY],
                "JSON_QUANTITY_TYPE": item[JSON_QUANTITY_TYPE].strip(),
                "SELLING_PRICE"     : item[SELLING_PRICE],
                "CATEGORY"          : item[CATEGORY].strip(),
            }
            entities.append(("update", entity))
        entities = [entities[i:i+100] for i in range(0, len(entities), 100)]
        operations: List[TransactionOperationType] = entities
        try:
            for entity_ls in entities:
                operations: List[TransactionOperationType] = entity_ls
                await items_table.submit_transaction(operations)
            print(f"Updated items in items table successfully")
        except TableTransactionError as e:
            print(f"Failed to update items in items table. Below is the error:\n\n{e}")
                
        
        
    async def run(self, insert_input, to_delete_item_codes, update_input, update_codes):
        if update_input:
            await self.update_items(update_input, update_codes)
        
        if insert_input:
            await self.insert_items(insert_input)
        else:
            print("No new items need to be inserted in the items table")
            
        if to_delete_item_codes:
            await self.delete_items(to_delete_item_codes)
        else:
            print("No items need to be deleted in the items table")
         
upload_stock = UPLOAD_STOCK()
   
   
    
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




'''async def generate_tamil_names(tanglish_names: list):
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