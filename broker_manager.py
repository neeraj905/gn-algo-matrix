import pyotp
import requests

try:
    from SmartApi import SmartConnect
except ImportError:
    SmartConnect = None

try:
    from neo_api_client import NeoAPI
except ImportError:
    NeoAPI = None

try:
    from dhanhq import dhanhq
except ImportError:
    dhanhq = None


class MultiBrokerHandler:
    def __init__(self, broker_name, creds):
        self.broker_name = broker_name
        self.creds = creds
        self.client = None
        self.connected = False

    def connect(self):
        try:
            if self.broker_name == "Angel One":
                if not SmartConnect:
                    return False, "smartapi-python library missing"
                self.client = SmartConnect(api_key=self.creds["api_key"])
                totp = pyotp.TOTP(self.creds["totp_secret"]).now()
                data = self.client.generateSession(
                    self.creds["client_id"], self.creds["password"], totp
                )
                if data and data.get("status"):
                    self.connected = True
                    return True, f"Angel One Connected ({self.creds['client_id']})"
                return False, data.get("message", "Angel One Login Failed")

            elif self.broker_name == "Kotak Neo":
                if not NeoAPI:
                    return False, "kotakneoapi library missing"
                self.client = NeoAPI(
                    environment="prod",
                    access_token=self.creds["access_token"],
                    neo_fin_key=self.creds.get("neo_fin_key", "neotradeapi")
                )
                totp = pyotp.TOTP(self.creds["totp_secret"]).now()
                self.client.totp_login(
                    mobile_number=self.creds["mobile_number"],
                    ucc=self.creds["client_id"],
                    totp=totp
                )
                if self.client.totp_validate(mpin=self.creds["password"]):
                    self.connected = True
                    return True, f"Kotak Neo Connected ({self.creds['client_id']})"
                return False, "Kotak Neo Validation Failed"

            elif self.broker_name == "Dhan":
                if not dhanhq:
                    return False, "dhanhq library missing"
                self.client = dhanhq(self.creds["client_id"], self.creds["access_token"])
                funds = self.client.get_fund_limits()
                if funds and funds.get("status") == "success":
                    self.connected = True
                    return True, f"Dhan Connected ({self.creds['client_id']})"
                return False, "Dhan Token Invalid"

            elif self.broker_name in ["Zerodha Kite", "Upstox"]:
                if self.creds.get("access_token") and self.creds.get("api_key"):
                    self.connected = True
                    return True, f"{self.broker_name} Active ({self.creds['client_id']})"
                return False, "API Key & Access Token Required"

            return False, "Unsupported Broker"
        except Exception as e:
            return False, str(e)

    def get_balance(self):
        if not self.connected:
            return 0.0
        try:
            if self.broker_name == "Angel One":
                res = self.client.rmsLimit()
                if res and res.get("status") and res.get("data"):
                    return float(res["data"].get("availablecash", 0.0))
            elif self.broker_name == "Kotak Neo":
                res = self.client.limits()
                if isinstance(res, dict):
                    return float(res.get("Net", 0.0))
            elif self.broker_name == "Dhan":
                res = self.client.get_fund_limits()
                if res and res.get("data"):
                    return float(res["data"].get("availabelBalance", 0.0))
            elif self.broker_name == "Zerodha Kite":
                headers = {"X-Kite-Version": "3", "Authorization": f"token {self.creds['api_key']}:{self.creds['access_token']}"}
                r = requests.get("https://kite.trade", headers=headers, timeout=5).json()
                return float(r["data"]["equity"]["available"]["live_balance"])
            elif self.broker_name == "Upstox":
                headers = {"Accept": "application/json", "Authorization": f"Bearer {self.creds['access_token']}"}
                r = requests.get("https://upstox.com", headers=headers, timeout=5).json()
                return float(r["data"]["equity"]["available_margin"])
        except Exception:
            pass
        return 0.0

    def get_ltp(self, exchange, symbol, token):
        if not self.connected:
            return None
        try:
            if self.broker_name == "Angel One":
                res = self.client.ltpData(exchange, symbol, str(token))
                if res and res.get("status") and res.get("data"):
                    return float(res["data"].get("ltp", 0.0))
            elif self.broker_name == "Zerodha Kite":
                headers = {"X-Kite-Version": "3", "Authorization": f"token {self.creds['api_key']}:{self.creds['access_token']}"}
                q = f"{exchange}:{symbol}"
                r = requests.get(f"https://kite.trade{q}", headers=headers, timeout=5).json()
                return float(r["data"][q]["last_price"])
        except Exception:
            pass
        return None

    def place_limit_order(self, symbol, token, side, qty, price, exchange="NFO"):
        if not self.connected:
            return False, "Broker Not Connected"
        try:
            price = round(float(price), 2)
            qty = int(qty)

            if self.broker_name == "Angel One":
                params = {
                    "variety": "NORMAL",
                    "tradingsymbol": symbol,
                    "symboltoken": str(token),
                    "transactiontype": side,
                    "exchange": exchange,
                    "ordertype": "LIMIT",
                    "producttype": "INTRADAY",
                    "duration": "DAY",
                    "price": str(price),
                    "squareoff": "0",
                    "stoploss": "0",
                    "quantity": str(qty)
                }
                oid = self.client.placeOrder(params)
                return (True, oid) if oid else (False, "No Order ID")

            elif self.broker_name == "Kotak Neo":
                seg = "bse_fo" if exchange == "BFO" else "nse_fo"
                res = self.client.place_order(
                    exchange_segment=seg,
                    product="MIS",
                    price=str(price),
                    order_type="L",
                    quantity=str(qty),
                    validity="DAY",
                    trading_symbol=symbol,
                    transaction_type="B" if side == "BUY" else "S"
                )
                return True, str(res)

            elif self.broker_name == "Dhan":
                seg = self.client.BSE_FNO if exchange == "BFO" else self.client.FNO
                res = self.client.place_order(
                    security_id=str(token),
                    exchange_segment=seg,
                    transaction_type=self.client.BUY if side == "BUY" else self.client.SELL,
                    quantity=qty,
                    order_type=self.client.LIMIT,
                    product_type=self.client.INTRA,
                    price=price
                )
                return True, str(res)

            elif self.broker_name == "Zerodha Kite":
                headers = {"X-Kite-Version": "3", "Authorization": f"token {self.creds['api_key']}:{self.creds['access_token']}"}
                payload = {
                    "tradingsymbol": symbol,
                    "exchange": exchange,
                    "transaction_type": side,
                    "order_type": "LIMIT",
                    "quantity": qty,
                    "product": "MIS",
                    "price": price,
                    "validity": "DAY"
                }
                r = requests.post("https://kite.trade", headers=headers, data=payload, timeout=5).json()
                return True, str(r)

            elif self.broker_name == "Upstox":
                headers = {"Accept": "application/json", "Authorization": f"Bearer {self.creds['access_token']}"}
                payload = {
                    "quantity": qty,
                    "product": "I",
                    "validity": "DAY",
                    "price": price,
                    "instrument_token": str(token),
                    "order_type": "LIMIT",
                    "transaction_type": side,
                    "disclosed_quantity": 0,
                    "trigger_price": 0,
                    "is_amo": False
                }
                r = requests.post("https://upstox.com", headers=headers, json=payload, timeout=5).json()
                return True, str(r)

            return False, "Order routing error"
        except Exception as e:
            return False, str(e)

    def square_off_all(self):
        logs = []
        if not self.connected:
            return False, ["Broker not connected"]
        try:
            if self.broker_name == "Angel One":
                ob = self.client.orderBook()
                if ob and ob.get("data"):
                    for o in ob["data"]:
                        if str(o.get("orderstatus", "")).lower() in ["open", "trigger pending", "validation pending"]:
                            self.client.cancelOrder(o["orderid"], o["variety"])
                            logs.append(f"Cancelled Order: {o['orderid']}")
                pos = self.client.position()
                if pos and pos.get("data"):
                    for p in pos["data"]:
                        net = int(p.get("netqty", 0))
                        if net != 0:
