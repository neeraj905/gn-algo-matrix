import requests
import yfinance as yf
from datetime import datetime

# Angel One Public Scrip Master URL (Sabhi NSE/BSE Option Tokens ke liye)
SCRIP_MASTER_URL = "https://angelbroking.com"

INDEX_CONFIG = {
    "NIFTY": {
        "yf_ticker": "^NSEI",
        "exch_seg": "NFO",
        "opt_type": "OPTIDX",
        "step": 50,
        "lot_size": 75,
        "spot_token": "99926000",
        "spot_exch": "NSE",
        "spot_sym": "Nifty 50"
    },
    "BANKNIFTY": {
        "yf_ticker": "^NSEBANK",
        "exch_seg": "NFO",
        "opt_type": "OPTIDX",
        "step": 100,
        "lot_size": 30,
        "spot_token": "99926009",
        "spot_exch": "NSE",
        "spot_sym": "Nifty Bank"
    },
    "FINNIFTY": {
        "yf_ticker": "NIFTY_FIN_SERVICE.NS",
        "exch_seg": "NFO",
        "opt_type": "OPTIDX",
        "step": 50,
        "lot_size": 65,
        "spot_token": "99926037",
        "spot_exch": "NSE",
        "spot_sym": "Nifty Fin Service"
    },
    "MIDCPNIFTY": {
        "yf_ticker": "^NSEMDCP50",
        "exch_seg": "NFO",
        "opt_type": "OPTIDX",
        "step": 25,
        "lot_size": 120,
        "spot_token": "99926074",
        "spot_exch": "NSE",
        "spot_sym": "NIFTY MID SELECT"
    },
    "SENSEX": {
        "yf_ticker": "^BSESN",
        "exch_seg": "BFO",
        "opt_type": "OPTIDX",
        "step": 100,
        "lot_size": 20,
        "spot_token": "99919000",
        "spot_exch": "BSE",
        "spot_sym": "SENSEX"
    }
}


class MultiIndexLiveEngine:
    def __init__(self):
        self.scrip_data = []
        self.last_loaded_date = None

    def load_scrip_master(self):
        """Din mein ek baar Angel One ka official option token master download karta hai"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.scrip_data and self.last_loaded_date == today:
            return True
        try:
            resp = requests.get(SCRIP_MASTER_URL, timeout=12)
            if resp.status_code == 200:
                raw = resp.json()
                # Sirf 5 indices ke OPTIDX contracts filter karein
                target_names = set(INDEX_CONFIG.keys())
                self.scrip_data = [
                    item for item in raw
                    if item.get("instrumenttype") == "OPTIDX" and item.get("name") in target_names
                ]
                self.last_loaded_date = today
                return True
        except Exception as e:
            print(f"Scrip Master Load Error: {e}")
        return False

    def get_live_spot_and_change(self, index_name, broker_handler=None):
        """Pehle active broker se real-time LTP leta hai, fallback mein Yahoo Finance use karta hai"""
        cfg = INDEX_CONFIG[index_name]
        spot = None
        day_change_pct = 0.0

        # 1. Broker Live API se exact tick price
        if broker_handler and broker_handler.connected:
            spot = broker_handler.get_ltp(cfg["spot_exch"], cfg["spot_sym"], cfg["spot_token"])

        # 2. Yahoo Finance se intraday open/close change % (Sideways check ke liye)
        try:
            ticker = yf.Ticker(cfg["yf_ticker"])
            hist = ticker.history(period="1d", interval="5m")
            if not hist.empty:
                open_px = float(hist["Open"].iloc[0])
                last_px = float(hist["Close"].iloc[-1])
                if not spot:
                    spot = last_px
                if open_px > 0:
                    day_change_pct = ((spot - open_px) / open_px) * 100.0
        except Exception:
            pass

        return round(spot, 2) if spot else None, round(day_change_pct, 3)

    def get_atm_option_contracts(self, index_name, spot_price):
        """Spot price ke hisaab se nearest expiry ka ATM CE aur ATM PE symbol + token nikalta hai"""
        if not spot_price or not self.load_scrip_master():
            return None, None

        cfg = INDEX_CONFIG[index_name]
        step = cfg["step"]
        atm_strike = round(spot_price / step) * step
        target_strike_val = atm_strike * 100  # Angel scrip master strike * 100 format mein hota hai

        now = datetime.now()
        matching = []
        for item in self.scrip_data:
            if item.get("name") == index_name and item.get("exch_seg") == cfg["exch_seg"]:
                try:
                    strike_num = float(item.get("strike", 0))
                    if abs(strike_num - target_strike_val) < 1:
                        exp_dt = datetime.strptime(item["expiry"], "%d%b%Y")
                        if exp_dt.date() >= now.date():
                            matching.append((exp_dt, item))
                except Exception:
                    continue

        if not matching:
            return None, None

        # Sabse nearest expiry chunein
        matching.sort(key=lambda x: x[0])
        nearest_exp = matching[0][0]

        ce_contract = None
        pe_contract = None
        for exp_dt, item in matching:
            if exp_dt == nearest_exp:
                sym = item.get("symbol", "")
                if sym.endswith("CE"):
                    ce_contract = {
                        "symbol": sym,
                        "token": item["token"],
                        "exchange": cfg["exch_seg"],
                        "strike": atm_strike,
                        "lot_size": int(item.get("lotsize", cfg["lot_size"]))
                    }
                elif sym.endswith("PE"):
                    pe_contract = {
                        "symbol": sym,
                        "token": item["token"],
                        "exchange": cfg["exch_seg"],
                        "strike": atm_strike,
                        "lot_size": int(item.get("lotsize", cfg["lot_size"]))
                    }
        return ce_contract, pe_contract

    def evaluate_signal(self, day_change_pct):
        """
        Sideways Market Filter + Momentum Signal:
        - Agar move -0.18% se +0.18% ke beech hai -> SIDEWAYS (No Trade)
        - Agar move > +0.18% -> BULLISH (BUY CALL)
        - Agar move < -0.18% -> BEARISH (BUY PUT)
        """
        if abs(day_change_pct) < 0.18:
            return "SIDEWAYS"
        elif day_change_pct >= 0.18:
            return "BUY_CE"
        else:
            return "BUY_PE"
  
