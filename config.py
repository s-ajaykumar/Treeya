import data.prompt as prompt 
from dataclasses import dataclass
from google.genai import types




@dataclass
class TTT:
    model = "gemini-2.5-flash"
    
    main_prompt =  prompt.main_version2
    translate_prompt = prompt.translate_item_names
    #frame_query_prompt = prompt.frame_query
    #translate_prompt = prompt.translate
    
    config_1 = types.GenerateContentConfig(
        temperature = 0,
        thinking_config = types.ThinkingConfig(thinking_budget = -1),
        response_mime_type = "application/json",
        system_instruction = [types.Part.from_text(text = main_prompt)]
    )
    config_2 = types.GenerateContentConfig(
        temperature = 0,
        thinking_config = types.ThinkingConfig(thinking_budget = 0),
        response_mime_type = "application/json",
        system_instruction = [types.Part.from_text(text = translate_prompt)]
    )
    
    '''config_2 = types.GenerateContentConfig(
        temperature = 0,
        thinking_config = types.ThinkingConfig(thinking_budget = 0),
        response_mime_type = "text/plain",
        system_instruction = [types.Part.from_text(text = frame_query_prompt)]
    )'''
    
    '''config_3 = types.GenerateContentConfig(
        temperature = 0,
        thinking_config = types.ThinkingConfig(thinking_budget = 0),
        response_mime_type = "text/plain",
        system_instruction = [types.Part.from_text(text = translate_prompt)]
    )'''
    
    
    
ttt = TTT()