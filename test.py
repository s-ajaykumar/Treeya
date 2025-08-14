import json
import csv

def csv_to_json():
    data = {}
    with open('data/items_version2_progress.csv', mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row["QUANTITY"] = int(row['QUANTITY']) 
            row['SELLING PRICE'] = int(row['SELLING PRICE']) 
            key = row['TANGLISH NAME']
            del row['TANGLISH NAME']
            data[key] = row

    with open('data/items_version2_progress.json', mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4, ensure_ascii = False)
        
csv_to_json()
