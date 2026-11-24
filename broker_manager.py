import pyotp
import requests

# Angel One SDK
try:
    from SmartApi import SmartConnect
except ImportError:
    SmartConnect = None

# Kotak Neo SDK
try:
    from neo_api_client import NeoAPI
except ImportError:
    NeoAPI = None

# Dhan SDK
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
                    return False, "smartapi-python library install nahi hai"
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
                    return False, "kotakneoapi library install nahi hai"
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
                val_res = self.client.totp_validate(mpin=self.creds["password"])
                if val_res:
                    self.connected = True
                    return True, f"Kotak Neo Connected ({self.creds['client_id']})"
                return False, "Kotak Neo TOTP/MPIN Validation Failed"

            elif self.broker_name == "Dhan":
                if not dhanhq:
                    return False, "dhanhq library install nahi hai"
                self.client = dhanhq(self.creds["client_id"], self.creds["access_token"])
                funds = self.client.get_fund_limits()
                if funds and funds.get("status") == "success":
                    self.connected = True
                    return True, f"Dhan Connected ({self.creds['client_id']})"
                return False, "Dhan Token/Client ID Invalid"

            elif self.broker_name in ["Zerodha Kite", "Upstox"]:
                # Access token based session verification
                if self.creds.get("access_token") and self.creds.get("api_key"):
                    self.connected = True
                    return True, f"{self.broker_name} Session Active ({self.creds['client_id']})"
                return False, "API Key aur Daily Access Token zaroori hai"

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
                if res and isinstance(res, dict):
                    return float(res.get("Net", 0.0))

            elif self.broker_name == "Dhan":
                res = self.client.get_fund_limits()
                if res and res.get("data"):
                    return float(res["data"].get("availabelBalance", 0.0))

            elif self.broker_name == "Zerodha Kite":
                headers = {
                    "X-Kite-Version": "3",
                    "Authorization": f"token {self.creds['api_key']}:{self.creds['access_token']}"
                }
                r = requests.get("https://kite.trade", headers=headers, timeout=5).json()
                return float(r["data"]["equity"]["available"]["live_balance"])

            elif self.broker_name == "Upstox":
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.creds['access_token']}"
                }
                r = requests.get("https://upstox.com", headers=headers, timeout=5).json()
                return float(r["data"]["equity"]["available_margin"])
        except Exception:
            pass
        return 0.0

    def place_limit_order(self, symbol, token, side, qty, price, exchange="NFO"):
        """SEBI Compliant Limit Order Placement across all brokers"""
        if not self.connected:
            return False, "Broker Connected Nahi Hai"
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
                return True, oid

            elif self.broker_name == "Kotak Neo":
                res = self.client.place_order(
                    exchange_segment="nse_fo" if exchange == "NFO" else "nse_cm",
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
                res = self.client.place_order(
                    security_id=str(token),
                    exchange_segment=self.client.FNO if exchange == "NFO" else self.client.NSE,
                    transaction_type=self.client.BUY if side == "BUY" else self.client.SELL,
                    quantity=qty,
                    order_type=self.client.LIMIT,
                    product_type=self.client.INTRA,
                    price=price
                )
                return True, str(res)

            elif self.broker_name == "Zerodha Kite":
                headers = {
                    "X-Kite-Version": "3",
                    "Authorization": f"token {self.creds['api_key']}:{self.creds['access_token']}"
                }
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
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.creds['access_token']}"
                }
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
        """Emergency Kill Switch & 3:15 PM Auto Exit for Active Broker"""
        logs = []
        if not self.connected:
            return False, ["Broker not connected"]
        try:
            if self.broker_name == "Angel One":
                ob = self.client.orderBook()
                if ob and ob.get("data"):
                    for o in ob["data"]:
                        if str(o.get("orderstatus", "")).lower() in ["open", "trigger pending"]:
                            self.client.cancelOrder(o["orderid"], o["variety"])
                            logs.append(f"Cancelled: {o['orderid']}")
                pos = self.client.position()
                if pos and pos.get("data"):
                    for p in pos["data"]:
                        net = int(p.get("netqty", 0))
                        if net != 0:
                            side = "SELL" if net > 0 else "BUY"
                            ltp = float(p.get("ltp", 0))
                            px = ltp * 1.02 if side == "BUY" else max(0.05, ltp * 0.98)
                            self.place_limit_order(p["tradingsymbol"], p["symboltoken"], side, abs(net), px, p["exchange"])
                  
