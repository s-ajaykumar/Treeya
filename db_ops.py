from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceNotFoundError
import time
import json
from dotenv import load_dotenv
import os
#import csv

load_dotenv()

CONNECTION_STRING = os.environ["AZURE_TABLE_STORAGE_CONNECTION_STRING"]
table_service_client = TableServiceClient.from_connection_string(conn_str = CONNECTION_STRING)

items_table = table_service_client.get_table_client(table_name = "items")
users_in_process_table = table_service_client.get_table_client(table_name = "usersInProcess")


    
def get_items():
    items = list(items_table.list_entities())
    return items

def get_user_in_process_data(partition_key, row_key = "conversation"):
    try:
        entity = users_in_process_table.get_entity(partition_key = partition_key, row_key = row_key)
        return json.loads(entity['data'])['conversations']  # -> List of conversations
    except ResourceNotFoundError:
        return None
    
def delete_user_in_process(partition_key, row_key = "conversation"):
    try:
        users_in_process_table.delete_entity(row_key = row_key, partition_key = partition_key)
        return json.dumps({"status" : "success", "data" : f"Deleted user in process[{partition_key}] successfully"})
    except:
        return json.dumps({"status" : "success", "data" : f"failed to delete user in process[{partition_key}]"})
    
def update_user_in_process_data(partition_key, data):
    pass
    
def create_conversations(user_id, conversations):
    row_key = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    partition_key = user_id
























'''
# CREATE entities
with open('data/items_version2.csv', mode='r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for i, row in enumerate(reader):
        my_entity = {
            'PartitionKey': row['TANGLISH NAME'].strip()[:2],
            'RowKey': str(i),
            'TANGLISH_NAME' : row['TANGLISH NAME'].strip(),
            'TAMIL_NAME': row['TAMIL NAME'].strip(),
            'QUANTITY': int(row['QUANTITY']),
            'SELLING_PRICE': int(row['SELLING PRICE']),
            'QUANTITY_TYPE': row['QUANTITY TYPE'].strip(),
            'CATEGORY': row['CATEGORY'].strip()
        }
        entity = table_client.create_entity(entity = my_entity)
        print(i)'''






