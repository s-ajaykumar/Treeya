import config
import db_ops

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


class TREEYA:
        
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
        items_database = db_ops.get_items()
        items_database = str(items_database)
        '''items_database = open("data/items_version2.json", "r").read()'''
        items_database = types.Content(role = "model", parts = [types.Part.from_text(text = items_database)])
        
        return items_database
        
    def save_conversation(self, user_id, query, response, prev_conv):
        '''res_obj = json.loads(response)
        if res_obj['status'] == "success":
            response = json.dumps({"data" : res_obj['data'], "total_sum" : res_obj['total_sum'], "status" : res_obj['status']}, ensure_ascii = False)
        else:
            response = json.dumps({"data" : res_obj['data'], "status" : res_obj['status']}, ensure_ascii = False)'''
            
        conversation = [{"role" : "user", "data" : query}, {"role" : "model", "data" : response}]
        
        if prev_conv:
            '''if res_obj['status'] == 'success':
                conversation = [conversation[1]]
            elif res_obj['status'] != 'success':'''
            conversation = prev_conv + conversation
            
        conversation = json.dumps({"conversations" : conversation}, encode_ascii = False)
        db_ops.update_user_in_process_data(partition_key = user_id, data = conversation)
            
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
            
    def TTT(self, contents, items_database):
        contents = [items_database] + contents
        
        response = gemini.models.generate_content(
            model = config.ttt.model,
            contents = contents,
            config = config.ttt.config_1,
        )
        '''response = json.loads(response.text)
        if response['status'] == 'success':
            response = json.dumps({"status" : response["status"], "data" : response["data"], "total_sum" : response['total_sum']}, ensure_ascii = False)
        else:
            response = json.dumps({"status" : response["status"], "data" : response["data"]}, ensure_ascii = False)'''
        logger.info(f"model: {response.text}") 
        return response.text
            
            
    async def main(self, audio_link, text, items_database_link, order_status, user_id):
        user_in_process_data = db_ops.get_user_in_process_data(partition_key = user_id)

        if order_status == "confirm" or order_status == "cancel":
            result = db_ops.delete_user_in_process(partition_key = user_id)
            return result

        try:
            items_database = self.get_items_database()
            logger.info("Queried Items database successfully")
        except:
            logger.info("Querying Items database failed")
            
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
    
        if user_in_process_data:
            contents = self.add_previous_conversation(query, user_in_process_data)
        else:
            contents = [types.Content(role = "user", parts = [types.Part.from_text(text = query)])]
            
        '''framed_query = self.frame_query(contents)
        print("framed query: ", framed_query)
        contents[-1] = types.Content(role = "user", parts = [types.Part.from_text(text = framed_query)])
            
        TTT_response = self.TTT(contents)
        self.save_conversation(framed_query, TTT_response, prev_conv)'''
        TTT_response = self.TTT(contents, items_database)
        self.save_conversation(user_id, query, TTT_response, user_in_process_data)
        
        logger.info(f"user: {query}") 
        #logger.info(f"model: {TTT_response}") 
    
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
    uvicorn.run("main_version2_concurrent:app", host = "localhost", port = 8000, reload = True)