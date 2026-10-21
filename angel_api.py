from SmartApi import SmartConnect
import pyotp

class AngelOneConnector:
    def __init__(self, api_key, client_id, password, totp_token):
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_token = totp_token
        self.smart_api = SmartConnect(api_key=self.api_key)
        self.auth_token = None

    def login(self):
        try:
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_token).now()
            # Login request
            data = self.smart_api.generateSession(self.client_id, self.password, totp)
            if data and data.get('status'):
                self.auth_token = data['data']['jwtToken']
                return True, "Login Successful!"
            else:
                return False, data.get('message', 'Login Failed')
        except Exception as e:
            return False, str(e)

    def get_ltp(self, exchange, tradingsymbol, symboltoken):
        try:
            # Fetching Last Traded Price from Angel One SmartAPI
            response = self.smart_api.ltpData(exchange, tradingsymbol, symboltoken)
            if response and 'data' in response:
                # Handle different response structures from Angel One API
                if isinstance(response['data'], dict):
                    if 'ltp' in response['data']:
                        return float(response['data']['ltp'])
            return None
        except Exception as e:
            return None
            
