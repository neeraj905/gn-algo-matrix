    engine = st.session_state.market_engine
    handler = st.session_state.broker_handler
    unrealized_pnl = 0.0
    sideways_count = 0
    crash_detected = False
    crash_index = ""

    for idx_name in INDEX_CONFIG.keys():
        spot, chg_pct = engine.get_live_spot_and_change(idx_name, handler)
        prev_spot = st.session_state.prev_spots.get(idx_name, spot)
        if spot:
            st.session_state.prev_spots[idx_name] = spot
        tick_up = (spot >= prev_spot) if (spot and prev_spot) else (chg_pct >= 0)
        num_color = "#22C55E" if (chg_pct >= 0 and tick_up) else "#EF4444"
        arrow = "▲" if chg_pct >= 0 else "▼"
        if chg_pct <= -0.85:
            crash_detected = True
            crash_index = f"{idx_name} ({chg_pct:+.2f}%)"
        signal = engine.evaluate_signal(chg_pct)
        if signal == "SIDEWAYS":
            sideways_count += 1
        ce_contract, pe_contract = engine.get_atm_option_contracts(idx_name, spot) if spot else (None, None)
        ce_sym = ce_contract["symbol"] if ce_contract else f"{idx_name} ATM CE"
        pe_sym = pe_contract["symbol"] if pe_contract else f"{idx_name} ATM PE"
        ce_ltp = handler.get_ltp(ce_contract["exchange"], ce_sym, ce_contract["token"]) if (handler and hasattr(handler, "get_ltp") and ce_contract) else None
        pe_ltp = handler.get_ltp(pe_contract["exchange"], pe_sym, pe_contract["token"]) if (handler and hasattr(handler, "get_ltp") and pe_contract) else None
        active = st.session_state.active_trades.get(idx_name)
        idx_pnl = 0.0
        if active:
            curr_ltp = ce_ltp if active["side"] == "CE" else pe_ltp
            if curr_ltp:
                idx_pnl = round((curr_ltp - active["entry"]) * active["qty"], 2)
                if curr_ltp > active["highest"]:
                    active["highest"] = curr_ltp
                    new_sl = round(curr_ltp * 0.95, 2)
                    if new_sl > active["sl"]:
                        active["sl"] = new_sl
                        add_log(f"📈 TRAIL SL UP {active['symbol']}: New SL ₹{active['sl']}")
                if curr_ltp <= active["sl"]:
                    if st.session_state.trading_mode == "LIVE REAL MONEY" and handler:
                        ok_exit, exit_res = handler.place_limit_order(active["symbol"], active["token"], "SELL", active["qty"], max(0.05, curr_ltp * 0.98), active["exchange"])
                        if not ok_exit:
                            trigger_danger_alarm(f"EXIT FAILED ({active['symbol']}): {exit_res}")
                    st.session_state.realized_pnl += idx_pnl
                    add_log(f"🛑 5% SL EXIT {active['symbol']} @ ₹{curr_ltp} | P&L: ₹{idx_pnl}")
                    del st.session_state.active_trades[idx_name]
                    active = None
                            if not active and st.session_state.bot_running and not st.session_state.capital_locked and is_market_open and signal in ["BUY_CE", "BUY_PE"]:
            chosen = ce_contract if signal == "BUY_CE" else pe_contract
            entry_ltp = ce_ltp if signal == "BUY_CE" else pe_ltp
            if chosen and entry_ltp and entry_ltp > 5.0:
                qty = chosen["lot_size"] * int(st.session_state.lots_per_index)
                if (entry_ltp * qty) <= risk_cap:
                    order_ok = True
                    if st.session_state.trading_mode == "LIVE REAL MONEY" and handler:
                        order_ok, oid = handler.place_limit_order(chosen["symbol"], chosen["token"], "BUY", qty, round(entry_ltp * 1.01, 2), chosen["exchange"])
                        if not order_ok:
                            trigger_danger_alarm(f"ORDER FAILED ({chosen['symbol']}): {oid}")
                        add_log(f"LIVE BUY {chosen['symbol']} ({qty}) -> {oid}")
                    else:
                        add_log(f"PAPER BUY {chosen['symbol']} ({qty}) @ ₹{entry_ltp}")
                    if order_ok:
                        st.session_state.active_trades[idx_name] = {"symbol": chosen["symbol"], "token": chosen["token"], "exchange": chosen["exchange"], "side": "CE" if signal == "BUY_CE" else "PE", "entry": entry_ltp, "highest": entry_ltp, "qty": qty, "sl": round(entry_ltp * 0.95, 2)}

        unrealized_pnl += idx_pnl
        spot_val = f"{spot:,.2f} ({chg_pct:+.2f}%)" if spot else "Scanning..."
        status_badge = "🟡 SIDEWAYS" if signal == "SIDEWAYS" else ("🟢 BULLISH" if signal == "BUY_CE" else "🔴 BEARISH")
        st.markdown(f"<div style='background-color:#1E293B;padding:8px 12px;border-radius:8px;border-left:4px solid {num_color};margin-top:6px;display:flex;justify-content:space-between;align-items:center;'><span style='font-weight:bold;color:#F8FAFC;'>{idx_name} • {status_badge}</span><span style='font-weight:900;font-size:1.05rem;color:{num_color};'>{arrow} {spot_val}</span></div>", unsafe_allow_html=True)
        with st.expander(f"Options & 5% Trailing SL ({idx_name})", expanded=False):
            st.table([
                {"Contract": ce_sym, "Signal": "ACTIVE BUY" if (active and active["side"] == "CE") else "WAIT", "Entry": active["entry"] if (active and active["side"] == "CE") else "-", "Live LTP": ce_ltp if ce_ltp else "API Req", "5% Trail SL": active["sl"] if (active and active["side"] == "CE") else "-"},
                {"Contract": pe_sym, "Signal": "ACTIVE BUY" if (active and active["side"] == "PE") else "WAIT", "Entry": active["entry"] if (active and active["side"] == "PE") else "-", "Live LTP": pe_ltp if pe_ltp else "API Req", "5% Trail SL": active["sl"] if (active and active["side"] == "PE") else "-"}
            ])

    market_is_safe = (not crash_detected) and (sideways_count < 4)
    if st.session_state.bot_running and not market_is_safe:
        trigger_capital_lock(f"Crash Alert in {crash_index}" if crash_detected else "Heavy Sideways Hulchul (4+ Indices)")

    total_pnl = round(st.session_state.realized_pnl + unrealized_pnl, 2)
    if total_pnl <= st.session_state.max_loss_limit and st.session_state.bot_running:
        execute_emergency_square_off(f"Max Loss Limit Crossed (₹{total_pnl:,.2f})")

    st.markdown("---")
    st.subheader("💰 Total Net P&L (All 5 Indices Combined)")
    pnl_color = "#22C55E" if total_pnl >= 0 else "#EF4444"
    st.markdown(f"<h2 style='color: {pnl_color};'>{'🟢' if total_pnl >= 0 else '🔴'} ₹{total_pnl:,.2f}</h2>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🛡️ Capital Lock & Green Re-Open Signal")
    if st.session_state.capital_locked or not market_is_safe:
        lock_msg = st.session_state.lock_reason if st.session_state.capital_locked else ("Crash Risk Detected" if crash_detected else "Market Sideways — Waiting for Clear Trend")
        st.markdown(f'<div class="lock-beacon">🔒 CAPITAL LOCKED (SAFE MODE)<br><span style="font-size:0.85rem;">Reason: {lock_msg}</span></div>', unsafe_allow_html=True)
        if market_is_safe:
            st.markdown('<div class="safe-beacon">🟢 GREEN SIGNAL: MARKET AB SAFE HAI — ALGO RE-OPEN KAR SAKTE HAIN!</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="safe-beacon">🟢 GREEN SIGNAL: MARKET STABLE & TRENDING — SAFE TO RUN ALGO</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Wake Up / Re-Open Algo", use_container_width=True):
            if not is_market_open:
                st.error("Market abhi band hai (09:15 - 03:15 ke beech hi start hoga).")
            elif not market_is_safe:
                st.warning("Abhi Green Signal nahi mila hai—thoda intezar karein.")
            else:
                st.session_state.capital_locked = False
                st.session_state.lock_reason = ""
                st.session_state.bot_running = True
                st.session_state.danger_alarm = False
                add_log("🟢 Green Signal Confirmed: Algo Re-Opened!")
                st.rerun()
    with c2:
        if st.button("🚨 Emergency Exit All", type="primary", use_container_width=True):
            execute_emergency_square_off("User Pressed Emergency Exit All!")
            st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>Multi-Index Pro • Nifty, BankNifty, FinNifty, Midcap & Sensex Active</p>", unsafe_allow_html=True)
                                 
