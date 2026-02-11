from utils.api import API
from utils.hwid import get_hwid

class AuthUtil:
    def __init__(self, api: API):
        self.api: API = api
    
    def check_token_is_valid(self) -> bool:
        status_code, resp = self.api.get_me(get_hwid())
        
        if status_code == 200:
            return True
        else:
            return False