from typing import Optional
from pydantic import BaseModel



class user_request(BaseModel):
    user_id: str
    audio_link: Optional[str] = None
    text: Optional[str] = None
    
class delete_user_in_process(BaseModel):
    user_id: str
    
class update_stock(BaseModel):
    items: list
    
class upload_stock_db(BaseModel):
    items_database_link: str