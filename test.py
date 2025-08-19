import json
import csv
import aiohttp
import asyncio
import soundfile as sf

def csv_to_json():
    data = {}
    with open('data/items_version2.csv', mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row["QUANTITY"] = int(row['QUANTITY']) 
            row['SELLING PRICE'] = int(row['SELLING PRICE']) 
            key = row['TANGLISH NAME']
            del row['TANGLISH NAME']
            data[key] = row

    with open('data/items_version2_progress.json', mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4, ensure_ascii = False)
        
#csv_to_json()






'''
audio_link = ""
ogg_file_path = "audio.ogg"
async def main(audio_link, ogg_file_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(audio_link) as response:
            data = await response.content.read()
            with open(ogg_file_path, mode = "wb") as f:
                f.write(data)
    data, sr = sf.read(ogg_file_path) 
    wav_file_path = ogg_file_path[:-4] + ".wav" 
    sf.write(wav_file_path, data, sr) 
                
if __name__ == "__main__":
    asyncio.run(main(audio_link, ogg_file_path))'''
                
