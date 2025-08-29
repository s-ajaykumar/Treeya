import config
import db_ops
import upload_stock
import RequestModel

import os
import time
import json
import copy
import aiohttp
import aiofiles
import tempfile
import soundfile as sf
from datetime import datetime
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from google import genai
from google.genai import types
from sarvamai import SarvamAI

load_dotenv()
    
    
class TREEYA:
    
    async def download_file(self, audio_link, ogg_file_path):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_link) as response:
                    data = await response.content.read()
                    async with aiofiles.open(ogg_file_path, mode = "wb") as f:
                        await f.write(data)
            print("Downloaded the user audio successfully.")
        except Exception as e:
            print(f"Failed to download the user audio. Below is the error:\n\n{e}")
        
    def convert_ogg_to_wav(self, ogg_file_path):
        data, sr = sf.read(ogg_file_path) 
        wav_file_path = ogg_file_path[:-4] + ".wav" 
        sf.write(wav_file_path, data, sr)      
        return wav_file_path  
    
    async def get_stock_db(self):
        items_database = await db_ops.get_stock_db()
        items_database = str(items_database)
        items_database = types.Content(role = "model", parts = [types.Part.from_text(text = items_database)])
        return items_database
        
        
    async def save_conversation(self, user_id, contents):
        conversation = json.dumps(contents, ensure_ascii = False)
        update_result = await db_ops.update_user_in_process_data(partition_key = user_id, conversations = conversation)
        print(update_result)
            
    def add_previous_conversation(self, query, prev_conv):
        contents = []
        query = types.Content(role = "user", parts = [types.Part.from_text(text = query)])
        
        for conv in prev_conv:
            role = conv['role'] 
            data = conv['data']
            content = types.Content(role = role, parts = [types.Part.from_text(text = data)])
            contents.append(content)
            
        contents += [query]
        return contents
       
    async def add_content(self, prev_contents, role, data):
        prev_contents = prev_contents + [{"role" : role, "data" : data}]
        return prev_contents
        
    def remove_empty_stock(self, search_stock_result):
        user_requested_items = search_stock_result["user_requested_items"]
        for j, item in enumerate(user_requested_items):
            if item['match'] == "EXACT" and not item['JSON_item']:
                item['match'] = "OUT_OF_STOCK"
            if item['match'] == "EXACT" and item['JSON_item'] and item['JSON_item'][0]['JSON_QUANTITY'] == 0:
                item['match'] = "OUT_OF_STOCK"
            if item['match'] == "MULTIPLE":
                item['JSON_item'] = [m for m in item['JSON_item'] if m['JSON_QUANTITY'] != 0]
            user_requested_items[j] = item
        return json.dumps(user_requested_items, ensure_ascii = False)
                    
        
    
    def STT(self, file_path):
        try:
            response = stt_client.speech_to_text.transcribe(
                file = open(file_path, "rb"),
                model = "saarika:v2.5",
                language_code = "ta-IN"
            )
            return response.transcript, "success"
        except Exception as e:
            print("STT failed. Below is the error:\n", e)
            return json.dumps({"type" : "failure", "data" : "Hey! Just a quick note\n\nPlease keep your *audio note* under *30 seconds* so we can move forward smoothly.\n\nThanks! 😊"}, ensure_ascii = False), "failure"
            
            
    async def search_stock(self, prev_contents, TTT_response):
        t1 = time.time()
        items_database = await self.get_stock_db()
        t2 = time.time()
        print(f"Time taken: Fetch STOCK_DB: {(t2-t1)*1000:2f} ms")
        
        contents = [items_database] + [types.Content(role = "user", parts = [types.Part.from_text(text = TTT_response)])]
        t1 = time.time()
        response = await gemini.aio.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_2,
        )
        t2 = time.time()
        print(f"Time taken: Search_Stock: {(t2-t1)*1000:2f} ms")
        response = response.text
        
        '''contents = [types.Content(role = "user", parts = [types.Part.from_text(text = response)])]
        t1 = time.time()
        response = await gemini.aio.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_3,
        )
        t2 = time.time()
        print(f"Time taken: Remove empty stock: {(t2-t1)*1000:2f} ms")
        response1 = response.text'''
        t1 = time.time()
        response1 = self.remove_empty_stock(json.loads(response))
        t2 = time.time()
        print(f"Time taken: Remove empty stock: {(t2-t1)*1000:2f} ms")
        
        contents = self.add_previous_conversation(response1, prev_contents)
        t1 = time.time()
        response2, type_ = await self.TTT(contents)
        t2 = time.time()
        print(f"Time taken: TTT: {(t2-t1)*1000:2f} ms")
        
        prev_contents = await self.add_content(prev_contents, "user", response1)
        prev_contents = await self.add_content(prev_contents, "model", response2)
        return response2, prev_contents
    
           
    async def TTT(self, contents):
        response = await gemini.aio.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_1,
        )
        response = response.text
        type_ = json.loads(response)['type']
        return response, type_
                   
       
                   
    async def main(self, user_id, audio_link, text):
        t1 = time.time()
        user_in_process_data = await db_ops.get_user_in_process_data(partition_key = user_id)
        t2 = time.time()
        print(f"Time taken: Fetch user_in_process DB: {(t2-t1)*1000:2f} ms")
            
        if audio_link:    
            with tempfile.TemporaryDirectory() as temp_dir:                 
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3] 
                ogg_file_path = os.path.join(temp_dir, f"{timestamp}.ogg")  
                await self.download_file(audio_link, ogg_file_path)
                wav_file_path = await run_in_threadpool(self.convert_ogg_to_wav, ogg_file_path)
                t1 = time.time()
                text, type_ = await run_in_threadpool(self.STT, wav_file_path)
                t2 = time.time()
                print(f"Time taken: STT: {(t2-t1)*1000:2f} ms")
                if type_ == "failure":
                    return text

        query = json.dumps(text, ensure_ascii = False)
    
        if user_in_process_data:
            contents = self.add_previous_conversation(query, user_in_process_data)
            prev_contents = copy.deepcopy(user_in_process_data)
            prev_contents = await self.add_content(prev_contents, "user", query)
        else:
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = query)])]
            prev_contents = await self.add_content([], "user", query)
            
        t1 = time.time()
        TTT_response, type_ = await self.TTT(contents)
        t2 = time.time()
        print(f"Time taken for TTT: {(t2-t1)*1000:2f} ms")
        prev_contents = await self.add_content(prev_contents, "model", TTT_response)
        
        if type_ == "search_stock":
            TTT_response, prev_contents = await self.search_stock(prev_contents, TTT_response)
        
        for c in prev_contents:
            print(c['role'])
            print(c['data'])
            
        await self.save_conversation(user_id, prev_contents)
        return TTT_response
    
  

stt_client = SarvamAI(api_subscription_key = os.environ['SARVAM_AI_API'])  
gemini = genai.Client()
treeya = TREEYA() 
app = FastAPI()    
    
    
@app.post("/user_request/") 
async def main(request: RequestModel.user_request):
    return await treeya.main(request.user_id, request.audio_link, request.text)

@app.post("/delete_user_in_process/") 
async def main(request: RequestModel.delete_user_in_process):
    return await db_ops.delete_user_in_process(partition_key = request.user_id)

'''@app.post("/update_stock/") 
async def main(request: RequestModel.update_stock):
    return await db_ops.update_stock(request.items, request.ignoreOrder)'''

@app.post("/upload_stock_db/") 
async def main(request: RequestModel.upload_stock_db):
    return await upload_stock.main(request.link)



if __name__ == '__main__':
    uvicorn.run("main:app", host = "localhost", port = 8000, reload = True)