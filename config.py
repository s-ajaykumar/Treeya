import data.prompt as prompt 
from dataclasses import dataclass
from google.genai import types




@dataclass
class TTT:
    model = "gemini-2.5-flash"
    
    main_prompt =  prompt.main_version2_progress2
    search_stock_prompt = prompt.search_stock
    translate_item_names = prompt.translate_item_names
    
    config_1 = types.GenerateContentConfig(
        temperature = 1,
        thinking_config = types.ThinkingConfig(thinking_budget = 0),
        response_mime_type = "application/json",
        system_instruction = [types.Part.from_text(text = main_prompt)]
    )
    config_2 = types.GenerateContentConfig(
        temperature = 1,
        thinking_config = types.ThinkingConfig(thinking_budget = 0),
        response_mime_type = "application/json",
        system_instruction = [types.Part.from_text(text = search_stock_prompt)]
    )
    config_3 = types.GenerateContentConfig(
        temperature = 1,
        thinking_config = types.ThinkingConfig(thinking_budget = 0),
        response_mime_type = "application/json",
        system_instruction = [types.Part.from_text(text = translate_item_names)]
    )
    
    
    
ttt = TTT()