import data.prompt as prompt 
from dataclasses import dataclass
from google.genai import types




@dataclass
class TTT:
    model = "gemini-2.5-flash"
    
    main_prompt =  prompt.main_version2_progress
    search_stock_prompt = prompt.search_stock
    remove_out_of_stock_prompt = prompt.remove_out_of_stock
    #translate_item_names = prompt.translate_item_names
    
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
        system_instruction = [types.Part.from_text(text = search_stock_prompt)]
    )
    config_3 = types.GenerateContentConfig(
        temperature = 0,
        thinking_config = types.ThinkingConfig(thinking_budget = 0),
        response_mime_type = "application/json",
        system_instruction = [types.Part.from_text(text = remove_out_of_stock_prompt)]
    )
    
    
    
ttt = TTT()