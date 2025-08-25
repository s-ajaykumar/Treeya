import config
import db_ops
import upload_stock
import RequestModel

import os
import time
import json
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
        
        
    async def save_conversation(self, user_id, query, response, prev_conv):
        conversation = [{"role" : "user", "data" : query}, {"role" : "model", "data" : response}]
        
        if prev_conv:
            conversation = prev_conv + conversation
            
        conversation = json.dumps(conversation, ensure_ascii = False)
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
       
        
    def STT(self, file_path):
        response = stt_client.speech_to_text.transcribe(
            file = open(file_path, "rb"),
            model = "saarika:v2.5",
            language_code = "ta-IN"
        )
        return response.transcript
            
    async def TTT(self, contents):
        response = await gemini.aio.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_1,
        )
        response = response.text
        print(f"model: {response}")
        print("-" * 50)
        return response
            
    async def search_stock(self, response, items_database):
        res_obj = json.loads(response)
        if res_obj['type'] == "search_stock":
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = response)])]
            contents = [items_database] + contents
            response = await gemini.aio.models.generate_content(
                model = config.ttt.model,
                contents = contents,
                config = config.ttt.config_2,
            )
            response = response.text
            print("SEARCH STOCK RESPONSE:\n", response)
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = response)])]
            response = await self.TTT(contents)
            return response
        else:
            return None
                   
    async def main(self, user_id, audio_link, text):
        t1 = time.time()
        user_in_process_data = await db_ops.get_user_in_process_data(partition_key = user_id)
        t2 = time.time()
        print(f"Time taken for fetching user_in_process DB: {(t2-t1)*1000:2f} ms")

        try:
            t1 = time.time()
            items_database = await self.get_stock_db()
            t2 = time.time()
            print(f"Time taken for fetching items DB: {(t2-t1)*1000:2f} ms")
        except:
            print("Querying Items database failed")
            
        if audio_link:    
            with tempfile.TemporaryDirectory() as temp_dir:                 
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3] 
                ogg_file_path = os.path.join(temp_dir, f"{timestamp}.ogg")  
                await self.download_file(audio_link, ogg_file_path)
                wav_file_path = await run_in_threadpool(self.convert_ogg_to_wav, ogg_file_path)
                text = await run_in_threadpool(self.STT, wav_file_path)

        query = text
    
        if user_in_process_data:
            contents = self.add_previous_conversation(query, user_in_process_data)
        else:
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = query)])]
            
        t1 = time.time()
        TTT_response = await self.TTT(contents)
        search_stock_result = await self.search_stock(TTT_response, items_database)
        TTT_response = TTT_response if search_stock_result is None else search_stock_result
        t2 = time.time()
        print(f"Time taken for TTT: {(t2-t1)*1000:2f} ms")
        
        await self.save_conversation(user_id, query, TTT_response, user_in_process_data)
        print(f"user: {query}") 
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

@app.post("/update_stock/") 
async def main(request: RequestModel.update_stock):
    return await db_ops.update_stock(request.items, request.ignoreOrder)

@app.post("/upload_stock_db/") 
async def main(request: RequestModel.upload_stock_db):
    return await upload_stock.main(request.link)



if __name__ == '__main__':
    uvicorn.run("mainVersion2Agent:app", host = "localhost", port = 8000, reload = True)