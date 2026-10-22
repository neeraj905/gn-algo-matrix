from SmartApi import SmartConnect
import pyotp

class AngelAPIHandler:
    def __init__(self, api_key, client_id, password, totp_secret):
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret
        self.smart_api = None
        self.session_data = None
        
    def connect(self):
        try:
            self.smart_api = SmartConnect(api_key=self.api_key)
            totp = pyotp.TOTP(self.totp_secret).now()
            data = self.smart_api.generateSession(self.client_id, self.password, totp)
            
            if data and data.get('status'):
                self.session_data = data['data']
                return True, "Broker connected successfully!"
            else:
                return False, data.get('message', 'Authentication failed')
        except Exception as e:
            return False, str(e)

    def get_ltp(self, exchange, symbol, token):
        try:
            if not self.smart_api:
                return None
            response = self.smart_api.ltpData(exchange, symbol, token)
            if response and 'data' in response:
                return float(response['data']['ltp'])
        except Exception as e:
            print(f"Error fetching LTP: {e}")
        return None
                
