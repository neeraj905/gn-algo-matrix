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
            if response and response.get('status') and response.get('data'):
                return float(response['data']['ltp'])
        except Exception as e:
            print(f"Error fetching LTP: {e}")
        return None

    def get_profile(self):
        try:
            if not self.smart_api or not self.session_data:
                return None
            res = self.smart_api.getProfile(self.session_data.get('refreshToken'))
            if res and res.get('status'):
                return res.get('data')
        except Exception:
            pass
        return None

    def get_funds(self):
        try:
            if not self.smart_api:
                return None
            res = self.smart_api.rmsLimit()
            if res and res.get('status'):
                return res.get('data')
        except Exception:
            pass
        return None

    def get_balance(self):
        """Available cash balance nikalne ke liye (Dashboard ke 25%/75% split ke liye)"""
        funds = self.get_funds()
        if funds:
            try:
                return float(funds.get('availablecash', 0.0))
            except Exception:
                return 0.0
        return 0.0

    def place_limit_order(self, exchange, symbol, token, transaction_type, quantity, price):
        """
        Real Limit Order bhejne ke liye (SEBI rules ke mutabik Limit Order safe rehta hai)
        transaction_type: 'BUY' ya 'SELL'
        """
        try:
            if not self.smart_api:
                return False, "Broker not connected"
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": str(token),
                "transactiontype": transaction_type,
                "exchange": exchange,
                "ordertype": "LIMIT",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": str(round(float(price), 2)),
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(int(quantity))
            }
            order_id = self.smart_api.placeOrder(order_params)
            if order_id:
                return True, order_id
            return False, "Order ID not returned"
        except Exception as e:
            return False, str(e)

    def modify_order(self, order_id, exchange, symbol, token, quantity, new_price):
        """Pending order ka price replace/modify karne ke liye"""
        try:
            if not self.smart_api:
                return False, "Broker not connected"
            params = {
                "variety": "NORMAL",
                "orderid": str(order_id),
                "ordertype": "LIMIT",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": str(round(float(new_price), 2)),
                "quantity": str(int(quantity)),
                "tradingsymbol": symbol,
                "symboltoken": str(token),
                "exchange": exchange
            }
            res = self.smart_api.modifyOrder(params)
            return True, res
        except Exception as e:
            return False, str(e)

    def square_off_all(self):
        """Emergency Kill Switch & 3:15 PM Auto Exit: Saare pending orders cancel aur open positions close karega"""
        logs = []
        if not self.smart_api:
            return False, ["Broker not connected"]
        try:
            # Step 1: Saare open/pending orders cancel karein
            order_book = self.smart_api.orderBook()
            if order_book and order_book.get('status') and order_book.get('data'):
                for order in order_book['data']:
                    status = str(order.get('orderstatus', '')).lower()
                    if status in ['open', 'trigger pending', 'validation pending']:
                        self.smart_api.cancelOrder(order['orderid'], order['variety'])
                        logs.append(f"Cancelled pending order: {order['orderid']}")

            # Step 2: Saari open positions ko turant exit karein
            positions = self.smart_api.position()
            if positions and positions.get('status') and positions.get('data'):
                for pos in positions['data']:
                    net_qty = int(pos.get('netqty', 0))
                    if net_qty != 0:
                        exit_type = "SELL" if net_qty > 0 else "BUY"
                        ltp = float(pos.get('ltp', 0))
                        # Turant execution ke liye LTP par 2% protection buffer
                        exec_price = ltp * 1.02 if exit_type == "BUY" else max(0.05, ltp * 0.98)
                        ok, resp = self.place_limit_order(
                            exchange=pos['exchange'],
                            symbol=pos['tradingsymbol'],
                            token=pos['symboltoken'],
                            transaction_type=exit_type,
                            quantity=abs(net_qty),
                            price=exec_price
                        )
                        logs.append(f"Exited {pos['tradingsymbol']} ({abs(net_qty)} qty): {resp}")
            return True, logs
        except Exception as e:
            return False, [str(e)]
