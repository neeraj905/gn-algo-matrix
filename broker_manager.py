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
                    return False, "smartapi-python missing"
                self.client = SmartConnect(api_key=self.creds["api_key"])
                totp = pyotp.TOTP(self.creds["totp_secret"]).now()
                data = self.client.generateSession(self.creds["client_id"], self.creds["password"], totp)
                if data and data.get("status"):
                    self.connected = True
                    return True, f"Angel One Connected ({self.creds['client_id']})"
                return False, data.get("message", "Login Failed")

            elif self.broker_name == "Kotak Neo":
                if not NeoAPI:
                    return False, "kotakneoapi missing"
                self.client = NeoAPI(environment="prod", access_token=self.creds["access_token"], neo_fin_key="neotradeapi")
                totp = pyotp.TOTP(self.creds["totp_secret"]).now()
                self.client.totp_login(mobile_number=self.creds["mobile_number"], ucc=self.creds["client_id"], totp=totp)
                if self.client.totp_validate(mpin=self.creds["password"]):
                    self.connected = True
                    return True, f"Kotak Neo Connected ({self.creds['client_id']})"
                return False, "Kotak Validation Failed"

            elif self.broker_name == "Dhan":
                if not dhanhq:
                    return False, "dhanhq missing"
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
                return False, "API Key & Token Required"

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
            return True, "Simulated Order Sent"
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
                            side = "SELL" if net > 0 else "BUY"
                            ltp = float(p.get("ltp", 0))
                            px = ltp * 1.02 if side == "BUY" else max(0.05, ltp * 0.98)
                            self.place_limit_order(p["tradingsymbol"], p["symboltoken"], side, abs(net), px, p["exchange"])
                            logs.append(f"Exited {p['tradingsymbol']} ({abs(net)})")
            return True, logs
        except Exception as e:
            return False, [str(e)]
