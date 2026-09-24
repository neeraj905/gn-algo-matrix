if __name__ == '__main__':
    status = check_bot_status()
    print(f"Current Bot Status: {status}")

    if status == "ON":
        ist = pytz.timezone('Asia/Kolkata')
        current_time_str = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
        
        # Market check hata diya taaki abhi test ho sake
        market_msg = "Market Test Mode"
        market_data = get_live_market_data()
        
        msg = "🚨 *GN ALGO MATRIX - TEST SIGNAL* 🚨\n"
        msg += f"⏰ *Time (IST):* `{current_time_str}`\n\n"
        
        if market_data:
            for symbol, data in market_data.items():
                price = data['price']
                prev_close = data['prev_close']
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                
                msg += f"📊 *Index:* {symbol}\n"
                msg += f"💰 *Live Price:* `{price:,.2f}`\n"
                msg += f"📊 *Change:* `{change:+.2f} ({change_pct:+.2f}%)`\n"
                msg += "-----------------------------------\n"
            
            send_message(msg)
        else:
            print("Failed to fetch market data.")
            # Agar data na aaye toh kam se kam ek test message bhej kar check karo ki Telegram API kaam kar rahi hai ya nahi
            send_message("⚠️ Test message: Bot is running, but market data failed to fetch.")
                
