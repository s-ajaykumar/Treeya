import config

import json
from datetime import datetime
import logging
import os
from dotenv import load_dotenv



import uvicorn
import soundfile as sf
from fastapi import Form
from typing import Optional
from urllib.request import urlretrieve
from fastapi import FastAPI, File, UploadFile


from google import genai
from google.genai import types
from sarvamai import SarvamAI

load_dotenv()

app = FastAPI()
gemini = genai.Client()
stt_client = SarvamAI(api_subscription_key = os.environ['SARVAM_AI_API'])

logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)





class STOCK_OPS:
    def __init__(self):
        self.stock_db = self.get_stock_db()
    
    def update(self, response):
        items_list = response['data']
        for item in items_list:
            item_id = item['TANGLISH NAME']
            json_item = self.get_item(item_id)
            json_item['QUANTITY'] = json_item['QUANTITY'] - item["QUANTITY"]
            self.update_item(item_id, json_item)
        self.update_db()
    
    def get_item(self, item_id):
        return self.stock_db[item_id]
    
    def update_item(self, item_id, json_item):
        self.stock_db[item_id] = json_item
        
    def update_db(self):
        with open("data/items_version2.json", "w", encoding = "utf-8") as f:
            json.dump(self.stock_db, f, indent = 4, ensure_ascii = False)
    
    def get_stock_db(self):
        stock_db = open("data/items_version2.json", "r").read()
        return stock_db



class TREEYA:
    def __init__(self):
        self.user_id = None
        self.is_user_in_process = None
        self.users_in_process_database = None
        self.items_database = self.get_items_database()
        
        
    def delete_order(self, user_id):
        del self.users_in_process_database[user_id]
        with open("data/users_in_process.json", "w", encoding = "utf-8") as f:
            json.dump(self.users_in_process_database, f, indent = 4)
        
    def convert_ogg_to_wav(self, ogg_file_path):
        data, sr = sf.read(ogg_file_path) 
        wav_file_path = ogg_file_path[:-4] + ".wav" 
        sf.write(wav_file_path, data, sr)      
        os.remove(ogg_file_path)
        return wav_file_path  
    
    def frame_query(self, contents):
        response = gemini.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_2,
        )
        return response.text
    
    def get_items_database(self):
        items_database = open("data/items_version2_progress.json", "r").read()
        items_database = types.Content(role = "model", parts = [types.Part.from_text(text = items_database)])
        '''items_database = open("data/items_progress.json", "rb").read()
        items_database = types.Content(role = "model", parts = [types.Part.from_bytes(mime_type = "application/json", data = items_database)])'''
        return items_database
    
    def get_users_in_process_database(self, ):
        with open("data/users_in_process.json", "r", encoding = "utf-8") as f:
            users_in_process_database = json.load(f)
        return users_in_process_database
        
    def save_conversation(self, query, response, prev_conv):
        res_obj = json.loads(response)
        conversation = [{"role" : "user", "data" : query}, {"role" : "model", "data" : response}]
        
        # Update stock
        if res_obj['status'] == "success":
            stock_ops.update(res_obj)
            
        if self.is_user_in_process:
            if res_obj['status'] == 'success':
                conversation = [conversation[1]]
            elif res_obj['status'] != 'success':
                conversation = prev_conv + conversation
        
        self.users_in_process_database[self.user_id] = conversation
        with open("data/users_in_process.json", "w", encoding = "utf-8") as f:
            json.dump(self.users_in_process_database, f, indent = 4, ensure_ascii = False)
            
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
        '''with open(file_path, "rb") as audio:
            response = stt_client.speech_to_text.translate(
                file = audio,
                model = "saaras:v2.5"
            )
        return response.transcript'''
        response = stt_client.speech_to_text.transcribe(
            file=open(file_path, "rb"),
            model="saarika:v2.5",
            language_code="ta-IN"
        )
        return response.transcript
            
    def TTT(self, contents):
        contents = [self.items_database] + contents
        
        response = gemini.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_1,
        )
        logger.info(f"model: {response.text}")
        '''response = json.loads(response.text)
        if response['status'] == 'success':
            response = json.dumps({"status" : response["status"], "data" : response["data"], "total_sum" : response['total_sum']}, ensure_ascii = False)
        else:
            response = json.dumps({"status" : response["status"], "data" : response["data"]}, ensure_ascii = False)'''
        return response.text
            
            
    async def main(self, audio_link, text, items_database_link, order_status, user_id):
        
        if order_status == "confirm" or order_status == "cancel":
            self.delete_order(user_id)
            return json.dumps({"data" : "success"})
        
        self.user_id = user_id
        self.users_in_process_database = self.get_users_in_process_database()
        self.is_user_in_process = user_id in self.users_in_process_database
        
        if items_database_link:
            urlretrieve(items_database_link, "data/items.xlsx")
            #convert_from_file("student.xls")
            
        if audio_link:                       
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3] 
            ogg_file_path = f"data/outputs/{timestamp}.ogg"
            urlretrieve(audio_link, ogg_file_path)
            wav_file_path = self.convert_ogg_to_wav(ogg_file_path)
            text = self.STT(wav_file_path)

        query = text
    
        if self.is_user_in_process:
            prev_conv = self.users_in_process_database[self.user_id]
            contents = self.add_previous_conversation(query, prev_conv)
        else:
            prev_conv = None
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = query)])]
            
        '''framed_query = self.frame_query(contents)
        print("framed query: ", framed_query)
        contents[-1] = types.Content(role = "user", parts = [types.Part.from_text(text = framed_query)])
            
        TTT_response = self.TTT(contents)
        self.save_conversation(framed_query, TTT_response, prev_conv)'''
        TTT_response = self.TTT(contents)
        self.save_conversation(query, TTT_response, prev_conv)
        
        logger.info(f"user: {query}") 
        logger.info(f"model: {TTT_response}") 
    
        return TTT_response
    
    
    
treeya = TREEYA()
stock_ops = STOCK_OPS()



@app.post("/upload-audio/") 
async def process_data(
                 audio_link: Optional[str] = Form(None),
                 text: Optional[str] = Form(None),
                 items_database_link: Optional[str] = Form(None),
                 order_status: Optional[str] = Form(None),
                 user_id: str = Form(...)
                 ):
     return await treeya.main(audio_link, text, items_database_link, order_status, user_id)
    
  
if __name__ == '__main__':
    uvicorn.run("main_version2_progress:app", host = "localhost", port = 8000, reload = True)









