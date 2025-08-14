'''
item names are feeded in "Tanglish" and "Pure English" to the AI.
'''


import data.config as config

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
#from excel2json import convert_from_file


from google import genai
from google.genai import types
from sarvamai import SarvamAI

load_dotenv()

app = FastAPI()
gemini = genai.Client()
stt_client = SarvamAI(api_subscription_key = os.environ['SARVAM_AI_API'])

logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)


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
    
    def frame_query(self, text):
        response = gemini.models.generate_content(
            model = config.ttt.model,
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = text)])],
            config = config.ttt.config_2,
        )
        return response.text
    
    def get_items_database(self):
        items_database = open("data/items_version1.json", "r").read()
        items_database = types.Content(role = "model", parts = [types.Part.from_text(text = items_database)])
        return items_database
    
    def get_users_in_process_database(self, ):
        with open("data/users_in_process.json", "r", encoding = "utf-8") as f:
            users_in_process_database = json.load(f)
        return users_in_process_database
        
    def save_in_process_conversation(self, query, response, prev_conv):
        conversation = [{"role" : "user", "data" : query}, {"role" : "model", "data" : response}]
        
        if self.is_user_in_process:
            conversation = prev_conv + conversation
        self.users_in_process_database[self.user_id] = conversation
        
        with open("data/users_in_process.json", "w", encoding = "utf-8") as f:
            json.dump(self.users_in_process_database, f, indent = 4)
            
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
            print("transcript: ", text)

            
        query = text
    
        if self.is_user_in_process:
            prev_conv = self.users_in_process_database[self.user_id]
            contents = self.add_previous_conversation(query, prev_conv)
        else:
            prev_conv = None
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = query)])]
            
        '''framed_query = self.frame_query(text)
        print("framed query: ", framed_query)
        contents[-1] = types.Content(role = "user", parts = [types.Part.from_text(text = framed_query)])
            
        TTT_response = self.TTT(contents)
        self.save_in_process_conversation(framed_query, TTT_response, prev_conv)
        
        logger.info(f"user: {framed_query}") 
        logger.info(f"model: {TTT_response}")'''
            
        TTT_response = self.TTT(contents)
        self.save_in_process_conversation(query, TTT_response, prev_conv)
        
        logger.info(f"user: {query}") 
        logger.info(f"model: {TTT_response}")
    
        return TTT_response
    
    
    
treeya = TREEYA()

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
    uvicorn.run("main_version1:app", host = "localhost", port = 8000, reload = False)
