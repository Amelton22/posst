import logging
import os
import warnings
import sys
import pandas as pd
import json
import requests
import time
import datetime
from datetime import datetime, timedelta
import pytz
import talib as ta
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import mplfinance as mpf
import win32com.client
import threading
import queue
import csv  # Add this line
SCRIPT_VERSION = "1.0"

try:
    log_file = r"C:\Users\dad\StockApp\logs\stock_signals.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(r"C:\Users\dad\StockApp\test.txt", "w") as f:
        f.write("test")
    # Clear any existing handlers to prevent console output
    logging.getLogger('').handlers.clear()
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8')
        ]
    )
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('mplfinance').setLevel(logging.WARNING)
    logging.debug("Logging initialized successfully")
except Exception as e:
    # Fallback configuration to ensure logging to file
    logging.getLogger('').handlers.clear()
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8')
        ]
    )
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('mplfinance').setLevel(logging.WARNING)
    logging.error(f"Failed to initialize logging to {log_file}: {e}")
logging.info("Script started, testing logging")
def beep():
    try:
        import winsound
        winsound.Beep(1000, 500)
    except Exception:
        pass

# Snippet 60: Updated class start with backtest logger in __init__ (replace from class to self.trading_mode)
class StockSignalsApp:
    # Snippet 170: Updated __init__ to fix NameError and add speak method
    def speak(self, message):
        """Speak a message using the speech engine if available and not muted."""
        if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
            try:
                self.speech_engine.Speak(message)
                logging.debug(f"Speaking: {message}")
            except Exception as e:
                logging.error(f"Error speaking message '{message}': {e}")

    # Snippet 7: Full __init__ method with all fixes applied (replace the entire __init__ method in part 1)
    def __init__(self, root):
        logging.debug("Starting initialization")
        try:
            self.root = root
            self.root.title("Stock Signals App")
            self.root.geometry("1000x850+100+100")
            self.last_fetch_time = {}
            self.added_stocks = set()
            self.base_cash = 1000.0
            self.day_portfolio = {}
            self.swing_portfolio = {}
            self.portfolio = self.day_portfolio
            self.data_cache = {}
            self.tabs = {}
            self.signal_labels = {}
            self.indicator_tables = {}
            self.interval_var = tk.StringVar(value="3min")
            self.transaction_history = {}
            self.day_cost_basis = {}
            self.swing_cost_basis = {}
            # Backtest logger setup
            self.backtest_logger = logging.getLogger('backtest')
            self.backtest_handler = logging.FileHandler(os.path.join(r"C:\Users\dad\StockApp\logs", "backtest_results.log"), mode='a', encoding='utf-8')
            self.backtest_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            self.backtest_handler.setFormatter(formatter)
            self.backtest_logger.addHandler(self.backtest_handler)
            self.backtest_logger.setLevel(logging.INFO)
            self.backtest_logger.propagate = False
            logging.getLogger('backtest').info("Backtest logger initialized")
            self.real_trades_logger = logging.getLogger('real_trades')
            self.real_trades_handler = logging.FileHandler(os.path.join(r"C:\Users\dad\StockApp\logs", "auto_trades.log"), mode='a', encoding='utf-8')
            self.real_trades_handler.setLevel(logging.INFO)
            self.real_trades_handler.setFormatter(formatter)
            self.real_trades_logger.addHandler(self.real_trades_handler)
            self.real_trades_logger.setLevel(logging.INFO)
            self.real_trades_logger.propagate = False
            self.real_trades_logger.info("Auto trades logger initialized")
            self.trade_counter = 0  # Sequential trade ID
            self.run_id = datetime.now(pytz.timezone("America/New_York")).strftime('%Y%m%d_%H%M%S')  # Run ID for CSV
            self.trading_mode = "day"
            self.last_trade_time = {}
            self.use_auto_trading = False
            self.manual_purchases = set()
            self.mock_base_cash = 1000.0
            self.mock_portfolio = {}
            self.mock_cost_basis = {}
            self.mock_last_trade_time = {}
            self.mock_transaction_history = {}
            self.buy_threshold = tk.DoubleVar(value=0.4)
            self.backtest_filter_var = tk.StringVar(value="All Trades")
            self.volume_level = tk.DoubleVar(value=1.0)
            self.is_muted = tk.BooleanVar(value=False)
            self.zone_period = 14
            self.group_visibility = {
                "Basic": tk.BooleanVar(value=True),
                "Advanced 1": tk.BooleanVar(value=True),
                "Advanced 2": tk.BooleanVar(value=True),
                "Advanced 3": tk.BooleanVar(value=True)
            }
            self.indicator_visibility = {
                "mfi": tk.BooleanVar(value=True),
                "macd": tk.BooleanVar(value=True),
                "stochastic": tk.BooleanVar(value=True),
                "ema13": tk.BooleanVar(value=True),
                "cci": tk.BooleanVar(value=True),
                "obv": tk.BooleanVar(value=True),
                "vwap": tk.BooleanVar(value=True),
                "demand_zone": tk.BooleanVar(value=True),
                "adx": tk.BooleanVar(value=True),
                "atr": tk.BooleanVar(value=True),
                "momentum": tk.BooleanVar(value=True),
                "stochastic_rsi": tk.BooleanVar(value=True),
                "williams_%r": tk.BooleanVar(value=True),
                "bollinger_bands": tk.BooleanVar(value=True),
                "rsi": tk.BooleanVar(value=True)
            }
            # Toggle loading after visibility vars
            toggles_file = os.path.join(r"C:\Users\dad\StockApp", "toggles.json")
            if os.path.exists(toggles_file):
                try:
                    with open(toggles_file, "r") as f:
                        toggles_data = json.load(f)
                    group_data = toggles_data.get("group_visibility", {})
                    for group, value in group_data.items():
                        if group in self.group_visibility and isinstance(value, bool):
                            self.group_visibility[group].set(value)
                    indicator_data = toggles_data.get("indicator_visibility", {})
                    for indicator_key, value in indicator_data.items():
                        if indicator_key in self.indicator_visibility and isinstance(value, bool):
                            self.indicator_visibility[indicator_key].set(value)
                    logging.info("Loaded toggle states from {}".format(toggles_file))
                except Exception as e:
                    logging.error("Error loading toggles: {}".format(e))
            self.supply_thresholds = {}
            self.demand_thresholds = {}
            self.threshold_zone_periods = {}
            self.manual_thresholds = {}
            self.highest_price = {}
            self.last_stock_update = 0
            self.fetch_queue = queue.Queue()
            self.after_ids = []
            self.threads = []
            self.cache_lock = threading.Lock()
            self.market_closed_warned = False
            self.data_fetch_manual_override = False
            self.held_stocks_file = os.path.join(r"C:\Users\dad\StockApp", "held_stocks.json")
            self.added_stocks_file = os.path.join(r"C:\Users\dad\StockApp", "added_stocks.json")
            self.screener_csv = os.path.join(r"C:\Users\dad\StockApp", "finviz.csv")
            self.next_refresh_time = datetime.now().timestamp() + 60
            self.market_closed_fetched = False
            self.data_fetch_enabled = True
            self.last_clear_date = datetime.now(pytz.timezone("America/New_York")).date()
            self._cache_data_to_save = {}
            self.failed_stocks = set()
            self.invalid_stocks = set()
            self.api_key = os.getenv("FMP_API_KEY") or "x1Xlj2xgF7mTkwjiDsRbUW3Nwjy9kyYT"
            if not self.api_key:
                logging.error("FMP_API_KEY not set")
                self.root.after(0, lambda: messagebox.showerror("Error", "FMP_API_KEY environment variable is required"))
                raise ValueValue("FMP_API_KEY not set")
            try:
                response = requests.get("https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={}".format(self.api_key))
                response.raise_for_status()
                if response.status_code != 200:
                    logging.error("Invalid FMP_API_KEY")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Invalid FMP_API_KEY. Please verify your API key."))
                    raise ValueError("Invalid FMP_API_KEY")
                logging.debug("API key validated successfully")
            except Exception as e:
                logging.error("API key validation failed: {}".format(e))
                self.root.after(0, lambda: messagebox.showerror("Error", "API key validation failed: {}".format(str(e))))
                raise
            self.status_label = ttk.Label(self.root, text="Initializing...", style="Status.TLabel")
            self.status_label.pack(side="top", pady=2)
            self.data_cache.clear()
            cache_file = os.path.join(r"C:\Users\dad\StockApp", "stock_cache.json")
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    logging.info("Cleared cache: {}".format(cache_file))
                except Exception as e:
                    logging.error("Error clearing cache: {}".format(e))
            if hasattr(self, 'load_portfolio'):
                self.load_portfolio()
                logging.debug("Portfolio loaded: day_portfolio={}, swing_portfolio={}, added_stocks={}".format(self.day_portfolio, self.swing_portfolio, self.added_stocks))
            else:
                logging.error("load_portfolio method not found in StockSignalsApp")
                self.day_portfolio = {}
                self.swing_portfolio = {}
                self.day_cost_basis = {}
                self.swing_cost_basis = {}
                self.added_stocks = set()
                self.portfolio = self.day_portfolio
                self.cost_basis = self.day_cost_basis
            try:
                if os.path.exists(self.added_stocks_file):
                    with open(self.added_stocks_file, "r") as f:
                        self.added_stocks = set(json.load(f))
                    logging.info("Loaded added stocks from {}: {}".format(self.added_stocks_file, self.added_stocks))
                else:
                    logging.info("No {} found, initializing empty".format(self.added_stocks_file))
                    self.added_stocks = set()
            except Exception as e:
                logging.error("Error loading added stocks: {}".format(e))
                self.added_stocks = set()
            held_stocks = list(set(self.day_portfolio.keys()) | set(self.swing_portfolio.keys()) | set(self.added_stocks))
            screener_stocks = self.fetch_screener_stocks()
            # Cap screener stocks at 10, prioritize high volume, filter valid
            valid_screener = []
            for s in screener_stocks[:10]:  # Early cap to 10
                df_test = self.fetch_data(s, self.interval_var.get(), force_fetch=True)
                if not df_test.empty and 'Close' in df_test.columns and not df_test['Close'].isna().all():
                    valid_screener.append(s)
                else:
                    self.invalid_stocks.add(s)
                    logging.warning("Filtered out invalid screener stock {}".format(s))
            if valid_screener:
                valid_screener = sorted(valid_screener, key=lambda s: self.get_stock_volume(s), reverse=True)[:10]
                logging.info("Capped valid screener stocks at 10 high-volume: {}".format(valid_screener))
            screener_stocks = valid_screener
            logging.info("Fetched screener stocks: {}".format(screener_stocks))
            self.stocks = list(dict.fromkeys(held_stocks + screener_stocks))
            if not self.stocks:
                self.stocks = []
            logging.debug("Stocks initialized: {}".format(self.stocks))
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds_{}.json".format(self.zone_period))
            try:
                if os.path.exists(thresholds_file):
                    with open(thresholds_file, "r") as f:
                        thresholds_data = json.load(f)
                    if not isinstance(thresholds_data, dict):
                        logging.warning("Corrupt {}, resetting to defaults".format(thresholds_file))
                        thresholds_data = {}
                    buy_threshold = thresholds_data.get("buy_threshold", 0.4)
                    if isinstance(buy_threshold, (int, float)) and buy_threshold > 0:
                        self.buy_threshold.set(float(buy_threshold))
                    else:
                        logging.warning("Invalid buy_threshold: {}, using default 0.4".format(buy_threshold))
                        self.buy_threshold.set(0.4)
                    zone_period = thresholds_data.get("zone_period", 14)
                    if isinstance(zone_period, (int, str)) and str(zone_period).strip() and int(zone_period) > 0:
                        self.zone_period = int(zone_period)
                    else:
                        logging.warning("Invalid zone_period: {}, using default 14".format(zone_period))
                        self.zone_period = 14
                    volume_level = thresholds_data.get("volume_level", 1.0)
                    if isinstance(volume_level, (int, float)) and 0 <= volume_level <= 1:
                        self.volume_level.set(float(volume_level))
                    else:
                        logging.warning("Invalid volume_level: {}, using default 1.0".format(volume_level))
                        self.volume_level.set(1.0)
                    invalid_stocks = thresholds_data.get("invalid_stocks", [])
                    if isinstance(invalid_stocks, list):
                        self.invalid_stocks.update([str(s) for s in invalid_stocks if isinstance(s, str) and s.strip()])
                    else:
                        logging.warning("Invalid invalid_stocks: {}, using empty set".format(invalid_stocks))
                        self.invalid_stocks = set()
                    supply_thresholds = thresholds_data.get("supply_thresholds", {})
                    demand_thresholds = thresholds_data.get("demand_thresholds", {})
                    threshold_zone_periods = thresholds_data.get("threshold_zone_periods", {})
                    manual_thresholds = thresholds_data.get("manual_thresholds", {})
                    if isinstance(supply_thresholds, dict) and isinstance(demand_thresholds, dict) and isinstance(threshold_zone_periods, dict):
                        for stock in self.stocks:
                            if stock in supply_thresholds and stock in demand_thresholds and stock in threshold_zone_periods:
                                if threshold_zone_periods[stock] == self.zone_period:
                                    self.supply_thresholds[stock] = float(supply_thresholds[stock]) if isinstance(supply_thresholds[stock], (int, float)) and float(supply_thresholds[stock]) > 0 else None
                                    self.demand_thresholds[stock] = float(demand_thresholds[stock]) if isinstance(demand_thresholds[stock], (int, float)) and float(demand_thresholds[stock]) > 0 else None
                                    self.threshold_zone_periods[stock] = self.zone_period
                    if isinstance(manual_thresholds, dict):
                        self.manual_thresholds = {
                            k: {
                                'target': float(v['target']) if v.get('target') and isinstance(v['target'], (int, float)) else None,
                                'stop': float(v['stop']) if v.get('stop') and isinstance(v['stop'], (int, float)) else None,
                                'period': int(v['period']) if v.get('period') and isinstance(v['period'], (int, str)) and str(v['period']).strip() else self.zone_period
                            } for k, v in manual_thresholds.items()
                        }
                        for stock in self.stocks:
                            if stock in manual_thresholds and manual_thresholds[stock].get('period') == self.zone_period:
                                if manual_thresholds[stock].get('target'):
                                    self.supply_thresholds[stock] = float(manual_thresholds[stock]['target'])
                                if manual_thresholds[stock].get('stop'):
                                    self.demand_thresholds[stock] = float(manual_thresholds[stock]['stop'])
                                self.threshold_zone_periods[stock] = self.zone_period
                                logging.debug("Loaded manual thresholds for {}: target=${:.2f}, stop=${:.2f}".format(stock, self.supply_thresholds.get(stock, 0), self.demand_thresholds.get(stock, 0)))
                    else:
                        logging.warning("Invalid manual_thresholds: {}, using empty dict".format(manual_thresholds))
                        self.manual_thresholds = {}
                    logging.info("Loaded settings from {}: buy_threshold={}, zone_period={}, volume_level={}, invalid_stocks={}, supply_thresholds={}, demand_thresholds={}, threshold_zone_periods={}, manual_thresholds={}".format(thresholds_file, self.buy_threshold.get(), self.zone_period, self.volume_level.get(), self.invalid_stocks, self.supply_thresholds, self.demand_thresholds, self.threshold_zone_periods, self.manual_thresholds))
                else:
                    logging.info("No {} found, using defaults".format(thresholds_file))
                    self.buy_threshold.set(0.4)
                    self.zone_period = 14
                    self.volume_level.set(1.0)
                    self.invalid_stocks = set()
                    self.supply_thresholds = {}
                    self.demand_thresholds = {}
                    self.threshold_zone_periods = {}
                    self.manual_thresholds = {}
            except Exception as e:
                logging.error("Error loading thresholds: {}".format(e))
                self.buy_threshold.set(0.4)
                self.zone_period = 14
                self.volume_level.set(1.0)
                self.invalid_stocks = set()
                self.supply_thresholds = {}
                self.demand_thresholds = {}
                self.threshold_zone_periods = {}
                self.manual_thresholds = {}
            for stock in self.stocks:
                if stock in self.supply_thresholds and stock in self.demand_thresholds and stock in self.threshold_zone_periods:
                    if self.threshold_zone_periods[stock] == self.zone_period and stock not in self.manual_thresholds:
                        self.manual_thresholds[stock] = {
                            'target': self.supply_thresholds[stock],
                            'stop': self.demand_thresholds[stock],
                            'period': self.zone_period
                        }
                        logging.debug("Backfilled manual_thresholds for {} from supply/demand: target=${:.2f}".format(stock, self.supply_thresholds[stock]))
            self.speech_engine = None
            if os.name == "nt":
                try:
                    import win32com.client
                    self.speech_engine = win32com.client.Dispatch("SAPI.SpVoice")
                    voices = self.speech_engine.GetVoices()
                    available_voices = [voice.GetDescription() for voice in voices]
                    logging.debug("Available SAPI voices: {}".format(available_voices))
                    if not available_voices:
                        logging.error("No SAPI voices available on this system")
                        error_msg = "No text-to-speech voices found. Voice feedback disabled. Check Control Panel > Speech Recognition > Text to Speech."
                        self.root.after(0, lambda: messagebox.showwarning("Warning", error_msg))
                    else:
                        selected_voice = None
                        for voice in voices:
                            if 'zira' in voice.GetDescription().lower():
                                selected_voice = voice
                                break
                        if selected_voice:
                            self.speech_engine.Voice = selected_voice
                            logging.info("Speech engine initialized with Zira voice")
                        else:
                            self.speech_engine.Voice = voices.Item(0)
                            logging.info("Speech engine initialized with default voice: {}".format(voices.Item(0).GetDescription()))
                        self.speech_engine.Volume = int(self.volume_level.get() * 100)
                        self.root.after(0, lambda: self.speak("Initialized successfully"))
                except ImportError as e:
                    error_msg = "Voice feedback disabled. Install pywin32 with 'pip install pywin32' and ensure Windows SAPI is configured."
                    logging.error("Failed to import win32com.client: {}".format(e))
                    self.root.after(0, lambda: messagebox.showwarning("Warning", error_msg))
                except Exception as e:
                    error_msg = "Voice feedback disabled due to error: {}. Check Windows SAPI settings in Control Panel.".format(str(e))
                    logging.error("Speech engine initialization failed: {}".format(e))
                    self.root.after(0, lambda: messagebox.showwarning("Warning", error_msg))
            else:
                logging.info("Speech engine skipped on non-Windows platform")
                self.speech_engine = None
            logging.debug("Setting up GUI")
            style = ttk.Style()
            style.configure("Main.TFrame", background="white", borderwidth=2, relief="solid")
            style.configure("Custom.Treeview", background="white", foreground="black", fieldbackground="white", borderwidth=2, relief="solid", rowheight=20)
            style.configure("Custom.Treeview.Heading", font=("Arial", 10, "bold"), borderwidth=1, relief="solid")
            style.configure("Buy.TButton", background="#90EE90", foreground="black", borderwidth=2, relief="solid")
            style.configure("Sell.TButton", background="#FF6347", foreground="black", borderwidth=2, relief="solid")
            style.configure("Auto.TButton", background="gray", foreground="black", borderwidth=2, relief="solid")
            style.configure("Reset.TButton", background="yellow", foreground="black", borderwidth=2, relief="solid")
            style.configure("Status.TLabel", font=("Arial", 10), foreground="black")
            style.configure("Signal.Row", font=("Arial", 10, "bold"))
            style.configure("signal_row", background="#FFFFFF", font=("Arial", 10, "bold"))
            style.configure("TNotebook.Tab", font=("Arial", 10))
            style.map("TNotebook.Tab", font=[("selected", ("Arial", 10, "bold"))])
            style.configure("Portfolio.TLabel", font=("Arial", 12, "bold"), foreground="#00008B")
            style.configure("Portfolio.TLabelframe", font=("Arial", 10, "bold"))
            style.configure("TotalPL.TLabel", font=("Arial", 10, "bold"))
            self.time_label = ttk.Label(self.root, text="", font=("Arial", 14), foreground="black", borderwidth=2, relief="solid", anchor="center")
            self.time_label.pack(side="top", fill="x", padx=5, pady=5)
            self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="determinate")
            self.progress_bar.pack(side="top", pady=2)
            def update_time():
                self.time_label.config(text=datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z"))
                after_id = self.root.after(1000, update_time)
                self.after_ids.append(after_id)
            update_time()
            def update_data_button_label():
                if self.data_fetch_manual_override:
                    logging.debug("Data fetch manually enabled, skipping market check")
                    self.root.after(0, lambda: self.refresh_data_button.config(text="Data On"))
                    return
                is_open = self.is_market_open()
                logging.debug("Market open check: {}".format(is_open))
                if is_open:
                    self.data_fetch_enabled = True
                    self.root.after(0, lambda: self.refresh_data_button.config(text="Data On"))
                else:
                    self.data_fetch_enabled = False
                    self.root.after(0, lambda: self.refresh_data_button.config(text="Data Off"))
                after_id = self.root.after(60000, update_data_button_label)
                self.after_ids.append(after_id)
            self.top_frame = ttk.Frame(self.root, style="Main.TFrame")
            self.top_frame.pack(side="top", fill="x", padx=5, pady=5)
            self.portfolio_summary = ttk.LabelFrame(self.top_frame, text="Portfolio Summary", padding=10, borderwidth=2, relief="solid", style="Portfolio.TLabelframe")
            self.portfolio_summary.pack(side="left", fill="y", padx=5)
            summary_inner_frame = ttk.Frame(self.portfolio_summary)
            summary_inner_frame.pack(fill="y", expand=True)
            self.cash_label = ttk.Label(summary_inner_frame, text="Cash: ${:.2f}".format(self.base_cash), foreground="#00008B", style="Portfolio.TLabel")
            self.cash_label.pack(anchor="w", pady=2)
            self.stocks_value_label = ttk.Label(summary_inner_frame, text="Stocks Value: $0.00", foreground="#00008B", style="Portfolio.TLabel")
            self.stocks_value_label.pack(anchor="w", pady=2)
            self.total_value_label = ttk.Label(self.portfolio_summary, text="Total Value: $0.00", foreground="#00008B", style="Portfolio.TLabel")
            self.total_value_label.pack(anchor="w", pady=2)
            self.auto_trade_button = ttk.Button(summary_inner_frame, text="Using Manual", style="Auto.TButton", command=self.toggle_auto_trading)
            self.auto_trade_button.pack(anchor="w", pady=5)
            ttk.Button(summary_inner_frame, text="Run Backtest", style="Reset.TButton", command=self.confirm_backtest).pack(anchor="w", pady=5)
            self.refresh_data_button = ttk.Button(summary_inner_frame, text="Data Off", style="Reset.TButton", command=self.manual_refresh_data)
            self.refresh_data_button.pack(anchor="w", pady=5)
            ttk.Button(summary_inner_frame, text="Toggle Day/Swing", style="Reset.TButton", command=self.toggle_trading_mode).pack(anchor="w", pady=5)
            ttk.Button(summary_inner_frame, text="Refresh Screener", style="Reset.TButton", command=self.refresh_screener).pack(anchor="w", pady=5)
            self.portfolio_frame = ttk.LabelFrame(self.top_frame, text="Portfolio", padding=10, borderwidth=2, relief="solid", style="Portfolio.TLabelframe")
            self.portfolio_frame.pack(side="right", fill="y", padx=5)
            columns = ("Stock", "Shares", "Cost", "Price", "Target", "Stop Loss", "P/L", "P/L %")
            self.portfolio_tree = ttk.Treeview(self.portfolio_frame, columns=columns, show="headings", height=5, style="Custom.Treeview")
            for col in columns:
                self.portfolio_tree.heading(col, text=col, anchor="center")
                if col in ["Shares", "Cost"]:
                    self.portfolio_tree.column(col, width=60, anchor="center")  # Shrunk from 80
                elif col in ["P/L", "P/L %", "Target", "Stop Loss"]:
                    self.portfolio_tree.column(col, width=70, anchor="center")
                else:
                    self.portfolio_tree.column(col, width=100, anchor="center")
            self.portfolio_tree.pack(fill="x")
            self.portfolio_tree.tag_configure('profit', background='lightgreen', foreground='black')
            self.portfolio_tree.tag_configure('loss', background='lightcoral', foreground='black')
            self.portfolio_tree.bind("<Double-1>", self.on_portfolio_double_click)
            self.total_pl_label = ttk.Label(self.portfolio_frame, text="Total P/L: $0.00", style="TotalPL.TLabel")
            self.total_pl_label.pack(anchor="e", padx=(0, 80), pady=2)
            self.entry_frame = ttk.Frame(self.portfolio_frame)
            # Row 1: Target, Stop Loss, and Zone Period
            target_stop_zone_frame = ttk.Frame(self.entry_frame)
            target_stop_zone_frame.pack(fill="x", padx=5, pady=2)
            # Target and Stop Loss
            ttk.Label(target_stop_zone_frame, text="Target:").pack(side="left", padx=2)
            self.target_entry = ttk.Entry(target_stop_zone_frame, width=10)
            self.target_entry.pack(side="left", padx=2)
            ttk.Label(target_stop_zone_frame, text="Stop Loss:").pack(side="left", padx=2)
            self.stop_loss_entry = ttk.Entry(target_stop_zone_frame, width=10)
            self.stop_loss_entry.pack(side="left", padx=2)
            ttk.Button(target_stop_zone_frame, text="Apply", command=self.apply_target_stop_loss).pack(side="left", padx=2)
            # Zone Period
            ttk.Label(target_stop_zone_frame, text="Zone Period (bars):").pack(side="left", padx=10)
            self.zone_period_entry = ttk.Entry(target_stop_zone_frame, width=5)
            self.zone_period_entry.delete(0, tk.END)
            self.zone_period_entry.insert(0, str(self.zone_period))
            self.zone_period_entry.pack(side="left", padx=2)
            ttk.Button(target_stop_zone_frame, text="Apply Zone Period", style="Reset.TButton", command=self.apply_zone_period).pack(side="left", padx=2)
            # Row 2: Volume and other buttons
            controls_frame = ttk.Frame(self.entry_frame)
            controls_frame.pack(fill="x", padx=5, pady=2)
            # Volume slider
            ttk.Label(controls_frame, text="Volume:").pack(side="left", padx=2)
            self.volume_scale = ttk.Scale(controls_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.volume_level, command=self.update_volume)
            self.volume_scale.pack(side="left", padx=2)
            # Other buttons (Light/Dark, Refresh Cash, Buy Threshold)
            ttk.Button(controls_frame, text="Light/Dark", command=self.toggle_theme).pack(side="left", padx=2)
            ttk.Button(controls_frame, text="Refresh Cash", command=self.refresh_cash).pack(side="left", padx=2)
            ttk.Label(controls_frame, text="Buy Threshold:").pack(side="left", padx=2)
            self.buy_threshold_entry = ttk.Entry(controls_frame, width=5)
            self.buy_threshold_entry.insert(0, str(self.buy_threshold.get()))
            self.buy_threshold_entry.pack(side="left", padx=2)
            ttk.Button(controls_frame, text="Apply Threshold", style="Reset.TButton", command=self.apply_threshold).pack(side="left", padx=2)
            self.entry_frame.pack(fill="x", pady=5)
            self.trade_frame = ttk.Frame(self.root, style="Main.TFrame")
            self.trade_frame.pack(side="top", fill="x", padx=5, pady=5)
            ttk.Label(self.trade_frame, text="Interval:").pack(side="left")
            self.interval_combo = ttk.Combobox(self.trade_frame, textvariable=self.interval_var, values=["3min", "4hour"], state="readonly", width=8)
            self.interval_combo.pack(side="left", padx=5)
            self.interval_combo.bind("<<ComboboxSelected>>", lambda e: [self.data_cache.clear(), self.update_data(first_fetch=True)])
            ttk.Label(self.trade_frame, text="Shares:").pack(side="left")
            self.shares_entry = ttk.Entry(self.trade_frame, width=10)
            self.shares_entry.insert(0, "5")
            self.shares_entry.pack(side="left", padx=5)
            ttk.Button(self.trade_frame, text="Buy", style="Buy.TButton", command=self.buy_stock).pack(side="left", padx=5)
            ttk.Button(self.trade_frame, text="Sell", style="Sell.TButton", command=self.sell_stock).pack(side="left", padx=5)
            ttk.Button(self.trade_frame, text="Sell All", style="Sell.TButton", command=self.sell_all_stocks).pack(side="left", padx=5)
            ttk.Label(self.trade_frame, text="Add Stock:").pack(side="left", padx=5)
            self.add_stock_entry = ttk.Entry(self.trade_frame, width=10)
            self.add_stock_entry.pack(side="left", padx=5)
            ttk.Button(self.trade_frame, text="Add", command=self.add_custom_stock).pack(side="left", padx=5)
            ttk.Button(self.trade_frame, text="Remove", style="Reset.TButton", command=lambda: self.remove_stock(self.current_stock)).pack(side="left", padx=5)
            ttk.Button(self.trade_frame, text="Toggle All Indicators", command=self.toggle_all_indicators).pack(side="left", padx=5)
            self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
            self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.main_frame.rowconfigure(0, weight=2)
            self.main_frame.rowconfigure(1, weight=1)
            self.main_frame.columnconfigure(0, weight=1)
            self.notebook = ttk.Notebook(self.main_frame)
            self.notebook.grid(row=0, column=0, sticky="nsew")
            self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
            self.history_container = ttk.Frame(self.main_frame)
            self.history_container.grid(row=1, column=0, sticky="nsew")
            self.history_container.rowconfigure(0, weight=1)
            self.history_container.columnconfigure(0, weight=1)
            self.history_frame = ttk.LabelFrame(self.history_container, text="All Transactions", padding=10, borderwidth=2, relief="solid")
            self.history_frame.grid(row=0, column=0, sticky="nsew")
            columns = ("Stock", "Action", "Shares", "Price", "Time")
            self.history_tree = ttk.Treeview(self.history_frame, columns=columns, show="headings", style="Custom.Treeview", height=4)
            for col in columns:
                self.history_tree.heading(col, text=col, anchor="center")
                self.history_tree.column(col, width=150 if col == "Time" else 100, anchor="center")
            self.history_tree.tag_configure('buy', background='lightgreen', foreground='black')
            self.history_tree.tag_configure('sell', background='lightcoral', foreground='black')
            scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.history_tree.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.history_tree.configure(yscrollcommand=scrollbar.set)
            self.history_tree.grid(row=0, column=0, sticky="nsew")
            self.history_frame.columnconfigure(0, weight=1)
            self.history_frame.rowconfigure(0, weight=1)
            self.resize_handle = ttk.Label(self.history_container, text="↕", cursor="size_ns")
            self.resize_handle.grid(row=1, column=0, sticky="ew", pady=(0, 5))
            self.resize_start_y = None
            self.resize_start_height = None
            def start_resize(event):
                self.resize_start_y = event.y_root
                self.resize_start_height = self.history_container.winfo_height()
            def do_resize(event):
                try:
                    if self.resize_start_y is None:
                        return
                    delta = event.y_root - self.resize_start_y
                    new_height = max(100, min(self.resize_start_height + delta, self.main_frame.winfo_height() - 100))
                    self.history_container.configure(height=new_height)
                    self.history_frame.configure(height=new_height - 20)
                    self.history_tree.configure(height=int((new_height - 20) // 20))
                except Exception as e:
                    logging.error(f"Error resizing history frame: {e}")
            def stop_resize(event):
                self.resize_start_y = None
                self.resize_start_height = None
            self.resize_handle.bind("<Button-1>", start_resize)
            self.resize_handle.bind("<B1-Motion>", do_resize)
            self.resize_handle.bind("<ButtonRelease-1>", stop_resize)
            self.version_label = ttk.Label(self.main_frame, text="Version: {}".format(SCRIPT_VERSION), font=("Arial", 10), foreground="black")
            self.version_label.grid(row=2, column=0, sticky="se", padx=5, pady=5)
            try:
                manual_purchases_file = os.path.join(r"C:\Users\dad\StockApp", "manual_purchases.json")
                if os.path.exists(manual_purchases_file):
                    with open(manual_purchases_file, "r") as f:
                        self.manual_purchases = set(json.load(f))
                    logging.info("Loaded manual purchases: {}".format(self.manual_purchases))
                else:
                    logging.info("No {} found, initializing empty".format(manual_purchases_file))
                    self.manual_purchases = set()
            except Exception as e:
                logging.error("Error loading manual purchases: {}".format(e))
                self.manual_purchases = set()
            # Post-load indicator visibility tweaks: ensure global vars
            self.indicators_list = [
                "mfi", "ema13" if self.interval_var.get() == "3min" else "sma13", "macd", "demand_zone",
                "stochastic", "cci", "obv", "vwap", "adx", "atr", "momentum",
                "stochastic_rsi", "williams_%r", "bollinger_bands"
            ]
            for indicator in self.indicators_list:
                if indicator not in self.indicator_visibility:
                    self.indicator_visibility[indicator] = tk.BooleanVar(value=True)
            for stock in self.stocks[:]:
                for indicator in self.indicators_list:
                    indicator_key = "{}_{}".format(stock, indicator)
                    if indicator_key not in self.indicator_visibility:
                        self.indicator_visibility[indicator_key] = tk.BooleanVar(value=self.indicator_visibility[indicator].get())
            # Load toggles after stock tabs to catch global indicators
            toggles_file = os.path.join(r"C:\Users\dad\StockApp", "toggles.json")
            if os.path.exists(toggles_file):
                try:
                    with open(toggles_file, "r") as f:
                        toggles_data = json.load(f)
                    group_data = toggles_data.get("group_visibility", {})
                    for group, value in group_data.items():
                        if group in self.group_visibility and isinstance(value, bool):
                            self.group_visibility[group].set(value)
                    indicator_data = toggles_data.get("indicator_visibility", {})
                    for indicator_key, value in indicator_data.items():
                        if indicator_key in self.indicators_list and isinstance(value, bool):
                            self.indicator_visibility[indicator_key].set(value)
                            # Sync per-stock keys
                            for stock in self.stocks:
                                if stock in ["***", "Backtest"]:
                                    continue
                                stock_key = "{}_{}".format(stock, indicator_key)
                                if stock_key in self.indicator_visibility:
                                    self.indicator_visibility[stock_key].set(value)
                    logging.info("Loaded global toggle states from {}".format(toggles_file))
                except Exception as e:
                    logging.error("Error loading toggles: {}".format(e))
            # Parallel fetch for held stocks with staleness check
            interval = self.interval_var.get()  # Get interval in main thread
            gui_update_queue = queue.Queue()  # Queue for GUI updates
            def fetch_stock_data(stock):
                if stock in ["***", "Backtest"]:
                    return
                cache_key = "{}_{}".format(stock, interval)
                cache_file = os.path.join(r"C:\Users\dad\StockApp", "{}_{}.json".format(cache_key, self.zone_period))
                df = None
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r") as f:
                            cached = json.load(f)
                        if cached["timestamp"] > (datetime.now().timestamp() - 3600):  # 1hr staleness threshold
                            df = pd.DataFrame.from_dict(cached["data"], orient="index")
                            df.index = pd.to_datetime(df.index)
                            df.index.name = "date"
                            logging.debug("Loaded cached data for {} period {}: {} rows".format(stock, self.zone_period, len(df)))
                        else:
                            logging.debug("Stale cache for {}, fetching fresh".format(stock))
                            os.remove(cache_file)  # Delete stale cache
                    except Exception as e:
                        logging.warning("Error loading cache for {} period {}: {}".format(stock, self.zone_period, e))
                if df is None or df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                    logging.debug("Fetching fresh data for {}".format(stock))
                    try:
                        df = self.fetch_data(stock, interval, force_fetch=True)
                        if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                            logging.warning("No valid data for {} in startup".format(stock))
                            return
                        df = self.calculate_indicators(df, stock)
                    except Exception as e:
                        logging.error("Failed to fetch data for {}: {}".format(stock, e))
                        return
                with self.cache_lock:
                    self.data_cache[cache_key] = df
                # Queue GUI updates instead of calling after() in thread
                gui_update_queue.put(lambda s=stock: self.create_tab_for_stock(s))
                gui_update_queue.put(lambda s=stock: self.update_tab_signal(s))
                logging.debug("Processed data for {}: {} rows".format(stock, len(df)))
            # Process GUI updates in main thread
            def process_gui_updates():
                try:
                    while not gui_update_queue.empty():
                        func = gui_update_queue.get_nowait()
                        func()
                        gui_update_queue.task_done()
                except queue.Empty:
                    pass
                except Exception as e:
                    logging.error(f"Error processing GUI updates: {e}")
                self.root.after(100, process_gui_updates)
            self.root.after(100, process_gui_updates)
            threads = []
            for stock in held_stocks:
                thread = threading.Thread(target=fetch_stock_data, args=(stock,), daemon=True)
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join(timeout=10.0)
            self.load_transaction_history()
            self.update_history_table()
            self.update_portfolio_table()
            def start_fetch_thread():
                fetch_thread = threading.Thread(target=self.async_fetch_data, daemon=True)
                self.threads.append(fetch_thread)
                fetch_thread.start()
            self.root.after(1000, start_fetch_thread)
            self.root.after(1000, self.refresh_screener)
            self.root.after(0, update_data_button_label)
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.after(0, lambda: self.status_label.config(text="Initialization complete"))
            logging.info("Initialization completed successfully")
            self.theme_var = tk.StringVar(value="light")
            self.configure_styles()
            self.apply_theme()
        except Exception as e:
            logging.exception("Initialization failed with full traceback: {}".format(e))
            self.root.after(0, lambda: messagebox.showerror("Initialization Error", "Failed to start application: {}".format(str(e))))
            self.root.destroy()
            
    def configure_styles(self):
        style = ttk.Style()
        # Light theme
        style.configure("Light.Main.TFrame", background="white", borderwidth=2, relief="solid")
        style.configure("Light.Custom.Treeview", background="white", foreground="black", fieldbackground="white", borderwidth=2, relief="solid", rowheight=20)
        style.configure("Light.Custom.Treeview.Heading", font=("Arial", 10, "bold"), borderwidth=1, relief="solid")
        style.configure("Light.Buy.TButton", background="#90EE90", foreground="black", borderwidth=2, relief="solid")
        style.configure("Light.Sell.TButton", background="#FF6347", foreground="black", borderwidth=2, relief="solid")
        style.configure("Light.Auto.TButton", background="gray", foreground="black", borderwidth=2, relief="solid")
        style.configure("Light.Reset.TButton", background="yellow", foreground="black", borderwidth=2, relief="solid")
        style.configure("Light.Status.TLabel", font=("Arial", 10), foreground="black")
        style.configure("Light.Signal.Row", font=("Arial", 10, "bold"))
        style.configure("Light.signal_row", background="#FFFFFF", font=("Arial", 10, "bold"))
        style.configure("Light.TNotebook.Tab", font=("Arial", 10))
        style.map("Light.TNotebook.Tab", font=[("selected", ("Arial", 10, "bold"))])
        style.configure("Light.Portfolio.TLabel", font=("Arial", 12, "bold"), foreground="#00008B")
        style.configure("Light.Portfolio.TLabelframe", font=("Arial", 10, "bold"))
        style.configure("Light.TotalPL.TLabel", font=("Arial", 10, "bold"))
        # Dark theme
        style.configure("Dark.Main.TFrame", background="gray20", borderwidth=2, relief="solid")
        style.configure("Dark.Custom.Treeview", background="gray20", foreground="white", fieldbackground="gray20", borderwidth=2, relief="solid", rowheight=20)
        style.configure("Dark.Custom.Treeview.Heading", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", background="gray30", foreground="white")
        style.configure("Dark.Buy.TButton", background="#90EE90", foreground="black", borderwidth=2, relief="solid")
        style.configure("Dark.Sell.TButton", background="#FF6347", foreground="black", borderwidth=2, relief="solid")
        style.configure("Dark.Auto.TButton", background="gray", foreground="white", borderwidth=2, relief="solid")
        style.configure("Dark.Reset.TButton", background="yellow", foreground="black", borderwidth=2, relief="solid")
        style.configure("Dark.Status.TLabel", font=("Arial", 10), foreground="white")
        style.configure("Dark.Signal.Row", font=("Arial", 10, "bold"), foreground="white")
        style.configure("Dark.signal_row", background="gray20", font=("Arial", 10, "bold"), foreground="white")
        style.configure("Dark.TNotebook.Tab", font=("Arial", 10, "bold"), background="gray30", foreground="white")
        style.map("Dark.TNotebook.Tab", font=[("selected", ("Arial", 10, "bold"))], background=[("selected", "gray40")])
        style.configure("Dark.Portfolio.TLabel", font=("Arial", 12, "bold"), foreground="cyan")
        style.configure("Dark.Portfolio.TLabelframe", font=("Arial", 10, "bold"), background="gray20", foreground="white")
        style.configure("Dark.TotalPL.TLabel", font=("Arial", 10, "bold"), foreground="white")

    def apply_theme(self):
        theme = self.theme_var.get()
        prefix = "Light." if theme == "light" else "Dark."
        style = ttk.Style()
        style.configure("Main.TFrame", **style.configure(f"{prefix}Main.TFrame"))
        style.configure("Custom.Treeview", **style.configure(f"{prefix}Custom.Treeview"))
        style.configure("Custom.Treeview.Heading", **style.configure(f"{prefix}Custom.Treeview.Heading"))
        style.configure("Buy.TButton", **style.configure(f"{prefix}Buy.TButton"))
        style.configure("Sell.TButton", **style.configure(f"{prefix}Sell.TButton"))
        style.configure("Auto.TButton", **style.configure(f"{prefix}Auto.TButton"))
        style.configure("Reset.TButton", **style.configure(f"{prefix}Reset.TButton"))
        style.configure("Status.TLabel", **style.configure(f"{prefix}Status.TLabel"))
        style.configure("Signal.Row", **style.configure(f"{prefix}Signal.Row"))
        style.configure("signal_row", **style.configure(f"{prefix}signal_row"))
        style.configure("TNotebook.Tab", **style.configure(f"{prefix}TNotebook.Tab"))
        style.map("TNotebook.Tab", **style.map(f"{prefix}TNotebook.Tab"))
        style.configure("Portfolio.TLabel", **style.configure(f"{prefix}Portfolio.TLabel"))
        style.configure("Portfolio.TLabelframe", **style.configure(f"{prefix}Portfolio.TLabelframe"))
        style.configure("TotalPL.TLabel", **style.configure(f"{prefix}TotalPL.TLabel"))
        self.root.configure(bg="white" if theme == "light" else "gray20")
        # Safe frame updates
        for frame in ['main_frame', 'trade_frame', 'portfolio_frame', 'portfolio_summary', 'history_frame']:
            if hasattr(self, frame):
                style_name = f"{prefix}Main.TFrame" if frame in ['main_frame', 'trade_frame'] else f"{prefix}Portfolio.TLabelframe"
                getattr(self, frame).configure(style=style_name)
        # Update all root children
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Label):
                child.configure(style=f"{prefix}Status.TLabel")
            elif isinstance(child, ttk.Frame):
                child.configure(style=f"{prefix}Main.TFrame")
            elif isinstance(child, ttk.LabelFrame):
                child.configure(style=f"{prefix}Portfolio.TLabelframe")
            elif isinstance(child, ttk.Treeview):
                child.configure(style=f"{prefix}Custom.Treeview")
        # Update notebook tabs
        for tab in self.tabs.values():
            if isinstance(tab, ttk.Frame):
                tab.configure(style=f"{prefix}Main.TFrame")
            for child in tab.winfo_children():
                if isinstance(child, ttk.Label):
                    child.configure(style=f"{prefix}Status.TLabel")
                elif isinstance(child, ttk.Frame):
                    child.configure(style=f"{prefix}Main.TFrame")
                elif isinstance(child, ttk.LabelFrame):
                    child.configure(style=f"{prefix}Portfolio.TLabelframe")
                elif isinstance(child, ttk.Treeview):
                    child.configure(style=f"{prefix}Custom.Treeview")
        logging.info(f"Applied theme: {theme}")

    def toggle_theme(self):
        theme = "dark" if self.theme_var.get() == "light" else "light"
        self.theme_var.set(theme)
        self.apply_theme()
        logging.info(f"Toggled theme to {theme}")
        if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
            self.speak(f"Theme switched to {theme}")
        beep()
        
    def refresh_cash(self):
        try:
            from tkinter import simpledialog
            cash_input = simpledialog.askstring("Refresh Cash", "Enter new cash amount:", initialvalue=str(self.base_cash))
            if cash_input is not None:
                new_cash = float(cash_input)
                if new_cash >= 0:
                    self.base_cash = new_cash
                    self.cash_label.config(text=f"Cash: ${self.base_cash:.2f}")
                    self.save_portfolio()  # Update saved portfolio with new cash
                    logging.info(f"Refreshed cash to ${new_cash:.2f}")
                    self.status_label.config(text=f"Cash refreshed to ${new_cash:.2f}")
                    if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                        self.speak(f"Cash refreshed to {new_cash:.2f} dollars")
                    beep()
                else:
                    messagebox.showerror("Error", "Cash amount must be non-negative")
        except ValueError:
            messagebox.showerror("Error", "Invalid cash amount")
        except Exception as e:
            logging.error(f"Error refreshing cash: {e}")
            messagebox.showerror("Error", "Failed to refresh cash")     
          
    # Snippet 189: Enhanced update_data with post-8PM ET cache-only mode (replace existing method)
    def update_data(self, first_fetch=False):
        logging.debug(f"Updating data, first_fetch={first_fetch}")
        try:
            import queue
            current_time = datetime.now().timestamp()
            now_et = datetime.now(pytz.timezone("America/New_York"))
            after_hours_close = now_et.replace(hour=20, minute=0, second=0, microsecond=0)
            force_cache_only = now_et > after_hours_close  # After 8 PM ET: cache only
            if not self.is_market_open() and not self.data_fetch_manual_override and not force_cache_only:
                if not self.market_closed_fetched:
                    self.update_stocks()
                    self.market_closed_fetched = True
                self.status_label.config(text="Market closed, using cached data")
                logging.info("Market closed, using cached data")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Market closed, using cached data")
                for stock in self.stocks:
                    if stock in ["***", "Backtest"]:
                        continue
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    df = self.data_cache.get(cache_key, pd.DataFrame())
                    if not df.empty and 'Close' in df.columns and not df['Close'].isna().all():
                        df = self.calculate_indicators(df, stock)
                        self.data_cache[cache_key] = df
                        if stock not in self.tabs:
                            self.create_tab_for_stock(stock, placeholder=False)
                        self.update_tab_signal(stock)
                        price = self.get_live_price(stock) or df['Close'].iloc[-1]
                        if price and 'supply_zone' in df.columns and not pd.isna(df["supply_zone"].iloc[-1]):
                            supply_zone = df["supply_zone"].iloc[-1]
                            if price >= supply_zone * 0.98:
                                if stock not in self.highest_price:
                                    self.highest_price[stock] = price
                                elif price > self.highest_price[stock]:
                                    self.highest_price[stock] = price
                                self.demand_thresholds[stock] = self.highest_price[stock] * 0.98
                                logging.debug(f"Updated trailing stop for {stock}: price=${price:.4f}, highest_price=${self.highest_price[stock]:.4f}, trailing_stop=${self.demand_thresholds[stock]:.4f}")
                self.update_portfolio_table()
                self.update_tab_labels()
                thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds.json")
                thresholds_data = {
                    "buy_threshold": self.buy_threshold.get(),
                    "zone_period": self.zone_period,
                    "volume_level": self.volume_level.get(),
                    "invalid_stocks": list(getattr(self, 'invalid_stocks', set())),
                    "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items()},
                    "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items()},
                    "threshold_zone_periods": self.threshold_zone_periods,
                    "highest_price": {k: float(v) for k, v in getattr(self, 'highest_price', {}).items()}
                }
                try:
                    os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                    with open(thresholds_file, "w") as f:
                        json.dump(thresholds_data, f, indent=2)
                    logging.info(f"Saved thresholds to {thresholds_file}")
                except Exception as e:
                    logging.error(f"Error saving thresholds: {e}")
                after_id = self.root.after(60000, lambda: self.update_data(first_fetch=False))
                self.after_ids.append(after_id)
                return
            if current_time < self.next_refresh_time and not first_fetch:
                after_id = self.root.after(1000, lambda: self.update_data(first_fetch=False))
                self.after_ids.append(after_id)
                return
            self.next_refresh_time = current_time + 300
            self.progress_bar.start()
            gui_update_queue = queue.Queue()
            def process_gui_updates():
                try:
                    while not gui_update_queue.empty():
                        func = gui_update_queue.get_nowait()
                        func()
                        gui_update_queue.task_done()
                except queue.Empty:
                    pass
                except Exception as e:
                    logging.error(f"Error processing GUI updates: {e}")
                if (self.is_market_open() or self.data_fetch_manual_override) and not force_cache_only:
                    self.root.after(500, process_gui_updates)
            self.root.after(500, process_gui_updates)
            def update_thread():
                try:
                    self._update_data_thread(first_fetch, gui_update_queue, force_cache_only)
                except Exception as e:
                    logging.error(f"Error in update thread: {e}")
                    gui_update_queue.put(lambda: self.status_label.config(text="Error updating data"))
                    gui_update_queue.put(lambda: self.speak("Error updating data"))
                    gui_update_queue.put(beep)
            thread = threading.Thread(target=update_thread, daemon=True)
            self.threads.append(thread)
            thread.start()
            after_id = self.root.after(60000, lambda: self.update_data(first_fetch=False))
            self.after_ids.append(after_id)
        except Exception as e:
            logging.error(f"Error updating data: {e}")
            self.status_label.config(text="Error updating data")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error updating data")
            beep()        
            
    def update_volume(self, *args):
        logging.debug("Updating volume")
        try:
            volume = self.volume_level.get()
            if hasattr(self, 'speech_engine') and self.speech_engine:
                self.speech_engine.Volume = int(volume * 100)
                logging.info(f"Set speech volume to {volume:.2f}")
            thresholds_file = os.path.join(os.getcwd(), "thresholds.json")
            try:
                thresholds_data = {}
                if os.path.exists(thresholds_file):
                    with open(thresholds_file, "r") as f:
                        thresholds_data = json.load(f)
                thresholds_data["volume_level"] = volume
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info(f"Saved volume level {volume:.2f} to {thresholds_file}")
            except Exception as e:
                logging.error(f"Error saving volume level: {e}")
        except Exception as e:
            logging.error(f"Error updating volume: {e}")
            self.status_label.config(text="Error updating volume")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error updating volume")		
				
    def toggle_mute(self):
        logging.debug(f"Toggling mute: {self.is_muted.get()}")
        try:
            if self.is_muted.get():
                logging.info("Voice muted")
                self.status_label.config(text="Voice muted")
                if hasattr(self, 'speech_engine') and self.speech_engine:
                    self.speak("Voice muted")
            else:
                logging.info("Voice unmuted")
                self.status_label.config(text="Voice unmuted")
                if hasattr(self, 'speech_engine') and self.speech_engine:
                    self.speak("Voice unmuted")
            beep()
        except Exception as e:
            logging.error(f"Error toggling mute: {e}")
            self.status_label.config(text="Error toggling mute")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error toggling mute")
            beep()	
			
    # Snippet 9: Fix buy_threshold override to respect user input and saved settings (replace apply_threshold method)
    def apply_threshold(self):
        logging.debug("Applying buy threshold")
        try:
            threshold_str = self.buy_threshold_entry.get().strip()
            try:
                threshold = float(threshold_str)
                if not 0 <= threshold <= 1:
                    raise ValueError("Threshold out of range")
            except ValueError:
                logging.warning("Invalid buy threshold: {}".format(threshold_str))
                self.status_label.config(text="Invalid buy threshold (0-1)")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Invalid buy threshold, must be between 0 and 1")
                beep()
                return
            if threshold == self.buy_threshold.get():
                logging.debug("Buy threshold unchanged: {}".format(threshold))
                self.status_label.config(text="Buy threshold unchanged")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Buy threshold unchanged")
                beep()
                return
            self.buy_threshold.set(threshold)
            # Save to thresholds.json
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds_{}.json".format(self.zone_period))
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items() if v is not None},
                "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items() if v is not None},
                "threshold_zone_periods": self.threshold_zone_periods,
                "manual_thresholds": {k: {sk: float(sv) if isinstance(sv, (int, float)) else sv for sk, sv in v.items()} for k, v in self.manual_thresholds.items()},
                "highest_price": {k: float(v) for k, v in getattr(self, 'highest_price', {}).items()}
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info("Saved buy threshold {} to {}".format(threshold, thresholds_file))
            except Exception as e:
                logging.error("Error saving buy threshold: {}".format(e))
            self.status_label.config(text="Buy threshold updated to {:.2f}".format(threshold))
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Buy threshold updated to {:.2f}".format(threshold))
            beep()
            # Trigger data update to apply new threshold
            self.data_cache.clear()
            self.update_data(first_fetch=True)
        except Exception as e:
            logging.error("Error applying buy threshold: {}".format(e))
            self.status_label.config(text="Error applying buy threshold")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error applying buy threshold")
            beep()
				
# Snippet 48: Full apply_zone_period with market closed skip and forced processing
    def apply_zone_period(self):
        import numpy as np  # Local import for NaN/inf handling
        logging.debug("Applying zone period")
        try:
            new_zone_period = self.zone_period_entry.get().strip()
            try:
                new_zone_period = int(new_zone_period)
                if new_zone_period <= 0:
                    raise ValueError("Zone period must be positive")
            except ValueError as e:
                logging.warning(f"Invalid zone period input: {new_zone_period}")
                self.status_label.config(text="Invalid zone period")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Invalid zone period")
                beep()
                return
            logging.debug(f"Zone period input: {new_zone_period}")
            # Save current period's thresholds and cache
            old_zone_period = self.zone_period
            if old_zone_period != new_zone_period:
                thresholds_file = os.path.join(r"C:\Users\dad\StockApp", f"thresholds_{old_zone_period}.json")
                thresholds_data = {
                    "buy_threshold": self.buy_threshold.get(),
                    "zone_period": old_zone_period,
                    "volume_level": self.volume_level.get(),
                    "invalid_stocks": list(self.invalid_stocks),
                    "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items() if v is not None},
                    "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items() if v is not None},
                    "threshold_zone_periods": self.threshold_zone_periods,
                    "manual_thresholds": {k: {sk: float(sv) if isinstance(sv, (int, float)) else sv for sk, sv in v.items()} for k, v in self.manual_thresholds.items()}
                }
                try:
                    os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                    with open(thresholds_file, "w") as f:
                        json.dump(thresholds_data, f, indent=2)
                    logging.info(f"Saved thresholds for period {old_zone_period} to {thresholds_file}")
                except Exception as e:
                    logging.error(f"Error saving thresholds for period {old_zone_period}: {e}")
                # Save current cache for each stock with JSON fixes
                for stock in self.stocks:
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    if cache_key in self.data_cache:
                        cache_file = os.path.join(r"C:\Users\dad\StockApp", f"{cache_key}_{old_zone_period}.json")
                        df = self.data_cache[cache_key]
                        df_to_save = df.copy()
                        df_to_save.index = df_to_save.index.astype(str)
                        df_to_save = df_to_save.replace({np.nan: None, np.inf: None, -np.inf: None})
                        try:
                            with open(cache_file, "w") as f:
                                json.dump({
                                    "timestamp": datetime.now().timestamp(),
                                    "data": df_to_save.to_dict(orient="index")
                                }, f, indent=2)
                            logging.debug(f"Saved cache for {stock} period {old_zone_period} to {cache_file}")
                        except Exception as e:
                            logging.error(f"Error saving cache for {stock} period {old_zone_period}: {e}")
            # Update to new zone period
            self.zone_period = new_zone_period
            self.data_cache.clear()
            self.supply_thresholds.clear()
            self.demand_thresholds.clear()
            self.threshold_zone_periods.clear()
            self.manual_thresholds.clear()
            # Load thresholds for new period if exists
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", f"thresholds_{self.zone_period}.json")
            if os.path.exists(thresholds_file):
                try:
                    with open(thresholds_file, "r") as f:
                        thresholds_data = json.load(f)
                    if isinstance(thresholds_data, dict):
                        self.supply_thresholds = {k: float(v) for k, v in thresholds_data.get("supply_thresholds", {}).items() if isinstance(v, (int, float)) and v > 0}
                        self.demand_thresholds = {k: float(v) for k, v in thresholds_data.get("demand_thresholds", {}).items() if isinstance(v, (int, float)) and v > 0}
                        self.threshold_zone_periods = thresholds_data.get("threshold_zone_periods", {})
                        self.manual_thresholds = {
                            k: {
                                'target': float(v['target']) if v.get('target') and isinstance(v['target'], (int, float)) else None,
                                'stop': float(v['stop']) if v.get('stop') and isinstance(v['stop'], (int, float)) else None,
                                'period': int(v['period']) if v.get('period') and isinstance(v['period'], (int, str)) and str(v['period']).strip() else self.zone_period
                            } for k, v in thresholds_data.get("manual_thresholds", {}).items()
                        }
                        logging.info(f"Loaded thresholds for period {self.zone_period} from {thresholds_file}")
                except Exception as e:
                    logging.error(f"Error loading thresholds for period {self.zone_period}: {e}")
            # Load cache for new period if exists with auto-delete on corrupt
            for stock in self.stocks:
                cache_key = f"{stock}_{self.interval_var.get()}"
                cache_file = os.path.join(r"C:\Users\dad\StockApp", f"{cache_key}_{self.zone_period}.json")
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r") as f:
                            cached = json.load(f)
                        if cached["timestamp"] > (datetime.now().timestamp() - 3600):
                            df = pd.DataFrame.from_dict(cached["data"], orient="index")
                            df.index = pd.to_datetime(df.index)
                            df.index.name = "date"
                            self.data_cache[cache_key] = df
                            logging.debug(f"Loaded cached data for {stock} period {self.zone_period}: {len(df)} rows")
                        else:
                            os.remove(cache_file)
                            logging.debug(f"Deleted stale cache {cache_file}")
                    except json.JSONDecodeError as e:
                        os.remove(cache_file)
                        logging.warning(f"Deleted corrupt cache {cache_file}: {e}")
                    except Exception as e:
                        logging.warning(f"Error loading cache for {stock} period {self.zone_period}: {e}")
            # Queue data fetch for stocks without cache, skip if market closed
            stocks_to_fetch = [stock for stock in self.stocks if stock not in ["***", "Backtest"] and f"{stock}_{self.interval_var.get()}" not in self.data_cache]
            if len(stocks_to_fetch) > 0 and self.is_market_open():
                for stock in stocks_to_fetch:
                    self.fetch_queue.put((stock, self.interval_var.get(), True))
                # Start fetch thread if stocks_to_fetch > 0 and no thread running
                fetch_thread_running = any(t.is_alive() for t in self.threads if hasattr(t, '_target') and t._target.__name__ == 'async_fetch_data')
                if not fetch_thread_running:
                    fetch_thread = threading.Thread(target=self.async_fetch_data, daemon=True)
                    self.threads.append(fetch_thread)
                    fetch_thread.start()
                    logging.debug("Started fetch thread for zone period update")
            else:
                logging.debug("Market closed or no stocks to fetch, skipping queue and processing directly")
                self.process_zone_period_update(stocks_to_fetch)
            # Poll for fetch completion
            self.root.after(500, lambda: self.check_fetch_completion(stocks_to_fetch))
            self.status_label.config(text=f"Updating zone period to {self.zone_period}...")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"Updating zone period to {self.zone_period}")
            self.update_portfolio_table()
            logging.debug(f"Zone period saved: {self.zone_period}")
            beep()
        except Exception as e:
            logging.error(f"Error applying zone period: {e}")
            self.status_label.config(text="Error applying zone period")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error applying zone period")
            beep()
            
    # Snippet 187: Added apply_volume method with comment (insert after apply_zone_period)
    def apply_volume(self):
        logging.debug("Applying volume level")
        try:
            new_volume = self.volume_entry.get().strip()
            try:
                new_volume = float(new_volume)
                if not 0 <= new_volume <= 1:
                    raise ValueError("Volume must be between 0 and 1")
            except ValueError as e:
                logging.warning(f"Invalid volume input: {new_volume}")
                self.status_label.config(text="Invalid volume level")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Invalid volume level")
                beep()
                return
            logging.debug(f"Volume input: {new_volume}")
            self.volume_level.set(new_volume)
            self.update_volume()
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", f"thresholds_{self.zone_period}.json")
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items() if v is not None},
                "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items() if v is not None},
                "threshold_zone_periods": self.threshold_zone_periods,
                "manual_thresholds": {k: {sk: float(sv) if isinstance(sv, (int, float)) else sv for sk, sv in v.items()} for k, v in self.manual_thresholds.items()}
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info(f"Saved volume level {new_volume:.2f} to {thresholds_file}")
            except Exception as e:
                logging.error(f"Error saving volume level: {e}")
            self.status_label.config(text=f"Volume set to {new_volume:.2f}")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"Volume set to {new_volume:.2f}")
            self.volume_entry.delete(0, tk.END)
            self.volume_entry.insert(0, str(new_volume))
            logging.debug(f"Volume saved: {self.volume_level.get()}")
            beep()
        except Exception as e:
            logging.error(f"Error applying volume: {e}")
            self.status_label.config(text="Error applying volume")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error applying volume")
            beep()            
            
# Snippet 49: Full check_fetch_completion with qsize log and process on timeout
# Snippet 50: Full check_fetch_completion with market closed skip for re-queue
    def check_fetch_completion(self, stocks_to_fetch, retry_count=0, max_retries=60):
        qsize = self.fetch_queue.qsize()
        logging.debug(f"Checking fetch queue completion (qsize={qsize}, retry {retry_count}/{max_retries})")
        try:
            if qsize == 0:
                # Queue empty, check data and process
                missing_data = []
                for stock in stocks_to_fetch:
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    df = self.data_cache.get(cache_key, pd.DataFrame())
                    if df is None or df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                        missing_data.append(stock)
                if missing_data and self.is_market_open():
                    logging.warning(f"Data missing for stocks: {missing_data}, retrying fetch")
                    for stock in missing_data:
                        self.fetch_queue.put((stock, self.interval_var.get(), True))
                    self.root.after(500, lambda: self.check_fetch_completion(stocks_to_fetch, retry_count + 1, max_retries))
                    return
                # Process thresholds even if some data missing when market closed
                logging.debug("Processing zone period update")
                self.process_zone_period_update(stocks_to_fetch)
                self.status_label.config(text=f"Applied zone period {self.zone_period}")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak(f"Applied zone period {self.zone_period}")
                beep()
                return
            if retry_count >= max_retries:
                logging.error(f"Fetch completion timed out after {max_retries} retries (qsize={qsize})")
                self.status_label.config(text="Fetch timed out, using available data")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Fetch timed out during zone update")
                beep()
                # Process with available data to avoid stalling
                logging.debug("Processing zone period update after timeout")
                self.process_zone_period_update(stocks_to_fetch)
                return
            # Queue still processing, check again after 500ms
            self.root.after(500, lambda: self.check_fetch_completion(stocks_to_fetch, retry_count + 1, max_retries))
        except Exception as e:
            logging.error(f"Error checking fetch completion: {e}")
            self.status_label.config(text="Error processing zone period")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error processing zone period")
            beep()
            
    def check_screener_refresh(self):
        logging.debug("Checking for screener refresh")
        try:
            flag_file = r"C:\Users\dad\StockApp\screener_refresh.flag"
            if os.path.exists(flag_file):
                try:
                    os.remove(flag_file)
                    logging.debug("Found and removed screener refresh flag")
                    self.refresh_screener()
                except Exception as e:
                    logging.error(f"Error processing screener refresh flag: {e}")
            after_id = self.root.after(500, self.check_screener_refresh)
            self.after_ids.append(after_id)
        except Exception as e:
            logging.error(f"Error in check_screener_refresh: {e}")          

    # Snippet 6: Fixed process_zone_period_update with local np import to resolve NameError
    def process_zone_period_update(self, stocks_to_fetch):
        import numpy as np  # Local import for NaN/inf handling
        logging.debug("Processing zone period update")
        try:
            for stock in stocks_to_fetch:
                cache_key = f"{stock}_{self.interval_var.get()}"
                df = self.data_cache.get(cache_key, pd.DataFrame())
                if df is None or df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                    logging.warning(f"No valid data for {stock}, using default thresholds")
                    price = self.get_live_price(stock) or 0.0
                    self.supply_thresholds[stock] = price * 1.05
                    self.demand_thresholds[stock] = price * 0.95
                    self.threshold_zone_periods[stock] = self.zone_period
                    continue
                df = self.calculate_indicators(df, stock)
                self.data_cache[cache_key] = df
                price = df["Close"].iloc[-1]
                # Check for manual override matching current period
                manual_match = (stock in self.manual_thresholds and self.manual_thresholds[stock].get('period') == self.zone_period)
                if manual_match:
                    target = self.manual_thresholds[stock].get('target', price * 1.05)
                    stop_loss = self.manual_thresholds[stock].get('stop', price * 0.95)
                    logging.debug(f"Using manual thresholds for {stock} (period {self.zone_period} matches)")
                else:
                    target = df["supply_zone"].iloc[-1] if 'supply_zone' in df and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.05
                    stop_loss = df["demand_zone"].iloc[-1] if 'demand_zone' in df and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.95
                    # Clear manual if period changed
                    if stock in self.manual_thresholds:
                        del self.manual_thresholds[stock]
                        logging.debug(f"Cleared manual override for {stock} due to period change")
                if target <= price or stop_loss >= price:
                    logging.warning(f"Invalid thresholds for {stock}: target={target:.2f}, stop_loss={stop_loss:.2f}, price={price:.2f}. Using defaults.")
                    target = price * 1.05
                    stop_loss = price * 0.95
                self.supply_thresholds[stock] = target
                self.demand_thresholds[stock] = stop_loss
                self.threshold_zone_periods[stock] = self.zone_period
                self.root.after(0, lambda s=stock: self.update_tab_signal(s))
            self.update_portfolio_table()
            # Always save updated thresholds
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", f"thresholds_{self.zone_period}.json")
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items()},
                "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items()},
                "threshold_zone_periods": self.threshold_zone_periods,
                "manual_thresholds": {k: {sk: float(sv) if isinstance(sv, (int, float)) else sv for sk, sv in v.items()} for k, v in self.manual_thresholds.items()}
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info(f"Saved updated thresholds to {thresholds_file}")
            except Exception as e:
                logging.error(f"Error saving updated thresholds: {e}")
            # Save cache for processed stocks
            for stock in stocks_to_fetch:
                cache_key = f"{stock}_{self.interval_var.get()}"
                if cache_key in self.data_cache:
                    cache_file = os.path.join(r"C:\Users\dad\StockApp", f"{cache_key}_{self.zone_period}.json")
                    df = self.data_cache[cache_key]
                    df_to_save = df.copy()
                    df_to_save.index = df_to_save.index.astype(str)
                    df_to_save = df_to_save.replace({np.nan: None, np.inf: None, -np.inf: None})
                    try:
                        with open(cache_file, "w") as f:
                            json.dump({
                                "timestamp": datetime.now().timestamp(),
                                "data": df_to_save.to_dict(orient="index")
                            }, f, indent=2)
                        logging.debug(f"Saved cache for {stock} period {self.zone_period} to {cache_file}")
                    except Exception as e:
                        logging.error(f"Error saving cache for {stock} period {self.zone_period}: {e}")
            self.status_label.config(text=f"Applied zone period: {self.zone_period}")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"Applied zone period {self.zone_period}")
            beep()
        except Exception as e:
            logging.error(f"Error processing zone period update: {e}")
            self.status_label.config(text="Error processing zone period")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error processing zone period")
            beep()

    def save_transaction_history(self):
        logging.debug("Saving transaction history")
        try:
            history_file = os.path.join(r"C:\Users\dad\StockApp", "transaction_history.json")
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            if not isinstance(self.transaction_history, dict):
                logging.warning("Transaction history is invalid, initializing empty")
                self.transaction_history = {}
            serializable_history = {}
            for stock, transactions in self.transaction_history.items():
                serializable_history[stock] = []
                for tx in transactions:
                    tx_copy = tx.copy()
                    if isinstance(tx.get('timestamp'), (datetime, pd.Timestamp)):
                        # Use %z for offset to avoid %Z issues
                        tz_aware = tx['timestamp'].tz_localize("America/New_York") if tx['timestamp'].tzinfo is None else tx['timestamp']
                        tx_copy['timestamp'] = tz_aware.strftime("%Y-%m-%d %H:%M:%S%z")
                    elif isinstance(tx.get('timestamp'), str):
                        # Validate by parsing without %Z, then reformat to %z
                        try:
                            # Strip potential %Z and parse naive, then localize and format with %z
                            timestamp_str = tx['timestamp']
                            if 'EDT' in timestamp_str or 'EST' in timestamp_str:
                                naive_str = timestamp_str.replace(' EDT', '').replace(' EST', '')
                                parsed = pd.to_datetime(naive_str, format="%Y-%m-%d %H:%M:%S", errors='coerce')
                                if not pd.isna(parsed):
                                    parsed = parsed.tz_localize("America/New_York")
                                    tx_copy['timestamp'] = parsed.strftime("%Y-%m-%d %H:%M:%S%z")
                                else:
                                    raise ValueError("Invalid parse")
                            else:
                                parsed = pd.to_datetime(timestamp_str, errors='coerce')
                                if pd.isna(parsed):
                                    raise ValueError("Invalid parse")
                                if parsed.tzinfo is None:
                                    parsed = parsed.tz_localize("America/New_York")
                                tx_copy['timestamp'] = parsed.strftime("%Y-%m-%d %H:%M:%S%z")
                        except ValueError:
                            logging.warning(f"Invalid timestamp for {stock}: {tx['timestamp']}, using current time")
                            now = datetime.now(pytz.timezone("America/New_York"))
                            tx_copy['timestamp'] = now.strftime("%Y-%m-%d %H:%M:%S%z")
                    else:
                        # Fallback for missing or invalid timestamp
                        logging.warning(f"Missing or invalid timestamp for {stock}, using current time")
                        now = datetime.now(pytz.timezone("America/New_York"))
                        tx_copy['timestamp'] = now.strftime("%Y-%m-%d %H:%M:%S%z")
                    # Ensure other fields are serializable
                    tx_copy['shares'] = int(tx.get('shares', 0))
                    tx_copy['price'] = float(tx.get('price', 0.0))
                    tx_copy['action'] = str(tx.get('action', ''))
                    tx_copy['mode'] = str(tx.get('mode', self.trading_mode))
                    serializable_history[stock].append(tx_copy)
            with open(history_file, "w", encoding='utf-8') as f:
                json.dump(serializable_history, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved transaction history to {history_file} for {len(self.transaction_history)} tickers")
        except (OSError, PermissionError) as e:
            logging.error(f"File error saving transaction history to {history_file}: {e}")
            self.status_label.config(text="Error saving transaction history")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error saving transaction history")
            beep()
        except Exception as e:
            logging.error(f"Error saving transaction history: {e}")
            self.status_label.config(text="Error saving transaction history")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error saving transaction history")
            beep()
			
    # Snippet 288: Filter update_history_table to today's transactions only (replace existing method)
    def update_history_table(self):
        logging.debug("Updating history table")
        try:
            current_date = datetime.now(pytz.timezone("America/New_York")).date()
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            all_transactions = []
            for stock, transactions in self.transaction_history.items():
                for t in transactions:
                    timestamp_str = t.get('timestamp', '')
                    try:
                        # Parse without timezone first, then localize to America/New_York for EDT/EST
                        if 'EDT' in timestamp_str or 'EST' in timestamp_str:
                            # Remove timezone abbreviation and parse naive, then localize
                            naive_str = timestamp_str.replace(' EDT', '').replace(' EST', '')
                            timestamp = pd.to_datetime(naive_str, format="%Y-%m-%d %H:%M:%S", errors='coerce')
                            if not pd.isna(timestamp):
                                timestamp = timestamp.tz_localize("America/New_York")
                        else:
                            # Try parsing with offset (e.g., 2025-09-23 15:56:42-04:00)
                            timestamp = pd.to_datetime(timestamp_str, format="%Y-%m-%d %H:%M:%S%z", errors='coerce')
                            if pd.isna(timestamp):
                                # Fallback to EDT format (e.g., 2025-09-23 16:03:12 EDT) - now handled above
                                timestamp = pd.to_datetime(timestamp_str, format="%Y-%m-%d %H:%M:%S %Z", errors='coerce')
                        if pd.isna(timestamp):
                            logging.warning(f"Invalid timestamp format for {stock}: {timestamp_str}, using current time")
                            timestamp = datetime.now(pytz.timezone("America/New_York"))
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Error parsing timestamp for {stock}: {e}, using current time")
                        timestamp = datetime.now(pytz.timezone("America/New_York"))
                    if timestamp.date() != current_date:
                        continue  # Filter to today's transactions only
                    all_transactions.append({
                        'stock': stock,
                        'action': t.get('action', ''),
                        'shares': t.get('shares', 0),
                        'price': t.get('price', 0.0),
                        'timestamp': timestamp,
                        'timestamp_str': timestamp_str
                    })
            all_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
            for t in all_transactions:
                tag = 'buy' if t['action'].lower() == 'buy' else 'sell' if t['action'].lower() == 'sell' else ''
                self.history_tree.insert("", "end", values=(
                    t['stock'], t['action'], t['shares'], f"${t['price']:.2f}", t['timestamp_str']
                ), tags=(tag,))
            logging.info(f"Updated history table with {len(all_transactions)} today's transactions")
        except Exception as e:
            logging.error(f"Error updating history table: {e}")
            self.status_label.config(text="Error updating history")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error updating history")
            beep()
			
    # Snippet 224: Updated create_tab_for_stock to respect indicator_visibility and dynamic height (replace existing from Snippet 172)
    def create_tab_for_stock(self, stock, placeholder=False):
        logging.debug("Creating tab for {} with placeholder={}".format(stock, placeholder))
        try:
            if stock not in self.tabs:
                tab = ttk.Frame(self.notebook)
                self.notebook.add(tab, text="{} $0.00".format(stock) if stock != "***" else "***", padding=5)
                self.tabs[stock] = tab
                if stock == "***":
                    label = ttk.Label(tab, text="***", foreground="blue", font=("Arial", 12, "bold"))
                    label.pack(anchor="center", pady=10)
                    logging.info("Created *** placeholder tab")
                    return
                if placeholder:
                    label = ttk.Label(tab, text="Loading {}...".format(stock), font=("Arial", 12))
                    label.pack(anchor="center", pady=10)
                    logging.info("Created placeholder tab for {}".format(stock))
                    return
                if stock == "Backtest":
                    main_frame = ttk.Frame(tab)
                    main_frame.pack(fill="both", expand=True, padx=5, pady=5)
                    filter_frame = ttk.Frame(main_frame)
                    filter_frame.pack(anchor="w", pady=5)
                    ttk.Label(filter_frame, text="Filter Trades:").pack(side="left", padx=5)
                    self.backtest_filter_var = tk.StringVar(value="Non-Zero Trades")
                    filter_combo = ttk.Combobox(filter_frame, textvariable=self.backtest_filter_var,
                                               values=["Non-Zero Trades", "All Trades", "Winning Trades", "Losing Trades"],
                                               state="readonly", width=15)
                    filter_combo.pack(side="left", padx=5)
                    filter_combo.bind("<<ComboboxSelected>>", lambda e: self.run_backtest_filter())
                    columns = ("Trade", "Percent", "Filler")
                    tree_widget = ttk.Treeview(main_frame, columns=columns, show="", height=12, style="Custom.Treeview")
                    tree_widget.column("Trade", width=600, anchor="center")
                    tree_widget.column("Percent", width=100, anchor="center")
                    tree_widget.column("Filler", width=0, stretch=False)
                    tree_widget.tag_configure("profit", background="lightgreen", foreground="black")
                    tree_widget.tag_configure("loss", background="lightcoral", foreground="black")
                    tree_widget.tag_configure("summary", background="lightblue", foreground="black")
                    tree_widget.pack(fill="both", expand=True, padx=5, pady=5)
                    self.backtest_summary_label = ttk.Label(main_frame, text="Total Trades: 0, Win Rate: 0.00%", style="Status.TLabel")
                    self.backtest_summary_label.pack(anchor="w", pady=5)
                    self.indicator_tables[stock] = tree_widget
                    logging.info("Created backtest tab")
                    return
                main_frame = ttk.Frame(tab)
                main_frame.pack(fill="both", expand=True, padx=5, pady=5)
                main_frame.columnconfigure(0, weight=4)
                main_frame.columnconfigure(1, weight=1)
                table_frame = ttk.Frame(main_frame)
                table_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
                signal_frame = ttk.Frame(table_frame)
                signal_frame.pack(fill="x", pady=5)
                self.signal_labels[stock] = ttk.Label(signal_frame, text="Signal: None", style="Status.TLabel")
                self.signal_labels[stock].pack(anchor="w")
                # Count visible indicators for dynamic height
                visible_indicators = sum(1 for ind in self.indicators_list if "{}_{}".format(stock, ind) in self.indicator_visibility and self.indicator_visibility["{}_{}".format(stock, ind)].get())
                table_height = max(10, min(visible_indicators, 16))  # Min 5, max 12 rows
                table_canvas = tk.Canvas(table_frame, height=table_height * 25, width=600)
                table_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table_canvas.yview)
                table_scrollbar.pack(side="right", fill="y")
                table_inner_frame = ttk.Frame(table_canvas)
                table_canvas.create_window((0, 0), window=table_inner_frame, anchor="nw")
                table_canvas.configure(yscrollcommand=table_scrollbar.set)
                table_canvas.pack(fill="both", expand=True)
                columns = ("Indicator", "Value", "Signal")
                self.indicator_tables[stock] = ttk.Treeview(table_inner_frame, columns=columns, show="headings",
                                                           height=table_height, style="Custom.Treeview")
                for col in columns:
                    self.indicator_tables[stock].heading(col, text=col, anchor="center")
                    self.indicator_tables[stock].column(col, width=250, anchor="center")
                self.indicator_tables[stock].tag_configure('green', background='lightgreen', foreground='black')
                self.indicator_tables[stock].tag_configure('red', background='lightcoral', foreground='black')
                self.indicator_tables[stock].tag_configure('lightgrey', background='lightgrey', foreground='black')
                # Clear table on creation
                for item in self.indicator_tables[stock].get_children():
                    self.indicator_tables[stock].delete(item)
                self.indicator_tables[stock].pack(fill="both", expand=True)
                def update_table_scroll_region(event):
                    table_canvas.configure(scrollregion=table_canvas.bbox("all"))
                table_inner_frame.bind("<Configure>", update_table_scroll_region)
                table_canvas.update_idletasks()
                table_canvas.configure(scrollregion=table_canvas.bbox("all"))
                right_frame = ttk.Frame(main_frame)
            # Snippet 6d: Replace create_tab_for_stock checkbox section for global-linked toggles (place after "right_frame = ..." line)
                right_frame.grid(row=0, column=1, sticky="ns", padx=5)
                check_canvas = tk.Canvas(right_frame, height=table_height * 20, width=150)
                check_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=check_canvas.yview)
                check_scrollbar.pack(side="right", fill="y")
                check_inner_frame = ttk.Frame(check_canvas)
                check_canvas.create_window((0, 0), window=check_inner_frame, anchor="nw")
                check_canvas.configure(yscrollcommand=check_scrollbar.set)
                check_canvas.pack(fill="y")
                groups = {
                    "Basic": ["mfi", "ema13" if self.interval_var.get() == "3min" else "sma13", "macd", "demand_zone"],
                    "Advanced 1": ["stochastic", "cci", "obv", "vwap"],
                    "Advanced 2": ["adx", "atr", "momentum"],
                    "Advanced 3": ["stochastic_rsi", "williams_%r", "bollinger_bands"]
                }
                for group_name, indicators in groups.items():
                    group_frame = ttk.LabelFrame(check_inner_frame, text=group_name, padding=5)
                    group_frame.pack(fill="x", pady=2)
                    ttk.Checkbutton(group_frame, text="Show {}".format(group_name),
                                    variable=self.group_visibility[group_name],
                                    command=lambda g=group_name: self.toggle_group_global(g)).pack(anchor="w")
                    for indicator in indicators:
                        global_key = indicator  # Use global key
                        if global_key not in self.indicator_visibility:
                            self.indicator_visibility[global_key] = tk.BooleanVar(value=True)
                        display_indicator = indicator.replace("_", " ").title()
                        ttk.Checkbutton(group_frame, text=display_indicator,
                                        variable=self.indicator_visibility[global_key],
                                        command=lambda ind=indicator: self.toggle_indicator_global(ind)).pack(anchor="w")
                def update_check_scroll_region(event):
                    check_canvas.configure(scrollregion=check_canvas.bbox("all"))
                check_inner_frame.bind("<Configure>", update_check_scroll_region)
                check_canvas.update_idletasks()
                check_canvas.configure(scrollregion=check_canvas.bbox("all"))
                if not placeholder:
                    cache_key = "{}_{}".format(stock, self.interval_var.get())
                    df = self.data_cache.get(cache_key, pd.DataFrame())
                    if not df.empty and 'Close' in df.columns and not df['Close'].isna().all():
                        df = self.calculate_indicators(df, stock)
                        with self.cache_lock:
                            self.data_cache[cache_key] = df
                        self.update_tab_signal(stock)
                        logging.info("Created full tab for {}".format(stock))
                    else:
                        self.indicator_tables[stock].insert("", "end", values=("No data", "", ""))
                        logging.info("Created placeholder tab for {}".format(stock))
        except (KeyError, ValueError) as e:
            logging.debug("Recoverable error creating tab for {}: {}".format(stock, e))
            if stock in self.tabs and self.indicator_tables.get(stock):
                logging.info("Tab for {} created despite error".format(stock))
            else:
                logging.error("Failed to create tab for {}: {}".format(stock, e))
                self.root.after(0, lambda: self.status_label.config(text="Error creating tab for {}".format(stock)))
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.root.after(0, lambda: self.speak("Error creating tab for {}".format(stock)))
                self.root.after(0, beep)
        except Exception as e:
            logging.error("Critical error creating tab for {}: {}".format(stock, e))
            self.root.after(0, lambda: self.status_label.config(text="Error creating tab for {}".format(stock)))
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.root.after(0, lambda: self.speak("Error creating tab for {}".format(stock)))
            self.root.after(0, beep)
			
    def create_chart_tab(self, stock, placeholder=False):
        logging.debug(f"Creating chart tab for {stock}, placeholder={placeholder}")
        try:
            if stock in self.tabs:
                logging.debug(f"Tab for {stock} already exists")
                return
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=stock)
            self.tabs[stock] = tab
            if placeholder:
                ttk.Label(tab, text=f"Loading {stock}...", font=("Arial", 12)).pack(pady=10)
                logging.info(f"Created placeholder tab for {stock}")
                return
            self.signal_labels[stock] = ttk.Label(tab, text="Signal: N/A", font=("Arial", 10, "bold"), style="Signal.Row")
            self.signal_labels[stock].pack(anchor="w", padx=5, pady=5)
            columns = ("Indicator", "Value", "Signal")
            tree_widget = ttk.Treeview(tab, columns=columns, show="headings", height=12, style="Custom.Treeview")
            tree_widget.heading("Indicator", text="Indicator", anchor="center")
            tree_widget.heading("Value", text="Value", anchor="center")
            tree_widget.heading("Signal", text="Signal", anchor="center")
            tree_widget.column("Indicator", width=150, anchor="center")
            tree_widget.column("Value", width=100, anchor="center")
            tree_widget.column("Signal", width=100, anchor="center")
            tree_widget.pack(fill="both", expand=True, padx=5, pady=5)
            self.indicator_tables[stock] = tree_widget
            logging.info(f"Created chart tab for {stock}")
        except Exception as e:
            logging.error(f"Error creating chart tab for {stock}: {e}")
            self.root.after(0, lambda: self.status_label.config(text=f"Error creating tab for {stock}"))

			
    def create_tabs(self):
        logging.debug(f"Creating tabs for stocks: {self.stocks}")
        try:
            for tab_id in self.notebook.tabs():
                self.notebook.forget(tab_id)
            self.tabs.clear()
            self.signal_labels.clear()
            self.indicator_tables.clear()
            for stock in self.stocks:
                if stock not in self.tabs:
                    self.create_tab_for_stock(stock, placeholder=False)
                    logging.debug(f"Created tab for stock {stock}")
            if "***" not in self.tabs:
                self.create_tab_for_stock("***")
                logging.debug("Created *** tab")
            for stock in self.stocks:
                if stock not in ["***", "Backtest"]:
                    self.root.after(0, lambda s=stock: self.update_tab_signal(s))
            logging.info("Tabs created successfully")
        except Exception as e:
            logging.error(f"Error creating tabs: {e}")
            self.root.after(0, lambda: self.status_label.config(text="Error creating tabs"))
            self.root.after(0, lambda: self.speak("Error creating tabs"))
            self.root.after(0, beep)
            
    # Snippet 220: Updated update_tab_signal to respect indicator_visibility and clear table (replace existing from Snippet 219)
    def update_tab_signal(self, stock):
        logging.debug("Updating tab signal for {}".format(stock))
        try:
            if stock not in self.signal_labels or stock not in self.indicator_tables:
                logging.warning("No signal label or indicator table for {}".format(stock))
                return
            cache_key = "{}_{}".format(stock, self.interval_var.get())
            df = self.data_cache.get(cache_key, pd.DataFrame())
            if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                    logging.warning("No valid data for {}".format(stock))
                    self.signal_labels[stock].config(text="Signal: No data")
                    self.invalid_stocks.add(stock)
                    return
                df = self.calculate_indicators(df, stock)
                self.data_cache[cache_key] = df
            # Initialize thresholds if not set
            price = df["Close"].iloc[-1] if not df.empty and "Close" in df.columns else self.get_live_price(stock) or 0.0
            if price == 0.0:
                logging.warning("No price available for {}, using default thresholds".format(stock))
                price = 1.0  # Avoid division by zero
            if stock not in self.supply_thresholds or stock not in self.demand_thresholds or self.threshold_zone_periods.get(stock) != self.zone_period:
                self.supply_thresholds[stock] = df["supply_zone"].iloc[-1] if 'supply_zone' in df and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.05
                self.demand_thresholds[stock] = df["demand_zone"].iloc[-1] if 'demand_zone' in df and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.95
                self.threshold_zone_periods[stock] = self.zone_period
                logging.debug("Initialized thresholds for {}: supply=${:.2f}, demand=${:.2f}".format(stock, self.supply_thresholds[stock], self.demand_thresholds[stock]))
            # Clear table completely
            for item in self.indicator_tables[stock].get_children():
                self.indicator_tables[stock].delete(item)
            buy_signals = 0
            active_indicators = 0
            for indicator in self.indicators_list:
                indicator_key = "{}_{}".format(stock, indicator)
                if indicator_key not in self.indicator_visibility or not self.indicator_visibility[indicator_key].get():
                    continue  # Skip if toggled off
                if indicator not in df.columns or pd.isna(df[indicator].iloc[-1]):
                    continue
                active_indicators += 1
                signal = ""
                if indicator == "mfi":
                    signal = "Buy" if df[indicator].iloc[-1] < 20 else "Sell" if df[indicator].iloc[-1] > 80 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "macd":
                    signal = "Buy" if df[indicator].iloc[-1] > 0 else "Sell" if df[indicator].iloc[-1] < 0 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "stochastic":
                    signal = "Buy" if df[indicator].iloc[-1] < 20 else "Sell" if df[indicator].iloc[-1] > 80 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "ema13" and self.interval_var.get() == "3min":
                    signal = "Buy" if df["Close"].iloc[-1] > df[indicator].iloc[-1] else "Sell" if df["Close"].iloc[-1] < df[indicator].iloc[-1] else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "sma13" and self.interval_var.get() != "3min":
                    signal = "Buy" if df["Close"].iloc[-1] > df[indicator].iloc[-1] else "Sell" if df["Close"].iloc[-1] < df[indicator].iloc[-1] else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "cci":
                    signal = "Buy" if df[indicator].iloc[-1] < -50 else "Sell" if df[indicator].iloc[-1] > 50 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "obv":
                    signal = "Buy" if df[indicator].diff().iloc[-1] > 0 else "Sell" if df[indicator].diff().iloc[-1] < 0 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "vwap":
                    signal = "Buy" if df["Close"].iloc[-1] < df[indicator].iloc[-1] else "Sell" if df["Close"].iloc[-1] > df[indicator].iloc[-1] else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "adx":
                    signal = "Buy" if df[indicator].iloc[-1] > 25 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "momentum":
                    signal = "Buy" if df[indicator].iloc[-1] > 0 else "Sell" if df[indicator].iloc[-1] < 0 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "stochastic_rsi":
                    signal = "Buy" if df[indicator].iloc[-1] < 20 else "Sell" if df[indicator].iloc[-1] > 80 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "williams_%r":
                    signal = "Buy" if df[indicator].iloc[-1] < -80 else "Sell" if df[indicator].iloc[-1] > -20 else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "bollinger_bands" and not pd.isna(df.get("bb_lower", pd.Series([float('nan')])).iloc[-1]):
                    signal = "Buy" if df["Close"].iloc[-1] < df["bb_lower"].iloc[-1] else "Sell" if df["Close"].iloc[-1] > df["bb_upper"].iloc[-1] else ""
                    if signal == "Buy":
                        buy_signals += 1
                elif indicator == "demand_zone":
                    signal = "Buy" if df["Close"].iloc[-1] < df[indicator].iloc[-1] else ""
                    if signal == "Buy":
                        buy_signals += 1
                value = df[indicator].iloc[-1] if indicator in df and not pd.isna(df[indicator].iloc[-1]) else "N/A"
                self.indicator_tables[stock].insert("", "end", values=(
                    indicator.replace("_", " ").title(),
                    "{:.4f}".format(value) if isinstance(value, float) else value,
                    signal
                ), tags=("green" if signal == "Buy" else "red" if signal == "Sell" else "lightgrey"))
            signal_text = "Buy" if active_indicators > 0 and (buy_signals / active_indicators) >= self.buy_threshold.get() else "Sell" if active_indicators > 0 else "No data"
            self.signal_labels[stock].config(text="Signal: {}".format(signal_text))
            logging.info("Updated signal for {}: {}, buy_signals={}, active_indicators={}".format(stock, signal_text, buy_signals, active_indicators))
            # Save thresholds
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds_{}.json".format(self.zone_period))
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items()},
                "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items()},
                "threshold_zone_periods": self.threshold_zone_periods
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info("Saved thresholds to {}".format(thresholds_file))
            except Exception as e:
                logging.error("Error saving thresholds: {}".format(e))
        except Exception as e:
            logging.error("Error updating tab signal for {}: {}".format(stock, e))
            self.signal_labels[stock].config(text="Signal: Error")
            self.root.after(0, lambda: self.status_label.config(text="Error updating signal for {}".format(stock)))
            self.root.after(0, beep)
            
    # Snippet 2: Enhanced calculate_indicators with NaN/inf handling for JSON-safe serialization (replace existing method)
    def calculate_indicators(self, df, stock):
        import numpy as np
        logging.debug(f"Calculating indicators for {stock} ({len(df)} rows)")
        try:
            if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                logging.warning(f"No valid data for {stock} in calculate_indicators")
                return df
            df = df.copy()
            # Ensure 3min timeframe for buy signals by resampling 1min data
            if self.interval_var.get() == "3min" and '1min' in self.interval_var.get():
                df = df.resample('3min').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
            # Basic indicators on 3min for signals
            df['sma13'] = df['Close'].rolling(window=13).mean()
            df['ema13'] = df['Close'].ewm(span=13).mean()
            logging.debug(f"EMA13 calc for {stock}: last Close={df['Close'].iloc[-1]:.2f}, last EMA13={df['ema13'].iloc[-1]:.2f}, signal={'Buy' if df['Close'].iloc[-1] > df['ema13'].iloc[-1] else 'Sell' if df['Close'].iloc[-1] < df['ema13'].iloc[-1] else 'Neutral'}")
            df['macd'] = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)[0]
            df['mfi'] = ta.MFI(df['High'], df['Low'], df['Close'], df['Volume'], timeperiod=14)
            df['stochastic'] = ta.STOCH(df['High'], df['Low'], df['Close'], fastk_period=14, slowk_period=3, slowd_period=3)[0]
            df['cci'] = ta.CCI(df['High'], df['Low'], df['Close'], timeperiod=14)
            df['obv'] = ta.OBV(df['Close'], df['Volume'])
            df['vwap'] = ((df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum())
            df['adx'] = ta.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)
            df['atr'] = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
            df['momentum'] = ta.MOM(df['Close'], timeperiod=14)
            df['stochastic_rsi'] = ta.STOCHRSI(df['Close'], timeperiod=14)[0]
            df['williams_%r'] = ta.WILLR(df['High'], df['Low'], df['Close'], timeperiod=14)
            bb_upper, bb_middle, bb_lower = ta.BBANDS(df['Close'], timeperiod=20)
            df['bb_upper'] = bb_upper
            df['bb_lower'] = bb_lower
            # Supply/demand zones on higher timeframe (15min)
            if len(df) < self.zone_period:
                price = df["Close"].iloc[-1] if not df.empty and "Close" in df.columns else 0.0
                df['supply_zone'] = price * 1.20
                df['demand_zone'] = price * 0.80
            else:
                df_15min = df.resample('15min').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
                recent_highs = df_15min['High'].rolling(window=self.zone_period).max()
                recent_lows = df_15min['Low'].rolling(window=self.zone_period).min()
                df_15min['supply_zone'] = recent_highs * 1.15 if not pd.isna(recent_highs.iloc[-1]) else df["Close"].iloc[-1] * 1.20
                df_15min['demand_zone'] = recent_lows * 0.85 if not pd.isna(recent_lows.iloc[-1]) else df["Close"].iloc[-1] * 0.80
                df_15min = df_15min.reindex(df.index, method='ffill')
                df['supply_zone'] = df_15min['supply_zone']
                df['demand_zone'] = df_15min['demand_zone']
            # Replace NaN/inf for JSON serialization safety
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            logging.debug(f"Indicators calculated for {stock}")
            return df
        except Exception as e:
            logging.error(f"Error calculating indicators for {stock}: {e}")
            return df
			
    def calculate_mfi(self, df):
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        raw_money_flow = typical_price * df["Volume"]
        positive_flow = raw_money_flow.where(df["Close"] > df["Close"].shift(1), 0)
        negative_flow = raw_money_flow.where(df["Close"] < df["Close"].shift(1), 0)
        positive_mf = positive_flow.rolling(window=14, min_periods=1).sum()
        negative_mf = negative_flow.rolling(window=14, min_periods=1).sum()
        mfi = 100 - (100 / (1 + positive_mf / negative_mf.replace(0, 1e-10)))
        return mfi.fillna(0)
        
    def update_target(self, stock, value):
        try:
            value = float(value)
            self.portfolio_tree.item(stock, values=(stock, self.portfolio.get(stock, 0), f"${self.cost_basis.get(stock, 0):.2f}",
                                                   f"${self.data_cache.get(f'{stock}_{self.interval_var.get()}', pd.DataFrame())['Close'].iloc[-1]:.2f}",
                                                   f"${value:.2f}", self.stop_loss_entry.get(), f"${0:.2f}"))
            logging.info(f"Updated target for {stock} to ${value:.2f}")
        except ValueError:
            logging.warning(f"Invalid target value for {stock}: {value}")
            self.speak("Invalid target value")
            beep()
			
    def update_stop_loss(self, stock, value):
        try:
            value = float(value)
            self.portfolio_tree.item(stock, values=(stock, self.portfolio.get(stock, 0), f"${self.cost_basis.get(stock, 0):.2f}",
                                                   f"${self.data_cache.get(f'{stock}_{self.interval_var.get()}', pd.DataFrame())['Close'].iloc[-1]:.2f}",
                                                   self.target_entry.get(), f"${value:.2f}", f"${0:.2f}"))
            logging.info(f"Updated stop loss for {stock} to ${value:.2f}")
        except ValueError:
            logging.warning(f"Invalid stop loss value for {stock}: {value}")
            self.speak("Invalid stop loss value")
            beep()	
			
    def apply_target_stop_loss(self):
        logging.debug("Applying target and stop loss")
        try:
            target = self.target_entry.get().strip()
            stop_loss = self.stop_loss_entry.get().strip()
            try:
                target = float(target) if target else None
                stop_loss = float(stop_loss) if stop_loss else None
                if target is not None and target <= 0:
                    raise ValueError("Target must be positive")
                if stop_loss is not None and stop_loss <= 0:
                    raise ValueError("Stop loss must be positive")
            except ValueError as e:
                logging.warning(f"Invalid target or stop loss: {e}")
                self.status_label.config(text="Invalid target or stop loss")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Invalid target or stop loss")
                beep()
                return
            if self.current_stock and (target is not None or stop_loss is not None):
                price = self.get_live_price(self.current_stock)
                if price == 0.0:
                    logging.error(f"No price data for {self.current_stock}")
                    self.status_label.config(text=f"No price data for {self.current_stock}")
                    if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                        self.speak(f"No price data for {self.current_stock}")
                    beep()
                    return
                if target is not None:
                    self.supply_thresholds[self.current_stock] = target
                    self.manual_thresholds[self.current_stock] = {
                        'target': target,
                        'stop': self.manual_thresholds.get(self.current_stock, {}).get('stop', price * 0.95),
                        'period': self.zone_period
                    }
                if stop_loss is not None:
                    self.demand_thresholds[self.current_stock] = stop_loss
                    self.manual_thresholds[self.current_stock] = {
                        'target': self.manual_thresholds.get(self.current_stock, {}).get('target', price * 1.05),
                        'stop': stop_loss,
                        'period': self.zone_period
                    }
                self.threshold_zone_periods[self.current_stock] = self.zone_period
                thresholds_file = os.path.join(r"C:\Users\dad\StockApp", f"thresholds_{self.zone_period}.json")
                thresholds_data = {
                    "buy_threshold": self.buy_threshold.get(),
                    "zone_period": self.zone_period,
                    "volume_level": self.volume_level.get(),
                    "invalid_stocks": list(self.invalid_stocks),
                    "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items() if v is not None},
                    "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items() if v is not None},
                    "threshold_zone_periods": self.threshold_zone_periods,
                    "manual_thresholds": {k: {sk: float(sv) if isinstance(sv, (int, float)) else sv for sk, sv in v.items()} for k, v in self.manual_thresholds.items()}
                }
                try:
                    os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                    with open(thresholds_file, "w") as f:
                        json.dump(thresholds_data, f, indent=2)
                    logging.info(f"Saved manual thresholds for {self.current_stock} to {thresholds_file}")
                except Exception as e:
                    logging.error(f"Error saving thresholds: {e}")
                self.update_portfolio_table()
                self.status_label.config(text=f"Applied manual overrides for {self.current_stock}")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak(f"Applied manual overrides for {self.current_stock}")
                beep()
            else:
                self.status_label.config(text="No stock selected or no changes applied")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("No stock selected or no changes applied")
                beep()
        except Exception as e:
            logging.error(f"Error applying target/stop loss: {e}")
            self.status_label.config(text="Error applying target/stop loss")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error applying target/stop loss")
            beep()
				
# Snippet 35: Debounced on_tab_changed to stop flood
    def on_tab_changed(self, event):
        if hasattr(self, '_last_tab_change') and time.time() - self._last_tab_change < 0.2:
            return  # Debounce 200ms
        self._last_tab_change = time.time()
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return
            tab_text = self.notebook.tab(current_tab, "text")
            stock = tab_text.split()[0] if " " in tab_text else tab_text
            if stock in self.stocks and stock not in ["***", "Backtest"]:
                logging.debug(f"Selected tab: {stock}")
                self.current_stock = stock
                self.root.after(200, lambda: self.update_tab_signal(stock))  # Debounce delay
        except Exception as e:
            logging.error(f"Error in on_tab_changed: {e}")
			
    def is_market_open(self):
        logging.debug("Checking market status")
        try:
            now = datetime.now(pytz.timezone("America/New_York"))
            is_weekday = now.weekday() < 5
            pre_market_open = now.replace(hour=4, minute=0, second=0, microsecond=0)
            after_hours_close = now.replace(hour=20, minute=0, second=0, microsecond=0)
            is_open = is_weekday and pre_market_open <= now <= after_hours_close
            logging.debug(f"Market check: now={now}, is_weekday={is_weekday}, is_open={is_open}")
            return is_open
        except Exception as e:
            logging.error(f"Error checking market status: {e}")
            return False
			
    def fetch_fmp_indicators(self, symbols):
        logging.debug(f"Fetching FMP indicators for {len(symbols)} symbols")
        try:
            indicators = ["rsi", "ema", "macd", "stoch", "cci", "obv", "vwap"]
            results = {}
            for symbol in symbols:
                results[symbol] = {}
                for indicator in indicators:
                    try:
                        url = f"https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}"
                        params = {"type": indicator, "period": 14 if indicator != "ema" else 13, "apikey": self.api_key}
                        response = requests.get(url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            if data and indicator in data[0]:
                                results[symbol][indicator] = data[0][indicator]
                                logging.info(f"Fetched {indicator} for {symbol}: {data[0][indicator]}")
                        else:
                            logging.warning(f"Failed to fetch {indicator} for {symbol}: Status {response.status_code}")
                    except Exception as e:
                        logging.error(f"Error fetching {indicator} for {symbol}: {e}")
            return results
        except Exception as e:
            logging.error(f"Error in fetch_fmp_indicators: {e}")
            return {}
			
    def start_fetch_thread(self):
        logging.debug("Starting fetch thread for top hottest stocks")
        try:
            fetch_thread = threading.Thread(target=self.async_fetch_top_hottest_stocks, daemon=True)
            self.threads.append(fetch_thread)
            fetch_thread.start()
            logging.info("Fetch thread started")
        except Exception as e:
            logging.error(f"Error starting fetch thread: {e}")
            self.status_label.config(text="Error starting fetch thread")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error starting fetch thread")
            beep()		
			
    def async_create_tab_and_update(self, stock, df):
        logging.debug(f"Async creating tab and updating signals for {stock}")
        try:
            if stock != "***" and stock not in self.tabs:
                self.create_tab_for_stock(stock, placeholder=False)
            df = self.calculate_indicators(df, stock)
            cache_key = f"{stock}_{self.interval_var.get()}"
            self.data_cache[cache_key] = df
            self.supply_thresholds[stock] = df["supply_zone"].iloc[-1] if 'supply_zone' in df and not pd.isna(df["supply_zone"].iloc[-1]) else df["Close"].iloc[-1] * 1.1
            self.demand_thresholds[stock] = df["demand_zone"].iloc[-1] if 'demand_zone' in df and not pd.isna(df["demand_zone"].iloc[-1]) else df["Close"].iloc[-1] * 0.9
            self.update_tab_signal(stock)
            logging.info(f"Completed async tab update for {stock}")
        except Exception as e:
            logging.error(f"Error in async tab update for {stock}: {e}")
            self.root.after(0, lambda: self.status_label.config(text=f"Error updating tab for {stock}"))
            self.root.after(0, lambda: self.speak(f"Error updating tab for {stock}"))
            self.root.after(0, beep)
            
    def _update_data_thread(self, first_fetch, gui_update_queue):
        logging.debug(f"Running data update thread, first_fetch={first_fetch}")
        try:
            lock = threading.Lock()
            stocks_to_process = [s for s in self.stocks if s not in ["***", "Backtest"]]
            for stock in stocks_to_process:
                with lock:
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=first_fetch)
                    if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                        logging.warning(f"No valid data for {stock}")
                        gui_update_queue.put(lambda: self.status_label.config(text=f"Critical: No data for {stock}"))
                        gui_update_queue.put(lambda: self.speak(f"Critical: No data for {stock}"))
                        gui_update_queue.put(beep)
                        continue
                    df = self.calculate_indicators(df, stock)
                    self.data_cache[cache_key] = df
                    live_price = self.get_live_price(stock)
                    if live_price == 0.0 and stock in self.portfolio:
                        logging.warning(f"No live price for portfolio stock {stock}")
                        gui_update_queue.put(lambda: self.status_label.config(text=f"Critical: No live price for {stock}"))
                        gui_update_queue.put(lambda: self.speak(f"Critical: No live price for {stock}"))
                        gui_update_queue.put(beep)
                    gui_update_queue.put(lambda s=stock: self.create_tab_for_stock(s, placeholder=False))
                    gui_update_queue.put(lambda s=stock: self.update_tab_signal(s))
                time.sleep(0.1)
            gui_update_queue.put(self.update_portfolio_table)
            gui_update_queue.put(self.update_tab_labels)  # Update labels after all tabs are created
            gui_update_queue.put(lambda: self.status_label.config(text="Data updated"))
            gui_update_queue.put(lambda: self.progress_bar.stop())
            gui_update_queue.put(beep)
            logging.info("Data update thread completed")
        except Exception as e:
            logging.error(f"Error in data update thread: {e}")
            gui_update_queue.put(lambda: self.status_label.config(text="Error updating data"))
            gui_update_queue.put(lambda: self.speak("Error updating data"))
            gui_update_queue.put(beep)          

# Snippet 2: Fixed save_cache_data to use fixed path instead of os.getcwd()
    def save_cache_data(self):
        logging.debug("Saving cache data")
        try:
            cache_file = os.path.join(r"C:\Users\dad\StockApp", "stock_cache.json")
            cache_data = {k: v.reset_index().to_dict('records') for k, v in self.data_cache.items()}
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            logging.info(f"Saved cache data to {cache_file} with {len(cache_data)} keys")
        except Exception as e:
            logging.error(f"Error saving cache data: {e}")
            self.status_label.config(text="Error saving cache data")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error saving cache data")
            beep()

# Snippet 3: Fixed update_tabs_with_new_stocks to use fixed path instead of os.getcwd()
    def update_tabs_with_new_stocks(self):
        logging.debug("Updating tabs with new stocks")
        try:
            gui_update_queue = queue.Queue()
            def process_gui_updates():
                try:
                    while not gui_update_queue.empty():
                        func = gui_update_queue.get_nowait()
                        func()
                        gui_update_queue.task_done()
                except queue.Empty:
                    pass
                except Exception as e:
                    logging.error(f"Error processing GUI updates: {e}")
                self.root.after(500, process_gui_updates)
            self.root.after(500, process_gui_updates)
            def update_thread():
                try:
                    lock = threading.Lock()
                    cache_file = os.path.join(r"C:\Users\dad\StockApp", "stock_cache.json")
                    cache_data = {}
                    if os.path.exists(cache_file):
                        try:
                            with open(cache_file, "r") as f:
                                cache_data = json.load(f)
                            logging.debug(f"Loaded cache data from {cache_file}")
                        except Exception as e:
                            logging.error(f"Error loading cache data: {e}")
                            cache_data = {}
                    with lock:
                        batch_size = 2
                        stocks_to_process = [s for s in self.stocks if s not in ["***", "Backtest"]]
                        failed_stocks = getattr(self, 'failed_stocks', set())
                        for i in range(0, len(stocks_to_process), batch_size):
                            batch = stocks_to_process[i:i + batch_size]
                            for stock in batch:
                                if stock in failed_stocks:
                                    logging.debug(f"Skipping {stock}: previously failed")
                                    continue
                                logging.debug(f"Creating tab for {stock}")
                                cache_key = f"{stock}_{self.interval_var.get()}"
                                df = self.data_cache.get(cache_key, pd.DataFrame())
                                if cache_key in cache_data and isinstance(df, pd.DataFrame) and not df.empty and 'Close' in df.columns and not df['Close'].isna().all() and all(col in df.columns for col in ['High', 'Low', 'Volume']):
                                    gui_update_queue.put(lambda s=stock: self.create_tab_for_stock(s))
                                    gui_update_queue.put(lambda s=stock: self.update_tab_signal(s))
                                else:
                                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                                    if not isinstance(df, pd.DataFrame) or df.empty or 'Close' not in df.columns or df['Close'].isna().all() or not all(col in df.columns for col in ['High', 'Low', 'Volume']):
                                        logging.warning(f"No valid data for {stock}, skipping tab creation")
                                        failed_stocks.add(stock)
                                        self.failed_stocks = failed_stocks
                                        gui_update_queue.put(lambda: self.status_label.config(text=f"No data for {stock}"))
                                        continue
                                    df = self.calculate_indicators(df, stock)
                                    self.data_cache[cache_key] = df
                                    cache_data[cache_key] = df.reset_index().to_dict('records')
                                    gui_update_queue.put(lambda s=stock: self.create_tab_for_stock(s))
                                    gui_update_queue.put(lambda s=stock: self.update_tab_signal(s))
                                time.sleep(0.8)
                        try:
                            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                            with open(cache_file, "w") as f:
                                json.dump(cache_data, f, indent=2)
                            logging.info(f"Saved cache data to {cache_file}")
                        except Exception as e:
                            logging.error(f"Error saving cache data: {e}")
                            gui_update_queue.put(lambda: self.status_label.config(text="Error saving cache"))
                        gui_update_queue.put(self.update_tab_labels)
                    gui_update_queue.put(lambda: self.status_label.config(text="Tabs updated"))
                    logging.info("Tabs updated with new stocks")
                except Exception as e:
                    logging.error(f"Error in update tabs thread: {e}")
                    gui_update_queue.put(lambda: self.status_label.config(text="Error updating tabs"))
            thread = threading.Thread(target=update_thread, daemon=True)
            self.threads.append(thread)
            thread.start()
        except Exception as e:
            logging.error(f"Error initiating update tabs: {e}")
            self.status_label.config(text="Error updating tabs")			
			
    def save_portfolio(self):
        logging.debug("Saving portfolio")
        try:
            portfolio_data = {
                "day_portfolio": {k: int(v) for k, v in self.day_portfolio.items() if v > 0},
                "swing_portfolio": {k: int(v) for k, v in self.swing_portfolio.items() if v > 0},
                "day_cost_basis": {k: float(v) for k, v in self.day_cost_basis.items() if k in self.day_portfolio and self.day_portfolio[k] > 0},
                "swing_cost_basis": {k: float(v) for k, v in self.swing_cost_basis.items() if k in self.swing_portfolio and self.swing_portfolio[k] > 0}
            }
            held_stocks_file = os.path.join(os.getcwd(), "held_stocks.json")
            os.makedirs(os.path.dirname(held_stocks_file), exist_ok=True)
            with open(held_stocks_file, "w") as f:
                json.dump(portfolio_data, f, indent=2)
            logging.info(f"Saved portfolio to {held_stocks_file}")
        except (OSError, PermissionError) as e:
            logging.error(f"Failed to save portfolio due to file error: {e}")
            self.speak("Error saving portfolio")
            beep()
        except Exception as e:
            logging.error(f"Error saving portfolio: {e}")
            self.speak("Error saving portfolio")
            beep()			
			
    def remove_stock(self, stock):
        logging.debug(f"Removing stock {stock}")
        try:
            if stock in self.day_portfolio or stock in self.swing_portfolio:
                logging.warning(f"Cannot remove {stock}: it is held in portfolio")
                self.status_label.config(text=f"Cannot remove {stock}: held in portfolio")
                self.speak(f"Cannot remove {stock}: held in portfolio")
                return
            cache_key = f"{stock}_{self.interval_var.get()}"
            df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
            if not isinstance(df, pd.DataFrame) or df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                logging.warning(f"Stock {stock} has no valid data, removing from stocks list")
                if stock in self.stocks:
                    self.stocks.remove(stock)
                if stock in self.tabs:
                    self.notebook.forget(self.tabs[stock])
                    del self.tabs[stock]
                    del self.signal_labels[stock]
                    del self.indicator_tables[stock]
                if stock in self.added_stocks:
                    self.added_stocks.remove(stock)
                cache_keys = [k for k in self.data_cache.keys() if k.startswith(f"{stock}_")]
                for k in cache_keys:
                    del self.data_cache[k]
                try:
                    with open(self.added_stocks_file, "w") as f:
                        json.dump(list(self.added_stocks), f, indent=2)
                    logging.info(f"Saved updated added stocks to {self.added_stocks_file}")
                except Exception as e:
                    logging.error(f"Error saving added stocks: {e}")
                self.update_portfolio_table()
                self.update_tab_labels()
                logging.info(f"Removed invalid stock {stock} due to no data")
                self.speak(f"Removed invalid stock {stock}")
                return
            if stock in self.stocks:
                self.stocks.remove(stock)
            if stock in self.tabs:
                self.notebook.forget(self.tabs[stock])
                del self.tabs[stock]
                del self.signal_labels[stock]
                del self.indicator_tables[stock]
            if stock in self.added_stocks:
                self.added_stocks.remove(stock)
            cache_keys = [k for k in self.data_cache.keys() if k.startswith(f"{stock}_")]
            for k in cache_keys:
                del self.data_cache[k]
            try:
                with open(self.added_stocks_file, "w") as f:
                    json.dump(list(self.added_stocks), f, indent=2)
                logging.info(f"Saved updated added stocks to {self.added_stocks_file}")
            except Exception as e:
                logging.error(f"Error saving added stocks: {e}")
            self.update_portfolio_table()
            self.update_tab_labels()
            logging.info(f"Removed stock {stock} successfully")
            self.speak(f"Removed stock {stock}")
        except Exception as e:
            logging.error(f"Error removing stock {stock}: {e}")
            self.status_label.config(text=f"Error removing {stock}")
            self.speak(f"Error removing {stock}")	
			
    def buy_stock(self):
        logging.debug("Initiating buy stock")
        try:
            stock = self.current_stock
            if not stock or stock == "***" or stock == "Backtest":
                logging.warning("No valid stock selected for buying")
                self.status_label.config(text="Select a valid stock to buy")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Select a valid stock to buy")
                beep()
                return
            # Use live quote first, fallback to historical close
            price = self.get_live_price(stock)
            if price == 0.0:
                cache_key = f"{stock}_{self.interval_var.get()}"
                df = self.data_cache.get(cache_key, pd.DataFrame())
                if df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                    if df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                        logging.warning(f"No valid data for {stock}, cannot buy")
                        self.status_label.config(text=f"No data for {stock}")
                        if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                            self.speak(f"No data for {stock}")
                        beep()
                        return
                    self.data_cache[cache_key] = df
                price = df['Close'].iloc[-1]
            shares_input = self.shares_entry.get().strip()
            if not shares_input:
                logging.warning("No shares input provided")
                self.status_label.config(text="Enter number of shares")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Enter number of shares")
                beep()
                return
            try:
                shares = int(shares_input)
                if shares <= 0:
                    raise ValueError("Shares must be positive")
            except ValueError:
                logging.warning(f"Invalid shares input: {shares_input}")
                self.status_label.config(text="Invalid shares input")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Invalid shares input")
                beep()
                return
            total_cost = price * shares
            if total_cost > self.base_cash:
                logging.warning(f"Insufficient funds to buy {shares} shares of {stock}")
                self.status_label.config(text="Insufficient funds")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Insufficient funds")
                beep()
                return
            self.base_cash -= total_cost
            self.cash_label.config(text=f"Cash: ${self.base_cash:.2f}")
            self.portfolio[stock] = self.portfolio.get(stock, 0) + shares
            self.cost_basis[stock] = ((self.cost_basis.get(stock, 0) * self.portfolio.get(stock, 0)) + total_cost) / self.portfolio[stock]
            self.transaction_history.setdefault(stock, []).append({
                'action': 'Buy',
                'shares': shares,
                'price': price,
                'timestamp': datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z"),
                'mode': self.trading_mode
            })
            self.save_transaction_history()
            self.save_portfolio()
            # Force-refresh cache and update tab after buy
            cache_key = f"{stock}_{self.interval_var.get()}"
            df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
            if not df.empty and 'Close' in df.columns and not df['Close'].isna().all():
                self.data_cache[cache_key] = df
            self.update_portfolio_table()
            self.update_history_table()
            self.update_tab_labels()  # Refresh tab price
            logging.info(f"Bought {shares} shares of {stock} at ${price:.2f}")
            self.status_label.config(text=f"Bought {shares} of {stock} at ${price:.2f}")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"Bought {shares} shares of {stock} at {price:.2f} dollars")
            beep()
        except Exception as e:
            logging.error(f"Error buying stock: {e}")
            self.status_label.config(text="Error buying stock")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error buying stock")
            beep()
			
    def sell_stock(self):
        logging.debug("Initiating sell stock")
        try:
            stock = self.current_stock
            if not stock or stock == "***" or stock == "Backtest":
                logging.warning("No valid stock selected for sell")
                self.status_label.config(text="Select a valid stock to sell")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Select a valid stock to sell")
                beep()
                return
            shares_input = self.shares_entry.get().strip()
            if not shares_input:
                logging.warning("No shares input provided")
                self.status_label.config(text="Enter number of shares")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Enter number of shares")
                beep()
                return
            try:
                shares = int(shares_input)
                if shares <= 0:
                    raise ValueError("Shares must be positive")
            except ValueError as e:
                logging.error(f"Invalid shares input: {shares_input}")
                self.status_label.config(text="Invalid shares input")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Invalid shares input")
                beep()
                return
            if stock not in self.portfolio or self.portfolio[stock] < shares:
                logging.warning(f"Insufficient shares to sell {shares} of {stock}")
                self.status_label.config(text="Insufficient shares")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Insufficient shares")
                beep()
                return
            cache_key = f"{stock}_{self.interval_var.get()}"
            df = self.data_cache.get(cache_key, pd.DataFrame())
            if df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                if df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                    logging.warning(f"No valid data for {stock}")
                    self.status_label.config(text=f"No data for {stock}")
                    if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                        self.speak(f"No data for {stock}")
                    beep()
                    return
                self.data_cache[cache_key] = df
            price = df['Close'].iloc[-1]
            self.base_cash += price * shares
            self.cash_label.config(text=f"Cash: ${self.base_cash:.2f}")
            self.portfolio[stock] -= shares
            if self.portfolio[stock] == 0:
                del self.portfolio[stock]
                del self.cost_basis[stock]
                if stock in self.manual_purchases:
                    self.manual_purchases.remove(stock)
                    try:
                        with open("manual_purchases.json", "w") as f:
                            json.dump(list(self.manual_purchases), f, indent=2)
                        logging.info("Saved manual purchases to manual_purchases.json")
                    except Exception as e:
                        logging.error(f"Error saving manual purchases: {e}")
            else:
                old_per_share = self.cost_basis.get(stock, price)
                total_original_cost = old_per_share * (self.portfolio[stock] + shares)
                cost_sold = old_per_share * shares
                remaining_cost = total_original_cost - cost_sold
                self.cost_basis[stock] = remaining_cost / self.portfolio[stock] if self.portfolio[stock] > 0 else 0
            self.transaction_history.setdefault(stock, []).append({
                'action': 'Sell',
                'shares': shares,
                'price': price,
                'timestamp': datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z")
            })
            self.save_transaction_history()
            self.save_portfolio()
            self.update_portfolio_table()
            self.update_history_table()
            logging.info(f"Sold {shares} shares of {stock} at ${price:.2f}")
            self.status_label.config(text=f"Sold {shares} of {stock} at ${price:.2f}")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"Sold {shares} shares of {stock}")
            beep()
        except Exception as e:
            logging.error(f"Error selling stock: {e}")
            self.status_label.config(text="Error selling stock")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error selling stock")
            beep()
			
    def sell_all_stocks(self):
        logging.debug("Selling all stocks")
        try:
            for stock in list(self.portfolio.keys()):
                shares = self.portfolio[stock]
                if shares > 0:
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    df = self.data_cache.get(cache_key, pd.DataFrame())
                    price = None
                    cache_file = os.path.join(os.getcwd(), "stock_cache.json")
                    if not self.is_market_open() and os.path.exists(cache_file):
                        try:
                            with open(cache_file, "r") as f:
                                cached_data = json.load(f)
                            if cache_key in cached_data:
                                df = pd.DataFrame(cached_data[cache_key])
                                if not df.empty and "Close" in df.columns and not pd.isna(df["Close"].iloc[-1]):
                                    price = df["Close"].iloc[-1]
                                    logging.debug(f"Loaded cached price for {stock}: ${price:.2f}")
                        except Exception as e:
                            logging.error(f"Error loading cached data for {stock}: {e}")
                    if price is None or df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                        price = self.cost_basis.get(stock, 0.0)
                        logging.debug(f"Using cost basis ${price:.2f} for {stock}")
                    total_value = shares * price
                    self.base_cash += total_value
                    self.transaction_history.setdefault(stock, []).append({
                        "timestamp": datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z"),
                        "action": "Sell",
                        "shares": shares,
                        "price": price,
                        "mode": self.trading_mode
                    })
                    del self.portfolio[stock]
                    if stock in self.cost_basis:
                        del self.cost_basis[stock]
                    if stock in self.tabs and stock not in self.added_stocks:
                        self.notebook.forget(self.tabs[stock])
                        del self.tabs[stock]
                        del self.signal_labels[stock]
                        del self.indicator_tables[stock]
                        if stock in self.stocks:
                            self.stocks.remove(stock)
                    logging.info(f"Sold {shares} shares of {stock} at ${price:.2f}")
            self.status_label.config(text="Sold all shares")
            self.speak("Sold all shares")
            beep()
            self.save_transaction_history()
            self.save_portfolio()
            self.update_portfolio_table()
            self.update_history_table()
            self.update_tab_labels()
        except Exception as e:
            logging.error(f"Error selling all stocks: {e}")
            self.status_label.config(text="Error selling all stocks")
            self.speak("Error selling all stocks")
            beep()		
			
    # Snippet 176: Fix clear_transaction_history to use fixed path
    def clear_transaction_history(self):
        logging.debug("Checking if transaction history should be cleared")
        try:
            now = datetime.now(pytz.timezone("America/New_York"))
            market_open = now.replace(hour=6, minute=0, second=0, microsecond=0)
            last_clear = getattr(self, 'last_clear_date', now.date() - timedelta(days=1))
            logging.debug(f"Current time: {now}, Market open: {market_open}, Last clear date: {last_clear}")
            if self.is_market_open() and now >= market_open and now.date() > last_clear:
                logging.info("Clearing transaction history at market open")
                self.transaction_history = {}
                history_file = os.path.join(r"C:\Users\dad\StockApp", "transaction_history.json")
                os.makedirs(os.path.dirname(history_file), exist_ok=True)
                with open(history_file, "w") as f:
                    json.dump({}, f)
                self.last_clear_date = now.date()
                logging.info("Transaction history cleared successfully")
            else:
                logging.debug("Transaction history not cleared: conditions not met")
        except Exception as e:
            logging.error(f"Error clearing transaction history: {e}")
            self.speak("Error clearing transaction history")
            beep()
			
    # Snippet 178: Remove clear_transaction_history from update_timer (replace update_timer in part 5)
    def update_timer(self):
        logging.debug("Updating timer")
        try:
            self.update_data()
            after_id = self.root.after(1000, self.update_timer)
            self.after_ids.append(after_id)
        except Exception as e:
            logging.error(f"Error in update_timer: {e}")
            self.speak("Error updating timer")
            beep()		
			
    def update_all_tab_signals(self):
        logging.debug("Updating all tab signals")
        for stock in self.stocks:
            self.update_tab_signal(stock)	
			
    def update_portfolio_table(self):
        logging.debug("Updating portfolio table")
        if getattr(self, 'zone_period_updating', False):
            logging.debug("Skipping portfolio table update: zone period update in progress")
            return
        try:
            for item in self.portfolio_tree.get_children():
                self.portfolio_tree.delete(item)
            total_value = self.base_cash
            total_pl = 0.0
            for stock, shares in self.portfolio.items():
                price = self.get_live_price(stock)
                if price == 0.0:
                    logging.error(f"No price data for {stock}, skipping portfolio update")
                    continue
                cache_key = f"{stock}_{self.interval_var.get()}"
                df = self.data_cache.get(cache_key)
                # Prioritize manual thresholds from JSON if period matches
                logging.debug(f"Manual check for {stock}: {self.manual_thresholds.get(stock)}")
                if stock in self.manual_thresholds and self.manual_thresholds[stock].get('period') == self.zone_period:
                    target = self.manual_thresholds[stock].get('target', price * 1.05)
                    stop_loss = self.manual_thresholds[stock].get('stop', price * 0.95)
                    logging.debug(f"Using manual thresholds for {stock}: target=${target:.2f}, stop_loss=${stop_loss:.2f}")
                else:
                    # Fall back to loaded supply/demand thresholds if available
                    if stock in self.supply_thresholds and stock in self.demand_thresholds and self.threshold_zone_periods.get(stock) == self.zone_period:
                        target = self.supply_thresholds[stock]
                        stop_loss = self.demand_thresholds[stock]
                        logging.debug(f"Using loaded thresholds for {stock}: target=${target:.2f}, stop_loss=${stop_loss:.2f}")
                    else:
                        if df is None or df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                            logging.debug(f"No cached data for {stock}, using default thresholds")
                            target = price * 1.05
                            stop_loss = price * 0.95
                        else:
                            df = self.calculate_indicators(df, stock)
                            self.data_cache[cache_key] = df
                            target = df["supply_zone"].iloc[-1] if 'supply_zone' in df and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.05
                            stop_loss = df["demand_zone"].iloc[-1] if 'demand_zone' in df and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.95
                            if target <= price or stop_loss >= price:
                                logging.debug(f"Recalculating thresholds for {stock}: target={target:.2f}, stop_loss={stop_loss:.2f}, price={price:.2f}")
                                target = price * 1.05
                                stop_loss = price * 0.95
                    # Clear manual thresholds if period doesn't match
                    if stock in self.manual_thresholds and self.manual_thresholds[stock].get('period') != self.zone_period:
                        del self.manual_thresholds[stock]
                        logging.debug(f"Cleared manual thresholds for {stock} due to period mismatch")
                self.supply_thresholds[stock] = target
                self.demand_thresholds[stock] = stop_loss
                self.threshold_zone_periods[stock] = self.zone_period
                cost = self.cost_basis.get(stock, price)
                pl = (price - cost) * shares
                pl_percent = ((price - cost) / cost * 100) if cost != 0 else 0.0
                total_value += price * shares
                total_pl += pl
                tags = ('profit' if pl > 0 else 'loss') if pl != 0 else ''
                self.portfolio_tree.insert("", "end", values=(
                    stock, 
                    shares, 
                    f"${cost:.2f}", 
                    f"${price:.2f}", 
                    f"${target:.2f}", 
                    f"${stop_loss:.2f}", 
                    f"${pl:.2f}", 
                    f"{pl_percent:.2f}%"
                ), tags=tags)
                logging.debug(f"Portfolio row for {stock}: price=${price:.2f}, target=${target:.2f}, stop_loss=${stop_loss:.2f}, pl=${pl:.2f}, pl_percent={pl_percent:.2f}%")
            self.cash_label.config(text=f"Cash: ${self.base_cash:.2f}")
            self.stocks_value_label.config(text=f"Stocks Value: ${(total_value - self.base_cash):.2f}")
            self.total_value_label.config(text=f"Total Value: ${total_value:.2f}")
            self.total_pl_label.config(text=f"Total P/L: ${total_pl:.2f}")
            logging.debug(f"Portfolio table updated: total_value=${total_value:.2f}, total_pl=${total_pl:.2f}")
        except Exception as e:
            logging.error(f"Error updating portfolio table: {e}")
            self.status_label.config(text="Error updating portfolio")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error updating portfolio")
				
# Snippet 149: Fixed on_portfolio_double_click to correct target and stop loss
    def on_portfolio_double_click(self, event):
        logging.debug("Portfolio double-click event")
        try:
            selection = self.portfolio_tree.selection()
            if not selection:
                logging.debug("No portfolio item selected")
                return
            item = self.portfolio_tree.item(selection[0])
            stock = item['values'][0]
            logging.debug(f"Double-clicked stock: {stock}")
            self.current_stock = stock
            # Get current price to validate thresholds
            price = self.get_live_price(stock)
            if price == 0.0:
                cache_key = f"{stock}_{self.interval_var.get()}"
                df = self.data_cache.get(cache_key, pd.DataFrame())
                if not df.empty and 'Close' in df.columns and not df['Close'].isna().all():
                    price = df['Close'].iloc[-1]
                else:
                    logging.warning(f"No valid price for {stock}, using default")
                    price = self.cost_basis.get(stock, 0.0)
            # Ensure target is above price and stop loss is below
            default_target = price * 1.05  # 5% above current price
            default_stop_loss = price * 0.95  # 5% below current price
            target = self.supply_thresholds.get(stock, default_target)
            stop_loss = self.demand_thresholds.get(stock, default_stop_loss)
            # Validate that target > price > stop_loss
            if target <= price or stop_loss >= price:
                logging.warning(f"Invalid thresholds for {stock}: target={target:.2f}, stop_loss={stop_loss:.2f}, price={price:.2f}. Resetting to defaults.")
                target = default_target
                stop_loss = default_stop_loss
                self.supply_thresholds[stock] = target
                self.demand_thresholds[stock] = stop_loss
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, f"{target:.2f}")
            self.stop_loss_entry.delete(0, tk.END)
            self.stop_loss_entry.insert(0, f"{stop_loss:.2f}")
            logging.debug(f"Populated target={target:.2f}, stop_loss={stop_loss:.2f} for {stock}")
            # Save updated thresholds
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds.json")
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": self.supply_thresholds,
                "demand_thresholds": self.demand_thresholds
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info(f"Saved thresholds to {thresholds_file}")
            except Exception as e:
                logging.error(f"Error saving thresholds: {e}")
                self.status_label.config(text="Error saving thresholds")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Error saving thresholds")
                beep()
        except Exception as e:
            logging.error(f"Error in portfolio double-click: {e}")
            self.status_label.config(text="Error selecting stock")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error selecting stock")	
				
    # Snippet 197: Fixed update_tab_labels to handle None price and skip invalid stocks (replace existing method)
    def update_tab_labels(self):
        logging.debug(f"Updating tab labels for {len(self.stocks)} stocks")
        try:
            self._updating_labels = True  # Flag to ignore tab change events
            if not hasattr(self, 'tabs'):
                self.tabs = {}
                logging.debug("Initialized self.tabs as empty dict")
            for stock in self.stocks:
                if stock in ["***", "Backtest"]:
                    continue
                # Use live price if available, fallback to cached close
                price = self.get_live_price(stock)
                if price is None or price == 0.0:
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    if cache_key in self.data_cache and isinstance(self.data_cache[cache_key], pd.DataFrame) and not self.data_cache[cache_key].empty and "Close" in self.data_cache[cache_key]:
                        price = self.data_cache[cache_key]["Close"].iloc[-1]
                    else:
                        logging.warning(f"No valid price or cache for {stock}, marking invalid")
                        self.invalid_stocks.add(stock)
                        if stock in self.stocks:
                            self.stocks.remove(stock)
                        if stock in self.tabs:
                            self.notebook.forget(self.tabs[stock])
                            del self.tabs[stock]
                            del self.signal_labels[stock]
                            del self.indicator_tables[stock]
                        continue
                if stock in self.tabs and self.notebook.winfo_exists() and self.notebook.index(self.tabs[stock]) >= 0:
                    self.notebook.tab(self.tabs[stock], text=f"{stock} ${price:.2f}")
                    logging.debug(f"Updated tab label for {stock} to ${price:.2f}")
                else:
                    logging.debug(f"Skipping tab update for {stock}: not in notebook or invalid")
            # Save updated invalid_stocks
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds.json")
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items()},
                "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items()},
                "threshold_zone_periods": self.threshold_zone_periods,
                "highest_price": {k: float(v) for k, v in getattr(self, 'highest_price', {}).items()}
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info(f"Saved thresholds with invalid_stocks to {thresholds_file}")
            except Exception as e:
                logging.error(f"Error saving thresholds: {e}")
            self._updating_labels = False
            logging.info("Completed updating tab labels")
        except Exception as e:
            logging.error(f"Failed to update tab labels: {e}")
            self._updating_labels = False
            self.root.after(0, lambda: self.status_label.config(text="Error updating tab labels"))
            self.root.after(0, lambda: self.speak("Error updating tab labels"))
            self.root.after(0, beep)
			
    # Snippet 203: Updated update_stocks to initialize thresholds for all stocks (replace existing)
    def update_stocks(self):
        logging.debug("Updating stocks")
        try:
            self.data_cache.clear()
            cache_file = os.path.join(r"C:\Users\dad\StockApp", "stock_cache.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logging.info(f"Cleared cache: {cache_file}")
            held_stocks = sorted(set(self.day_portfolio.keys()) | set(self.swing_portfolio.keys()))
            logging.info(f"Held stocks: {held_stocks}")
            screener_stocks = self.fetch_screener_stocks()
            # Cap screener stocks at 10, prioritize high volume
            if len(screener_stocks) > 10:
                screener_stocks = sorted(screener_stocks, key=lambda s: self.get_stock_volume(s), reverse=True)[:10]
                logging.info(f"Capped screener stocks at 10 high-volume: {screener_stocks}")
            logging.info(f"Fetched screener stocks: {screener_stocks}")
            new_stocks = held_stocks[:]
            new_stocks.extend([s for s in sorted(self.added_stocks) if s not in new_stocks])
            new_stocks.extend([s for s in screener_stocks if s not in new_stocks])
            logging.debug(f"New stocks: {new_stocks}")
            removed_stocks = [stock for stock in self.stocks if stock not in new_stocks and stock != "Backtest"]
            for stock in removed_stocks:
                if stock in self.tabs:
                    self.notebook.forget(self.tabs[stock])
                    del self.tabs[stock]
                    del self.signal_labels[stock]
                    del self.indicator_tables[stock]
            self.stocks = new_stocks
            logging.info(f"Updated stocks: {self.stocks}")
            for stock in self.stocks:
                if stock not in self.tabs:
                    self.create_tab_for_stock(stock)
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                    if not isinstance(df, pd.DataFrame) or df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                        logging.warning(f"No valid data for {stock}, creating placeholder tab")
                        self.create_tab_for_stock(stock, placeholder=True)
                        continue
                    df = self.calculate_indicators(df, stock)
                    with self.cache_lock:
                        self.data_cache[cache_key] = df
                    # Initialize thresholds if not set
                    price = df["Close"].iloc[-1] if not df.empty and "Close" in df.columns else self.get_live_price(stock) or 0.0
                    if stock not in self.supply_thresholds or stock not in self.demand_thresholds or self.threshold_zone_periods.get(stock) != self.zone_period:
                        self.supply_thresholds[stock] = df["supply_zone"].iloc[-1] if 'supply_zone' in df and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.05
                        self.demand_thresholds[stock] = df["demand_zone"].iloc[-1] if 'demand_zone' in df and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.95
                        self.threshold_zone_periods[stock] = self.zone_period
                        logging.debug(f"Initialized thresholds for {stock}: supply=${self.supply_thresholds[stock]:.2f}, demand=${self.demand_thresholds[stock]:.2f}")
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, "w") as f:
                    json.dump({k: v.reset_index().to_dict('records') for k, v in self.data_cache.items()}, f, indent=2)
                logging.info(f"Saved cache data: {cache_file}")
            except Exception as e:
                logging.error(f"Error saving cache: {e}")
            # Save thresholds
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", f"thresholds_{self.zone_period}.json")
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items()},
                "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items()},
                "threshold_zone_periods": self.threshold_zone_periods,
                "manual_thresholds": {k: {sk: float(sv) if isinstance(sv, (int, float)) else sv for sk, sv in v.items()} for k, v in self.manual_thresholds.items()}
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info(f"Saved thresholds to {thresholds_file}")
            except Exception as e:
                logging.error(f"Error saving thresholds: {e}")
            self.update_tab_labels()
        except Exception as e:
            logging.error(f"Error updating stocks: {e}")
            self.status_label.config(text="Error updating stocks")
            self.speak("Error updating stocks")
            beep()
            
    def refresh_screener(self):
        logging.debug("Refreshing screener stocks")
        try:
            self.data_cache.clear()
            screener_stocks = self.fetch_screener_stocks()
            logging.info(f"Fetched screener stocks: {screener_stocks}")
            held_stocks = sorted(set(self.day_portfolio.keys()) | set(self.swing_portfolio.keys()) | set(self.added_stocks))
            new_stocks = held_stocks + [s for s in screener_stocks if s not in held_stocks and s not in ["***", "Backtest"]]
            logging.debug(f"New stocks: {new_stocks}")
            for stock in list(self.stocks):
                if stock not in new_stocks and stock not in ["***", "Backtest"]:
                    if stock in self.tabs:
                        self.notebook.forget(self.tabs[stock])
                        del self.tabs[stock]
                        del self.signal_labels[stock]
                        del self.indicator_tables[stock]
                        logging.debug(f"Removed tab for {stock}")
            self.stocks = new_stocks
            logging.info(f"Updated stocks: {self.stocks}")
            for stock in self.stocks:
                if stock not in self.tabs and stock not in ["***", "Backtest"]:
                    self.create_tab_for_stock(stock)
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                    if not isinstance(df, pd.DataFrame) or df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                        logging.warning(f"No valid data for {stock}, creating placeholder tab")
                        self.create_tab_for_stock(stock, placeholder=True)
                        continue
                    df = self.calculate_indicators(df, stock)
                    self.data_cache[cache_key] = df
                    self.update_tab_signal(stock)
                    self.notebook.select(self.tabs[stock])
                    logging.debug(f"Created tab for {stock}")
            cache_file = os.path.join(r"C:\Users\dad\StockApp", "stock_cache.json")
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                serializable_cache = {}
                for key, df in self.data_cache.items():
                    df_reset = df.reset_index()
                    df_reset['date'] = df_reset['date'].astype(str)
                    serializable_cache[key] = df_reset.to_dict('records')
                with open(cache_file, "w", encoding='utf-8') as f:
                    json.dump(serializable_cache, f, indent=2)
                logging.info(f"Saved cache data to {cache_file}")
            except Exception as e:
                logging.error(f"Error saving cache: {e}")
            self.update_portfolio_table()
            self.update_tab_labels()
            self.notebook.update_idletasks()
            self.status_label.config(text="Screener refreshed")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Screener refreshed")
            beep()
        except Exception as e:
            logging.error(f"Error refreshing screener: {e}")
            self.status_label.config(text="Error refreshing screener")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error refreshing screener")
            beep()
					
    # Snippet 199: Removed popup from toggle_auto_trading, defaults to mock mode (replace existing from Snippet 192)
    def toggle_auto_trading(self):
        logging.debug("Toggling auto trading")
        try:
            self.use_auto_trading = not self.use_auto_trading
            if self.use_auto_trading:
                self.trading_mode_flag = "mock"  # Default to mock
                self.auto_trade_button.config(text=f"Using Auto ({self.trading_mode_flag})")
                logging.info(f"Auto trading enabled in {self.trading_mode_flag} mode")
                self.status_label.config(text=f"Auto trading enabled ({self.trading_mode_flag})")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak(f"Auto trading enabled in {self.trading_mode_flag} mode")
                after_id = self.root.after(5000, self.run_auto_trade)
                self.after_ids.append(after_id)
            else:
                self.trading_mode_flag = None
                self.auto_trade_button.config(text="Using Manual")
                logging.info("Auto trading disabled")
                self.status_label.config(text="Auto trading disabled")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Auto trading disabled")
                for after_id in self.after_ids:
                    self.root.after_cancel(after_id)
                self.after_ids.clear()
            beep()
        except Exception as e:
            logging.error(f"Error toggling auto trading: {e}")
            self.status_label.config(text="Error toggling auto trading")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error toggling auto trading")
            for after_id in self.after_ids:
                self.root.after_cancel(after_id)
            self.after_ids.clear()
            beep()
            
    def toggle_trading_mode(self):
        logging.debug("Toggling trading mode")
        try:
            self.trading_mode = "swing" if self.trading_mode == "day" else "day"
            self.portfolio = self.swing_portfolio if self.trading_mode == "swing" else self.day_portfolio
            self.cost_basis = self.swing_cost_basis if self.trading_mode == "swing" else self.day_cost_basis
            self.save_transaction_history()
            stock_list = self.fetch_screener_stocks()
            held_stocks = sorted(self.day_portfolio.keys() if self.trading_mode == "day" else self.swing_portfolio.keys())
            added_stocks = sorted(self.added_stocks)
            fetched_stocks = [s for s in stock_list if s not in held_stocks and s not in self.added_stocks]
            self.stocks = list(dict.fromkeys(held_stocks + added_stocks + ["***"] + fetched_stocks))
            for tab_id in self.notebook.tabs():
                self.notebook.forget(tab_id)
            self.tabs.clear()
            self.signal_labels.clear()
            self.indicator_tables.clear()
            if hasattr(self, 'held_notebook'):
                self.held_notebook.destroy()
            if hasattr(self, 'fetched_notebook'):
                self.fetched_notebook.destroy()
            for stock in self.stocks:
                if stock == "***":
                    self.create_tab_for_stock(stock)
                    continue
                if stock in self.tabs:
                    logging.debug(f"Skipping duplicate tab for {stock}")
                    continue
                cache_key = f"{stock}_{self.interval_var.get()}"
                df = self.data_cache.get(cache_key, pd.DataFrame())
                if df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                price = df["Close"].iloc[-1] if not df.empty and "Close" in df.columns and not pd.isna(df["Close"].iloc[-1]) else self.cost_basis.get(stock, 0.0)
                if price > 20 and stock not in self.day_portfolio and stock not in self.swing_portfolio and stock not in self.added_stocks:
                    logging.warning(f"Skipping tab creation for {stock}: Price ${price:.2f} exceeds $20")
                    if stock in self.stocks:
                        self.stocks.remove(stock)
                    continue
                self.create_tab_for_stock(stock, placeholder=False)
                if df is not None and not df.empty:
                    df = self.calculate_indicators(df, stock)
                    self.data_cache[cache_key] = df
                    self.supply_thresholds[stock] = df["supply_zone"].iloc[-1] if 'supply_zone' in df and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.1
                    self.demand_thresholds[stock] = df["demand_zone"].iloc[-1] if 'demand_zone' in df and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.9
                else:
                    df = pd.DataFrame({
                        "Open": [price], "High": [price], "Low": [price], "Close": [price], "Volume": [0]
                    }, index=[pd.Timestamp.now()])
                    df.index.name = "date"
                    df = self.calculate_indicators(df, stock)
                    self.data_cache[cache_key] = df
                    self.supply_thresholds[stock] = price * 1.1
                    self.demand_thresholds[stock] = price * 0.9
                self.update_tab_signal(stock)
                self.root.update_idletasks()
            self.transaction_history = self.load_transaction_history()
            self.update_portfolio_table()
            self.update_history_table()
            self.update_tab_labels()
            if self.current_stock and self.current_stock in self.stocks and self.current_stock != "***":
                cache_key = f"{self.current_stock}_{self.interval_var.get()}"
                df = self.data_cache.get(cache_key, pd.DataFrame())
                if df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                    df = self.fetch_data(self.current_stock, self.interval_var.get(), force_fetch=True)
                    if df is not None and not df.empty:
                        df = self.calculate_indicators(df, self.current_stock)
                        self.data_cache[cache_key] = df
                price = df["Close"].iloc[-1] if "Close" in df and not pd.isna(df["Close"].iloc[-1]) else self.cost_basis.get(self.current_stock, 0.0)
                supply = df['supply_zone'].iloc[-1] if 'supply_zone' in df and not pd.isna(df['supply_zone'].iloc[-1]) else price * 1.1
                demand = df['demand_zone'].iloc[-1] if 'demand_zone' in df and not pd.isna(df['demand_zone'].iloc[-1]) else price * 0.9
                self.target_entry.delete(0, tk.END)
                self.target_entry.insert(0, f"{supply:.2f}")
                self.stop_loss_entry.delete(0, tk.END)
                self.stop_loss_entry.insert(0, f"{demand:.2f}")
                self.entry_frame.pack(fill="x", pady=5)
            logging.info(f"Switched to {self.trading_mode} trading")
            self.status_label.config(text=f"Switched to {self.trading_mode} trading")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"Switched to {self.trading_mode} trading")
            beep()
        except Exception as e:
            logging.error(f"Error toggling trading mode: {e}")
            self.status_label.config(text="Error toggling trading mode")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error toggling trading mode")
            beep()            
			
    # Snippet 302: Updated run_auto_trade with manual threshold reset and cache path check
    def run_auto_trade(self):
        logging.debug("Running auto trade")
        try:
            if not self.is_market_open():
                logging.debug("Auto trade skipped: market closed")
                after_id = self.root.after(5000, self.run_auto_trade)
                self.after_ids.append(after_id)
                return
            if not self.use_auto_trading:
                logging.debug("Auto trading disabled, enabling for debugging")
                self.use_auto_trading = True
                self.auto_trade_button.config(text="Using Auto")
                self.status_label.config(text="Auto trading enabled")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Auto trading enabled")
            current_time = datetime.now(pytz.timezone("America/New_York")).timestamp()
            save_thresholds = False  # Flag for periodic saves
            cache_dir = os.path.join(r"C:\Users\dad\StockApp", "cache")
            logging.debug("Using cache directory: {}".format(cache_dir))
            # Batch fetch live prices
            valid_stocks = [s for s in self.stocks if s not in ["***", "Backtest"] and s in self.signal_labels and s in self.indicator_tables]
            stock_prices = self.batch_get_live_prices(valid_stocks)
            self.trade_counter += 1  # Increment trade ID
            run_id = datetime.now(pytz.timezone("America/New_York")).strftime('%Y%m%d_%H%M%S')
            for stock in valid_stocks:
                last_buy = self.last_trade_time.get("{}_buy".format(stock), 0)
                last_sell = self.last_trade_time.get("{}_sell".format(stock), 0)
                if current_time - last_buy < 300:  # 5min cooldown for buys
                    logging.debug("Skipping {}: within 5-minute buy cooldown".format(stock))
                    continue
                if current_time - last_sell < 60:  # 1min cooldown for sells
                    logging.debug("Skipping {}: within 1-minute sell cooldown".format(stock))
                    continue
                cache_key = "{}_{}".format(stock, self.interval_var.get())
                df = self.data_cache.get(cache_key, pd.DataFrame())
                last_fetch = self.last_fetch_time.get(cache_key, 0)
                if (not isinstance(df, pd.DataFrame) or df.empty or 'Close' not in df.columns or
                    df['Close'].isna().all() or len(df) < 100 or current_time - last_fetch > 300):
                    logging.debug("Fetching fresh data for {}: cache invalid or stale".format(stock))
                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                    self.data_cache[cache_key] = df
                    self.last_fetch_time[cache_key] = current_time
                if not isinstance(df, pd.DataFrame) or df.empty or 'Close' not in df.columns or df['Close'].isna().all() or len(df) < 100:
                    avg_vol = df["Volume"].rolling(14).mean().iloc[-1] if not df.empty else 0
                    if avg_vol < 500:
                        logging.debug("Low-vol skip for {}: {}, no alert".format(stock, avg_vol))
                        continue
                    logging.warning("No valid data for {} after fetch, skipping auto trade".format(stock))
                    self.status_label.config(text="Critical: No data for {}".format(stock))
                    self.speak("Critical: No data for {}".format(stock))
                    continue
                avg_volume = df["Volume"].rolling(window=14, min_periods=1).mean().iloc[-1]
                price = df['Close'].iloc[-1]  # Use for volume filter
                min_volume = 500 if price < 5 else 1000  # Flexible: lower for penny stocks
                if avg_volume < min_volume:
                    logging.debug("Skipping {}: average volume {} below {}".format(stock, avg_volume, min_volume))
                    continue
                df = self.calculate_indicators(df, stock)
                self.data_cache[cache_key] = df
                price = stock_prices.get(stock, 0.0)
                if price == 0.0:
                    price = df['Close'].iloc[-1]
                    logging.warning("Using historical price for {}: ${:.4f}".format(stock, price))
                if price == 0.0:
                    logging.warning("No price for {}, skipping auto trade".format(stock))
                    continue
                self.update_tab_signal(stock)
                signal = self.signal_labels[stock].cget("text").split(": ")[1]
                buy_signals = sum(1 for ind in ["mfi", "macd", "stochastic", "ema13", "cci", "obv", "vwap", "demand_zone"] if
                                  self.indicator_visibility.get("{}_{}".format(stock, ind), tk.BooleanVar(value=True)).get() and ind in df.columns and
                                  not pd.isna(df[ind].iloc[-1]) and (
                                      (ind == "mfi" and df[ind].iloc[-1] < 20) or
                                      (ind == "macd" and df[ind].iloc[-1] > 1e-6) or
                                      (ind == "stochastic" and df[ind].iloc[-1] < 20) or
                                      (ind == "ema13" and df["Close"].iloc[-1] > df[ind].iloc[-1]) or
                                      (ind == "cci" and df[ind].iloc[-1] < -50) or
                                      (ind == "obv" and df[ind].diff().iloc[-1] > 0) or
                                      (ind == "vwap" and df["Close"].iloc[-1] < df[ind].iloc[-1]) or
                                      (ind == "demand_zone" and df["Close"].iloc[-1] < df[ind].iloc[-1])))
                active_indicators = sum(1 for ind in ["mfi", "macd", "stochastic", "ema13", "cci", "obv", "vwap", "demand_zone"] if
                                        self.indicator_visibility.get("{}_{}".format(stock, ind), tk.BooleanVar(value=True)).get() and ind in df.columns and
                                        not pd.isna(df[ind].iloc[-1]))
                logging.debug("Auto trade debug for {}: signal={}, buy_signals={}, active_indicators={}, threshold={}, volume={}, cash=${:.2f}, in_portfolio={}, manual_purchases={}".format(
                    stock, signal, buy_signals, active_indicators, self.buy_threshold.get(), avg_volume, self.base_cash, stock in self.portfolio, stock in self.manual_purchases))
                risk_amount = self.base_cash * 0.01
                shares_to_trade = min(max(int(risk_amount / price), 1), 1000)
                manual_target = self.manual_thresholds.get(stock, {}).get('target')
                manual_stop = self.manual_thresholds.get(stock, {}).get('stop')
                supply = manual_target if manual_target is not None else (self.supply_thresholds.get(stock) or (df["supply_zone"].iloc[-1] if "supply_zone" in df.columns and not pd.isna(df["supply_zone"].iloc[-1]) else None))
                demand = manual_stop if manual_stop is not None else (self.demand_thresholds.get(stock) or (df["demand_zone"].iloc[-1] if "demand_zone" in df.columns and not pd.isna(df["demand_zone"].iloc[-1]) else None))
                if supply is None or demand is None:
                    logging.warning("No valid zones for {}, skipping trade".format(stock))
                    continue
                # Validate manual target and reset if invalid
                if manual_target is not None and (manual_target <= price or manual_stop >= price):
                    logging.warning("Invalid manual thresholds for {}: target=${:.4f}, stop=${:.4f}, price=${:.4f}, resetting to auto".format(stock, manual_target or 0, manual_stop or 0, price))
                    supply = df["supply_zone"].iloc[-1] if "supply_zone" in df.columns and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.20
                    demand = df["demand_zone"].iloc[-1] if "demand_zone" in df.columns and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.80
                    self.manual_thresholds[stock] = {'target': supply, 'stop': demand, 'period': self.zone_period}
                    save_thresholds = True
                # Ratio check: (target - price) / (price - stop) >= 1
                risk_reward_ratio = (supply - price) / (price - demand) if (price - demand) > 0 else 0
                logging.debug("Zone distances for {}: price=${:.4f}, supply=${:.4f} (distance={:.4f}), demand=${:.4f} (distance={:.4f}), ratio={:.1f}:1".format(
                    stock, price, supply, supply - price, demand, price - demand, risk_reward_ratio))
                if risk_reward_ratio < 1:
                    logging.debug("Skipping {}: risk-reward ratio {:.1f}:1 below 1:1".format(stock, risk_reward_ratio))
                    continue
                old_supply = self.supply_thresholds.get(stock, supply)
                trailing_active = stock in self.highest_price
                if price >= supply * 0.995:
                    if not trailing_active:
                        self.highest_price[stock] = price
                        trailing_active = True
                    elif price > self.highest_price[stock]:
                        self.highest_price[stock] = price
                        save_thresholds = True
                    self.supply_thresholds[stock] = self.highest_price[stock]
                    self.demand_thresholds[stock] = old_supply * 0.99
                    if stock in self.manual_thresholds:
                        self.manual_thresholds[stock]['target'] = self.supply_thresholds[stock]
                        self.manual_thresholds[stock]['stop'] = self.demand_thresholds[stock]
                    logging.debug("Updated trailing stop for {}: price=${:.4f}, old_supply=${:.4f}, new_target=${:.4f}, stop=${:.4f}".format(
                        stock, price, old_supply, self.supply_thresholds[stock], self.demand_thresholds[stock]))
                if stock not in self.portfolio and signal == "Buy":
                    self.supply_thresholds[stock] = supply
                    self.demand_thresholds[stock] = demand
                    if stock in self.manual_thresholds:
                        self.manual_thresholds[stock]['target'] = supply
                        self.manual_thresholds[stock]['stop'] = demand
                    save_thresholds = True
                if stock not in self.supply_thresholds or stock not in self.demand_thresholds:
                    logging.warning("Thresholds not set for {}, skipping trade".format(stock))
                    continue
                logging.debug("Thresholds for {}: supply=${:.4f}, demand=${:.4f}, shares_to_trade={}, ratio={:.1f}:1".format(
                    stock, self.supply_thresholds[stock], self.demand_thresholds[stock], shares_to_trade, risk_reward_ratio))
                if signal == "Buy" and stock not in self.portfolio and stock not in self.manual_purchases:
                    if self.base_cash >= (price * shares_to_trade):
                        logging.debug("Buy condition passed for {}, proceeding to execute".format(stock))
                        self.base_cash -= price * shares_to_trade
                        self.cash_label.config(text="Cash: ${:.2f}".format(self.base_cash))
                        self.portfolio[stock] = self.portfolio.get(stock, 0) + shares_to_trade
                        self.cost_basis[stock] = price
                        self.transaction_history.setdefault(stock, []).append({
                            'action': 'Buy',
                            'shares': shares_to_trade,
                            'price': price,
                            'timestamp': datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S%z"),
                            'mode': self.trading_mode,
                            'buy_signals': buy_signals,
                            'ratio': "{:.1f}:1".format(risk_reward_ratio)
                        })
                        self.last_trade_time["{}_buy".format(stock)] = current_time
                        self.save_transaction_history()
                        save_thresholds = True
                        self.real_trades_logger.info("Trade {}: {} Buy ${:.2f} (shares: {}, signals: {}, ratio: {:.1f}:1, mode: {})".format(
                            self.trade_counter, stock, price, shares_to_trade, buy_signals, risk_reward_ratio, self.trading_mode))
                        csv_file = os.path.join(r"C:\Users\dad\StockApp", "all_auto_trades.csv")
                        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
                        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            if f.tell() == 0:
                                writer.writerow(['Run ID', 'Trade ID', 'Stock', 'Action', 'Buy Price', 'Sell Price', 'Percent Gain', 'Profit', 'Trailing Stop', 'Sell Time', 'Ratio'])
                            writer.writerow([
                                run_id,
                                self.trade_counter,
                                stock,
                                'Buy',
                                "{:.2f}".format(price),
                                '',
                                '',
                                '',
                                'no',
                                '',
                                "{:.1f}:1".format(risk_reward_ratio)
                            ])
                        logging.info("Auto-traded: Bought {} shares of {} at ${:.4f} for ${:.2f} in {} mode, signals={}, ratio={:.1f}:1".format(
                            shares_to_trade, stock, price, price * shares_to_trade, self.trading_mode, buy_signals, risk_reward_ratio))
                        self.status_label.config(text="Auto-traded: Bought {} of {} for ${:.2f} (ratio {:.1f}:1)".format(shares_to_trade, stock, price * shares_to_trade, risk_reward_ratio))
                        if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                            self.speak("Auto-traded: Bought {} shares of {} for {:.2f} dollars, ratio {:.1f} to 1".format(shares_to_trade, stock, price * shares_to_trade, risk_reward_ratio))
                    else:
                        logging.warning("Insufficient funds for {}: cash=${:.2f}, needed=${:.2f}".format(stock, self.base_cash, price * shares_to_trade))
                        self.status_label.config(text="Critical: Insuficient funds for {}".format(stock))
                        self.speak("Critical: Insufficient funds for {}".format(stock))
                elif stock in self.portfolio:
                    target = self.supply_thresholds[stock]
                    stop_loss = self.demand_thresholds[stock]
                    logging.debug("Sell check for {}: price=${:.4f}, target=${:.4f}, stop_loss=${:.4f}".format(stock, price, target, stop_loss))
                    if price <= stop_loss:
                        shares_owned = self.portfolio[stock]
                        self.base_cash += price * shares_owned
                        self.cash_label.config(text="Cash: ${:.2f}".format(self.base_cash))
                        cost_basis = self.cost_basis.get(stock, price)
                        percent_gain = ((price - cost_basis) / cost_basis * 100) if cost_basis else 0
                        profit = (price - cost_basis) * shares_owned if cost_basis else 0
                        del self.portfolio[stock]
                        if stock in self.cost_basis:
                            del self.cost_basis[stock]
                        if stock in self.highest_price:
                            del self.highest_price[stock]
                        self.transaction_history.setdefault(stock, []).append({
                            'action': 'Sell',
                            'shares': shares_owned,
                            'price': price,
                            'timestamp': datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S%z"),
                            'mode': self.trading_mode,
                            'buy_signals': buy_signals,
                            'ratio': "{:.1f}:1".format(risk_reward_ratio)
                        })
                        self.last_trade_time["{}_sell".format(stock)] = current_time
                        self.save_transaction_history()
                        save_thresholds = True
                        trailing_str = 'yes' if stock in self.highest_price else 'no'
                        self.real_trades_logger.info("Trade {}: {} Sell ${:.2f} (shares: {}, % gain: {:.2f}%, profit: ${:.2f}, trailing: {}, mode: {}, ratio: {:.1f}:1)".format(
                            self.trade_counter, stock, price, shares_owned, percent_gain, profit, trailing_str, self.trading_mode, risk_reward_ratio))
                        csv_file = os.path.join(r"C:\Users\dad\StockApp", "all_auto_trades.csv")
                        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
                        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                run_id,
                                self.trade_counter,
                                stock,
                                'Sell',
                                "{:.2f}".format(self.cost_basis.get(stock, price)),
                                "{:.2f}".format(price),
                                "{:+.2f}%".format(percent_gain),
                                "${:.2f}".format(profit),
                                trailing_str,
                                datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S"),
                                "{:.1f}:1".format(risk_reward_ratio)
                            ])
                        logging.info("Auto-traded: Sold {} shares of {} at ${:.4f} in {} mode, signals={}, ratio={:.1f}:1".format(
                            shares_owned, stock, price, self.trading_mode, buy_signals, risk_reward_ratio))
                        self.status_label.config(text="Auto-traded: Sold {} of {} (ratio {:.1f}:1)".format(shares_owned, stock, risk_reward_ratio))
                        if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                            self.speak("Auto-traded: Sold {} shares of {}".format(shares_owned, stock))
            self.save_portfolio()
            self.update_portfolio_table()
            self.update_history_table()
            if save_thresholds:
                thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds.json")
                thresholds_data = {
                    "buy_threshold": self.buy_threshold.get(),
                    "zone_period": self.zone_period,
                    "volume_level": self.volume_level.get(),
                    "invalid_stocks": list(getattr(self, 'invalid_stocks', set())),
                    "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items()},
                    "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items()},
                    "threshold_zone_periods": self.threshold_zone_periods,
                    "manual_thresholds": {k: {sk: float(sv) if isinstance(sv, (int, float)) else sv for sk, sv in v.items()} for k, v in self.manual_thresholds.items()},
                    "highest_price": {k: float(v) for k, v in getattr(self, 'highest_price', {}).items()}
                }
                try:
                    os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                    with open(thresholds_file, "w") as f:
                        json.dump(thresholds_data, f, indent=2)
                    logging.info("Saved thresholds to {}".format(thresholds_file))
                except Exception as e:
                    logging.error("Error saving thresholds: {}".format(e))
            after_id = self.root.after(5000, self.run_auto_trade)
            self.after_ids.append(after_id)
        except Exception as e:
            logging.error("Error in auto trading: {}".format(e))
            self.status_label.config(text="Error in auto trading")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error in auto trading")
            after_id = self.root.after(5000, self.run_auto_trade)
            self.after_ids.append(after_id)
				
    def get_live_price(self, stock):
        logging.debug(f"Fetching live price for {stock}")
        try:
            url = f"https://financialmodelingprep.com/api/v3/quote/{stock}?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                price = data[0].get("price")
                if price is not None:
                    logging.info(f"Live price for {stock}: ${price:.4f}")
                    return float(price)
            logging.warning(f"No valid price data for {stock}")
            return None
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error fetching price for {stock}: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout fetching price for {stock}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error fetching price for {stock}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error fetching price for {stock}: {e}")
            return None
            
    # Snippet 209: Added batch_get_live_prices helper for run_auto_trade (insert after get_live_price)
    def batch_get_live_prices(self, stocks):
        logging.debug(f"Batch fetching live prices for {len(stocks)} stocks")
        try:
            # Batch up to 10 stocks per API call to avoid rate limits
            batch_size = 10
            prices = {}
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i + batch_size]
                symbols = ','.join(batch)
                url = f"https://financialmodelingprep.com/api/v3/quote/{symbols}?apikey={self.api_key}"
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if data and isinstance(data, list):
                        for item in data:
                            symbol = item.get("symbol")
                            price = item.get("price")
                            if symbol and price is not None:
                                prices[symbol] = float(price)
                                logging.info(f"Live price for {symbol}: ${price:.4f}")
                            else:
                                logging.warning(f"No valid price data for {symbol} in batch")
                                prices[symbol] = 0.0
                    else:
                        logging.warning(f"No valid data in batch response for {symbols}")
                        for symbol in batch:
                            prices[symbol] = 0.0
                    time.sleep(0.2)  # Avoid rate limit
                except requests.exceptions.ConnectionError as e:
                    logging.error(f"Connection error in batch fetch for {symbols}: {e}")
                    for symbol in batch:
                        prices[symbol] = 0.0
                except requests.exceptions.Timeout as e:
                    logging.error(f"Timeout in batch fetch for {symbols}: {e}")
                    for symbol in batch:
                        prices[symbol] = 0.0
                except requests.exceptions.RequestException as e:
                    logging.error(f"Request error in batch fetch for {symbols}: {e}")
                    for symbol in batch:
                        prices[symbol] = 0.0
                except Exception as e:
                    logging.error(f"Unexpected error in batch fetch for {symbols}: {e}")
                    for symbol in batch:
                        prices[symbol] = 0.0
            return prices
        except Exception as e:
            logging.error(f"Error in batch_get_live_prices: {e}")
            return {stock: 0.0 for stock in stocks}            
		
    def reset_mock(self):
        logging.debug("Resetting mock data")
        try:
            self.mock_base_cash = 1000.0
            self.mock_portfolio = {}
            self.mock_cost_basis = {}
            self.mock_last_trade_time = {}
            self.mock_transaction_history = {}
            mock_held_stocks_file = os.path.join(os.getcwd(), "mock_held_stocks.json")
            mock_transaction_history_file = os.path.join(os.getcwd(), "mock_transaction_history.json")
            if os.path.exists(mock_held_stocks_file):
                os.remove(mock_held_stocks_file)
                logging.info(f"Deleted mock held stocks file: {mock_held_stocks_file}")
            if os.path.exists(mock_transaction_history_file):
                os.remove(mock_transaction_history_file)
                logging.info(f"Deleted mock transaction history file: {mock_transaction_history_file}")
            self.update_portfolio_table()
            self.update_history_table()
            self.status_label.config(text="Hold for results")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Hold for Results")
            beep()
        except Exception as e:
            logging.error(f"Error resetting mock data: {e}")
            self.status_label.config(text="Error resetting mock data")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error resetting mock data")
            beep()		
			
    def add_custom_stock(self):
        logging.debug("Adding custom stock")
        try:
            stock = self.add_stock_entry.get().upper().strip()
            if not stock:
                logging.warning("No stock symbol entered")
                self.speak("Please enter a stock symbol")
                beep()
                return
            if stock in self.stocks:
                logging.info(f"Stock {stock} already added")
                self.speak(f"Stock {stock} already added")
                beep()
                self.add_stock_entry.delete(0, tk.END)
                return
            cache_file = os.path.join(r"C:\Users\dad\StockApp", "stock_cache.json")
            cache_data = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                    logging.debug(f"Loaded cache data from {cache_file}")
                except Exception as e:
                    logging.error(f"Error loading cached data for {stock}: {e}")
            cache_key = f"{stock}_{self.interval_var.get()}"
            df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
            if not isinstance(df, pd.DataFrame) or df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[-1]):
                logging.error(f"Failed to fetch valid data for {stock}")
                self.speak(f"Invalid stock data for {stock}")
                beep()
                return
            price = df["Close"].iloc[-1]
            if price > 20 and stock not in self.day_portfolio and stock not in self.swing_portfolio:
                logging.warning(f"Stock {stock} price ${price:.2f} exceeds $20 limit")
                self.speak(f"Stock {stock} price ${price:.2f} exceeds $20 limit")
                beep()
                return
            self.data_cache[cache_key] = df
            df_reset = df.reset_index()
            df_reset['date'] = df_reset['date'].astype(str)
            cache_data[cache_key] = df_reset.to_dict('records')
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, "w") as f:
                    json.dump(cache_data, f, indent=2)
                logging.info(f"Saved cache data to {cache_file}")
            except Exception as e:
                logging.error(f"Error saving cache data: {e}")
            self.stocks.append(stock)
            self.added_stocks.add(stock)
            try:
                os.makedirs(os.path.dirname(self.added_stocks_file), exist_ok=True)
                with open(self.added_stocks_file, "w") as f:
                    json.dump(list(self.added_stocks), f, indent=2)
                logging.info(f"Saved added stocks to {self.added_stocks_file}: {self.added_stocks}")
            except Exception as e:
                logging.error(f"Error saving added stocks: {e}")
                self.speak(f"Error saving added stock {stock}")
                beep()
                return
            df = self.calculate_indicators(df, stock)
            self.data_cache[cache_key] = df
            self.supply_thresholds[stock] = df["supply_zone"].iloc[-1] if 'supply_zone' in df and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.1
            self.demand_thresholds[stock] = df["demand_zone"].iloc[-1] if 'demand_zone' in df and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.9
            self.create_tab_for_stock(stock, placeholder=False)
            self.update_tab_signal(stock)
            self.notebook.select(self.tabs[stock])
            self.current_stock = stock
            logging.info(f"Added custom stock {stock} at ${price:.2f}")
            self.speak(f"Added stock {stock}")
            beep()
            self.add_stock_entry.delete(0, tk.END)
            self.update_portfolio_table()
        except Exception as e:
            logging.error(f"Error adding custom stock {stock}: {e}")
            self.speak(f"Error adding stock {stock}")
            beep()
			
    def fetch_initial_data(self):
        logging.debug("Fetching initial data")
        try:
            if not self.is_market_open() and not self.data_fetch_manual_override:
                logging.info("Market closed and manual override off, skipping initial data fetch")
                self.status_label.config(text="Market closed, awaiting manual data fetch")
                return
            gui_update_queue = queue.Queue()
            def process_gui_updates():
                try:
                    while not gui_update_queue.empty():
                        func = gui_update_queue.get_nowait()
                        func()
                        gui_update_queue.task_done()
                except queue.Empty:
                    pass
                except Exception as e:
                    logging.error(f"Error processing GUI updates: {e}")
                self.root.after(500, process_gui_updates)
            self.root.after(500, process_gui_updates)
            def fetch_thread():
                try:
                    lock = threading.Lock()
                    batch_size = 2
                    stocks_to_process = [s for s in self.stocks if s not in ["***", "Backtest"]]
                    for i in range(0, len(stocks_to_process), batch_size):
                        batch = stocks_to_process[i:i + batch_size]
                        batch_data = {}
                        for stock in batch:
                            with lock:
                                cache_key = f"{stock}_{self.interval_var.get()}"
                                if (cache_key in self.data_cache and
                                    isinstance(self.data_cache[cache_key], pd.DataFrame) and
                                    not self.data_cache[cache_key].empty and
                                    'Close' in self.data_cache[cache_key].columns and
                                    not self.data_cache[cache_key]['Close'].isna().all()):
                                    last_update = getattr(self.data_cache[cache_key], 'last_update', 0)
                                    if time.time() - last_update < 300:
                                        logging.debug(f"Skipping fetch for {stock}: recent cache")
                                        batch_data[stock] = self.data_cache[cache_key]
                                        continue
                                df = self.fetch_data(stock, self.interval_var.get(), force_fetch=False)
                                if not df.empty and 'Close' in df.columns and not df['Close'].isna().all():
                                    df.last_update = time.time()
                                    with self.cache_lock:
                                        self.data_cache[cache_key] = df
                                    batch_data[stock] = df
                                else:
                                    logging.warning(f"No valid data for {stock}")
                                    gui_update_queue.put(lambda: self.status_label.config(text=f"No data for {stock}"))
                                    gui_update_queue.put(lambda: self.speak(f"No data for {stock}"))
                                    gui_update_queue.put(beep)
                                time.sleep(0.8)
                        for stock, df in batch_data.items():
                            gui_update_queue.put(lambda s=stock: self.create_tab_for_stock(s, placeholder=False))
                            gui_update_queue.put(lambda s=stock: self.update_tab_signal(s))
                        time.sleep(1.5)
                    gui_update_queue.put(self.update_tab_labels)
                    gui_update_queue.put(lambda: self.status_label.config(text="Initial data loaded"))
                    logging.info("Initial data fetch completed")
                except Exception as e:
                    logging.error(f"Error in initial data fetch thread: {e}")
                    gui_update_queue.put(lambda: self.status_label.config(text="Error fetching initial data"))
                    gui_update_queue.put(lambda: self.speak("Error fetching initial data"))
                    gui_update_queue.put(beep)
            thread = threading.Thread(target=fetch_thread, daemon=True)
            self.threads.append(thread)
            thread.start()
        except Exception as e:
            logging.error(f"Error initiating initial data fetch: {e}")
            self.status_label.config(text="Error fetching initial data")
            self.speak("Error fetching initial data")
            beep()
            
    def fetch_screener_stocks(self):
        logging.debug("Fetching screener stocks from screener app")
        try:
            cache_file = os.path.join(r"C:\Users\dad\StockApp", "screener_cache.json")
            if not os.path.exists(cache_file):
                logging.warning(f"No screener_cache.json found at {cache_file}")
                return []
            with open(cache_file, "r") as f:
                cached_stocks = json.load(f)
            symbols = [stock["symbol"].upper() for stock in cached_stocks if isinstance(stock, dict) and "symbol" in stock]
            logging.info(f"Fetched {len(symbols)} screener stocks from cache: {symbols[:10]}")
            return symbols
        except Exception as e:
            logging.error(f"Error loading screener cache: {e}")
            return []
            
    # Snippet 204: Added get_stock_volume helper for volume-based stock sorting (insert after fetch_screener_stocks)
    def get_stock_volume(self, stock):
        try:
            cache_key = f"{stock}_{self.interval_var.get()}"
            df = self.data_cache.get(cache_key, pd.DataFrame())
            if df.empty or 'Volume' not in df.columns:
                df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                if df.empty or 'Volume' not in df.columns:
                    return 0
            return df["Volume"].rolling(window=14, min_periods=1).mean().iloc[-1]
        except Exception as e:
            logging.error(f"Error fetching volume for {stock}: {e}")
            return 0            
            
            # Snippet 6a: Replace toggle_all_indicators for global indicator sync
    # Snippet 6a: Replace toggle_all_indicators for global indicator sync
    def toggle_all_indicators(self):
        logging.debug("Toggling all indicators")
        try:
            all_on = not all(var.get() for var in self.indicator_visibility.values() if isinstance(var.get(), bool))
            for indicator_key, var in self.indicator_visibility.items():
                if isinstance(var.get(), bool):
                    var.set(all_on)
            for stock in self.stocks:
                if stock in ["***", "Backtest"]:
                    continue
                self.update_tab_signal(stock)
            # Sync group toggles after per-stock updates
            for group_name in self.group_visibility:
                group_indicators = self.get_group_indicators(group_name)
                group_on = all(self.indicator_visibility[ind].get() for ind in group_indicators if ind in self.indicator_visibility)
                self.group_visibility[group_name].set(group_on)
            status = "enabled" if all_on else "disabled"
            logging.info(f"All indicators {status}")
            self.status_label.config(text=f"All indicators {status}")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"All indicators {status}")
            beep()
        except Exception as e:
            logging.error(f"Error toggling all indicators: {e}")
            self.status_label.config(text="Error toggling indicators")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error toggling indicators")
            beep()
            
    def get_group_indicators(self, group_name):
        groups = {
            "Basic": ["mfi", "ema13" if self.interval_var.get() == "3min" else "sma13", "macd", "demand_zone"],
            "Advanced 1": ["stochastic", "cci", "obv", "vwap"],
            "Advanced 2": ["adx", "atr", "momentum"],
            "Advanced 3": ["stochastic_rsi", "williams_%r", "bollinger_bands"]
        }
        return groups.get(group_name, [])            
            
    # Snippet 195: Full _update_data_thread with low-vol skip and alert suppression (replace existing from Snippet 190)
    def _update_data_thread(self, first_fetch, gui_update_queue, force_cache_only=False):
        logging.debug(f"Running data update thread, first_fetch={first_fetch}, force_cache_only={force_cache_only}")
        try:
            lock = threading.Lock()
            stocks_to_process = [s for s in self.stocks if s not in ["***", "Backtest"]]
            for stock in stocks_to_process:
                with lock:
                    cache_key = f"{stock}_{self.interval_var.get()}"
                    if force_cache_only:
                        df = self.data_cache.get(cache_key, pd.DataFrame())
                        if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                            logging.debug(f"Cache empty for {stock} in cache-only mode, skipping")
                            continue
                    else:
                        df = self.fetch_data(stock, self.interval_var.get(), force_fetch=first_fetch)
                        if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                            # Low-vol check before alert
                            avg_vol = df["Volume"].rolling(14).mean().iloc[-1] if not df.empty else 0
                            if avg_vol < 500:
                                logging.debug(f"Skipping low-vol {stock}: {avg_vol:.0f}, no alert")
                                continue
                            logging.warning(f"No valid data for {stock}")
                            gui_update_queue.put(lambda: self.status_label.config(text=f"Critical: No data for {stock}"))
                            gui_update_queue.put(lambda: self.speak(f"Critical: No data for {stock}"))
                            gui_update_queue.put(beep)
                            continue
                    # Low-vol skip post-fetch
                    avg_vol = df["Volume"].rolling(14).mean().iloc[-1] if not df.empty else 0
                    if avg_vol < 500:
                        logging.debug(f"Low-vol skip for {stock}: {avg_vol:.0f}, no alert")
                        continue
                    with self.cache_lock:
                        df = self.calculate_indicators(df, stock)
                        self.data_cache[cache_key] = df
                    live_price = self.get_live_price(stock)
                    if live_price == 0.0 and stock in self.portfolio:
                        logging.warning(f"No live price for portfolio stock {stock}")
                        gui_update_queue.put(lambda: self.status_label.config(text=f"Critical: No live price for {stock}"))
                        gui_update_queue.put(lambda: self.speak(f"Critical: No live price for {stock}"))
                        gui_update_queue.put(beep)
                    gui_update_queue.put(lambda s=stock: self.create_tab_for_stock(s, placeholder=False))
                    gui_update_queue.put(lambda s=stock: self.update_tab_signal(s))
                time.sleep(0.1)
            gui_update_queue.put(self.update_portfolio_table)
            gui_update_queue.put(self.update_tab_labels)  # Update labels after all tabs are created
            gui_update_queue.put(lambda: self.status_label.config(text="Data updated"))
            gui_update_queue.put(lambda: self.progress_bar.stop())
            gui_update_queue.put(beep)
            logging.info("Data update thread completed")
        except Exception as e:
            logging.error(f"Error in data update thread: {e}")
            gui_update_queue.put(lambda: self.status_label.config(text="Error updating data"))
            gui_update_queue.put(lambda: self.speak("Error updating data"))
            gui_update_queue.put(beep)
            
    # Snippet 6f: Replace on_closing toggles save for global indicators only
    def on_closing(self):
        logging.debug("Closing application")
        try:
            self.save_portfolio()
            logging.debug("Saving portfolio")
            portfolio_data = {
                "day_portfolio": self.day_portfolio,
                "swing_portfolio": self.swing_portfolio,
                "day_cost_basis": self.day_cost_basis,
                "swing_cost_basis": self.swing_cost_basis
            }
            try:
                with open(self.held_stocks_file, "w") as f:
                    json.dump(portfolio_data, f, indent=2)
                logging.info(f"Saved portfolio to {self.held_stocks_file}")
            except Exception as e:
                logging.error(f"Error saving portfolio: {e}")
            logging.debug("Saving transaction history")
            transaction_history_file = os.path.join(r"C:\Users\dad\StockApp", "transaction_history.json")
            try:
                with open(transaction_history_file, "w") as f:
                    json.dump(self.transaction_history, f, indent=2)
                logging.info(f"Saved transaction history to {transaction_history_file} for {len(self.transaction_history)} tickers")
            except Exception as e:
                logging.error(f"Error saving transaction history: {e}")
            logging.debug("Saving added stocks")
            try:
                with open(self.added_stocks_file, "w") as f:
                    json.dump(list(self.added_stocks), f, indent=2)
                logging.info(f"Saved added stocks to {self.added_stocks_file}")
            except Exception as e:
                logging.error(f"Error saving added stocks: {e}")
            logging.debug("Saving thresholds")
            thresholds_file = os.path.join(r"C:\Users\dad\StockApp", "thresholds.json")
            thresholds_data = {
                "buy_threshold": self.buy_threshold.get(),
                "zone_period": self.zone_period,
                "volume_level": self.volume_level.get(),
                "invalid_stocks": list(self.invalid_stocks),
                "supply_thresholds": {k: float(v) for k, v in self.supply_thresholds.items()},
                "demand_thresholds": {k: float(v) for k, v in self.demand_thresholds.items()},
                "threshold_zone_periods": self.threshold_zone_periods
            }
            try:
                os.makedirs(os.path.dirname(thresholds_file), exist_ok=True)
                with open(thresholds_file, "w") as f:
                    json.dump(thresholds_data, f, indent=2)
                logging.info(f"Saved thresholds to {thresholds_file}")
            except Exception as e:
                logging.error(f"Error saving thresholds: {e}")
            # Save toggles (globals only)
            toggles_file = os.path.join(r"C:\Users\dad\StockApp", "toggles.json")
            toggles_data = {
                "group_visibility": {k: v.get() for k, v in self.group_visibility.items()},
                "indicator_visibility": {k: v.get() for k, v in self.indicator_visibility.items() if k in self.indicators_list}
            }
            try:
                os.makedirs(os.path.dirname(toggles_file), exist_ok=True)
                with open(toggles_file, "w") as f:
                    json.dump(toggles_data, f, indent=2)
                logging.info(f"Saved global toggles to {toggles_file}")
            except Exception as e:
                logging.error(f"Error saving toggles: {e}")
            unique_after_ids = list(set(self.after_ids))  # Remove duplicates
            for after_id in unique_after_ids:
                try:
                    self.root.after_cancel(after_id)
                except Exception:
                    pass
            self.after_ids.clear()
            for thread in self.threads:
                try:
                    thread.join(timeout=1.0)
                except Exception:
                    pass
            logging.info("Application closed successfully")
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error during closing: {e}")
            self.root.destroy()
            
    # Snippet 300: Updated fetch_data with cache subfolder and robust error handling
    def fetch_data(self, stock, interval, force_fetch=False):
        logging.debug("Fetching data for {} ({})".format(stock, interval))
        cache_dir = os.path.join(r"C:\Users\dad\StockApp", "cache")
        cache_key = "{}_{}".format(stock, interval)
        cache_file = os.path.join(cache_dir, "{}_{}.json".format(cache_key, self.zone_period))
        if not force_fetch and os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cached = json.load(f)
                if cached["timestamp"] > (datetime.now().timestamp() - 7200):  # 2hr cache
                    df = pd.DataFrame.from_dict(cached["data"], orient="index")
                    df.index = pd.to_datetime(df.index)
                    df.index.name = "date"
                    if not df.empty and all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']) and not df['Close'].isna().all():
                        logging.debug("Loaded valid cached data for {}: {} rows".format(stock, len(df)))
                        return df
                    else:
                        logging.warning("Invalid cached data for {}, fetching fresh data".format(stock))
            except Exception as e:
                logging.warning("Error loading cache for {}: {}".format(stock, e))
        retries = 3
        for attempt in range(retries):
            try:
                # Fetch 1min data for 3min interval
                fetch_interval = "1min" if interval == "3min" else interval
                url = "https://financialmodelingprep.com/api/v3/historical-chart/{}/{}?apikey={}".format(fetch_interval, stock, self.api_key)
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if not data or not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                    logging.warning("No valid data returned for {} ({}) on attempt {}, response: {}".format(stock, fetch_interval, attempt+1, response.text[:100]))
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Backoff: 1s, 2s, 4s
                        continue
                    # Fallback to daily if intraday fails
                    logging.debug("Falling back to daily for {}".format(stock))
                    daily_url = "https://financialmodelingprep.com/api/v3/historical-price-full/{}?apikey={}".format(stock, self.api_key)
                    daily_resp = requests.get(daily_url, timeout=10)
                    daily_resp.raise_for_status()
                    daily_data = daily_resp.json()
                    if 'historical' in daily_data and daily_data['historical']:
                        df_daily = pd.DataFrame(daily_data['historical'])
                        df_daily['date'] = pd.to_datetime(df_daily['date'])
                        df_daily.set_index('date', inplace=True)
                        df_daily = df_daily[['open', 'high', 'low', 'close', 'volume']].rename(columns={
                            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
                        })
                        if interval == "3min":
                            df_daily = df_daily.resample('3H').agg({
                                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                            }).dropna()
                        logging.debug("Used daily fallback for {}: {} rows".format(stock, len(df_daily)))
                        if len(df_daily) < 100:
                            logging.warning(f"Insufficient data for {stock}: {len(df_daily)} bars, expected 100")
                            return pd.DataFrame()
                        return df_daily
                    else:
                        logging.warning("Daily fallback failed for {}, response: {}".format(stock, str(daily_data)[:100]))
                        return pd.DataFrame()
                df = pd.DataFrame(data)
                if 'date' not in df.columns or df.empty:
                    logging.warning("Invalid data structure for {} ({}) on attempt {}, response: {}".format(stock, fetch_interval, attempt+1, response.text[:100]))
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return pd.DataFrame()
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']].rename(columns={
                    'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
                })
                if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                    logging.warning("No usable data for {} after processing on attempt {}".format(stock, attempt+1))
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    # Last price fallback
                    last_price = self.get_live_price(stock)
                    if last_price and last_price > 0:
                        df = pd.DataFrame({
                            'Open': [last_price], 'High': [last_price], 'Low': [last_price],
                            'Close': [last_price], 'Volume': [0]
                        }, index=[pd.Timestamp.now()])
                        df.index.name = "date"
                        logging.debug("Used last price fallback for {}: ${:.2f}".format(stock, last_price))
                    else:
                        logging.warning("No last price for {}, skipping".format(stock))
                        return pd.DataFrame()
                # Resample to 3min if needed
                if interval == "3min":
                    df = df.resample('3min').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                if len(df) < 100:
                    logging.warning(f"Insufficient data for {stock}: {len(df)} bars, expected 100")
                    return pd.DataFrame()
                df_to_save = df.copy()
                df_to_save.index = df_to_save.index.astype(str)
                try:
                    os.makedirs(cache_dir, exist_ok=True)
                    with open(cache_file, "w") as f:
                        json.dump({"timestamp": datetime.now().timestamp(), "data": df_to_save.to_dict(orient="index")}, f, indent=2)
                    logging.debug("Saved cache for {}".format(stock))
                except Exception as e:
                    logging.error("Error saving cache for {}: {}".format(stock, e))
                return df
            except requests.exceptions.ConnectionError as e:
                logging.error("Connection error fetching data for {} on attempt {}: {}".format(stock, attempt+1, e))
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return pd.DataFrame()
            except requests.exceptions.Timeout as e:
                logging.error("Timeout fetching data for {} on attempt {}: {}".format(stock, attempt+1, e))
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return pd.DataFrame()
            except requests.exceptions.RequestException as e:
                logging.error("Request error fetching data for {} on attempt {}: {}".format(stock, attempt+1, e))
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return pd.DataFrame()
            except Exception as e:
                logging.error("Unexpected error fetching data for {} on attempt {}: {}".format(stock, attempt+1, e))
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return pd.DataFrame()
        return pd.DataFrame()  # Final fallback
  
    # Snippet 301: Updated async_fetch_data with cache subfolder and fresh data fetch
    def async_fetch_data(self):
        logging.debug("Starting async data fetch")
        try:
            while True:
                if not self.is_market_open() and not self.data_fetch_manual_override:
                    logging.debug("Market closed and manual override off, skipping data fetch")
                    time.sleep(60)
                    continue
                lock = threading.Lock()
                batch_size = 2
                stocks_to_process = [s for s in self.stocks if s not in ["***", "Backtest"]]
                for i in range(0, len(stocks_to_process), batch_size):
                    batch = stocks_to_process[i:i + batch_size]
                    batch_data = {}
                    for stock in batch:
                        with lock:
                            cache_key = "{}_{}".format(stock, self.interval_var.get())
                            if (cache_key in self.data_cache and
                                isinstance(self.data_cache[cache_key], pd.DataFrame) and
                                not self.data_cache[cache_key].empty and
                                'Close' in self.data_cache[cache_key].columns and
                                not self.data_cache[cache_key]['Close'].isna().all()):
                                last_update = getattr(self.data_cache[cache_key], 'last_update', 0)
                                if time.time() - last_update < 300:
                                    logging.debug("Skipping fetch for {}: recent cache".format(stock))
                                    batch_data[stock] = self.data_cache[cache_key]
                                    continue
                            df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                            if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                                logging.warning("No valid data for {} in async fetch".format(stock))
                                self.root.after(0, lambda s=stock: self.status_label.config(text="No data for {}".format(s)))
                                self.root.after(0, lambda s=stock: self.speak("No data for {}".format(s)))
                                self.root.after(0, beep)
                                continue
                            df.last_update = time.time()
                            with self.cache_lock:
                                self.data_cache[cache_key] = df
                            batch_data[stock] = df
                        time.sleep(0.8)
                    for stock, df in batch_data.items():
                        self.root.after(0, lambda s=stock: self.create_tab_for_stock(s, placeholder=False))
                        self.root.after(0, lambda s=stock: self.update_tab_signal(s))
                    time.sleep(1.5)
                self.root.after(0, self.update_tab_labels)
                self.root.after(0, lambda: self.status_label.config(text="Data updated"))
                time.sleep(60)
        except Exception as e:
            logging.error("Error in async data fetch: {}".format(e))
            self.root.after(0, lambda: self.status_label.config(text="Error fetching data"))
            self.root.after(0, lambda: self.speak("Error fetching data"))
            self.root.after(0, beep)
            time.sleep(60)
            self.async_fetch_data()
            
# Snippet 1: Replace the existing load_transaction_history method (in last part) to handle EDT timezone parsing
    def load_transaction_history(self):
        logging.debug("Loading transaction history")
        try:
            history_file = os.path.join(r"C:\Users\dad\StockApp", "transaction_history.json")
            logging.debug(f"Attempting to read transaction history: {history_file}")
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r") as f:
                        raw_data = f.read()
                        logging.debug(f"Raw contents of {history_file}: {raw_data}")
                        self.transaction_history = json.loads(raw_data)
                    if not isinstance(self.transaction_history, dict):
                        logging.warning(f"Invalid JSON format in {history_file}, initializing empty")
                        self.transaction_history = {}
                    else:
                        for stock, transactions in self.transaction_history.items():
                            for tx in transactions:
                                if 'timestamp' in tx and isinstance(tx['timestamp'], str):
                                    try:
                                        timestamp_str = tx['timestamp']
                                        # Handle EDT/EST by removing abbreviation and localizing
                                        if 'EDT' in timestamp_str or 'EST' in timestamp_str:
                                            # Remove timezone abbreviation and parse naive, then localize
                                            naive_str = timestamp_str.replace(' EDT', '').replace(' EST', '')
                                            timestamp = pd.to_datetime(naive_str, format="%Y-%m-%d %H:%M:%S", errors='coerce')
                                            if not pd.isna(timestamp):
                                                # Localize to America/New_York (handles EDT/EST)
                                                timestamp = timestamp.tz_localize("America/New_York")
                                        else:
                                            # Try parsing with offset (e.g., 2025-09-23 15:56:42-04:00)
                                            timestamp = pd.to_datetime(timestamp_str, format="%Y-%m-%d %H:%M:%S%z", errors='coerce')
                                            if pd.isna(timestamp):
                                                # Fallback to naive parsing without timezone
                                                naive_str = ' '.join(timestamp_str.split()[:2])
                                                timestamp = pd.to_datetime(naive_str, format="%Y-%m-%d %H:%M:%S", errors='coerce')
                                                if not pd.isna(timestamp):
                                                    timestamp = timestamp.tz_localize("America/New_York")
                                        if pd.isna(timestamp):
                                            logging.warning(f"Invalid timestamp for {stock}: {timestamp_str}, using current time")
                                            tx['timestamp'] = datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S%z")
                                        else:
                                            tx['timestamp'] = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")
                                    except Exception as e:
                                        logging.warning(f"Error parsing timestamp for {stock}: {e}, using current time")
                                        tx['timestamp'] = datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S%z")
                                else:
                                    logging.warning(f"Missing or invalid timestamp for {stock}, using current time")
                                    tx['timestamp'] = datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S%z")
                        logging.info(f"Loaded transaction history from {history_file}: {len(self.transaction_history)} tickers")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse {history_file}: {e}")
                    self.transaction_history = {}
            else:
                logging.info(f"No {history_file} found, initializing empty")
                self.transaction_history = {}
            return self.transaction_history
        except Exception as e:
            logging.error(f"Error loading transaction history: {e}")
            self.status_label.config(text="Error loading transaction history")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error loading transaction history")
            self.transaction_history = {}
            return self.transaction_history
			
# Snippet 59: load_portfolio
    def load_portfolio(self):
        logging.debug("Loading portfolio")
        try:
            portfolio_file = os.path.join(r"C:\Users\dad\StockApp", "held_stocks.json")
            if os.path.exists(portfolio_file):
                with open(portfolio_file, "r") as f:
                    portfolio_data = json.load(f)
                self.day_portfolio = portfolio_data.get("day_portfolio", {})
                self.swing_portfolio = portfolio_data.get("swing_portfolio", {})
                self.day_cost_basis = portfolio_data.get("day_cost_basis", {})
                self.swing_cost_basis = portfolio_data.get("swing_cost_basis", {})
                self.portfolio = self.day_portfolio if self.trading_mode == "day" else self.swing_portfolio
                self.cost_basis = self.day_cost_basis if self.trading_mode == "day" else self.swing_cost_basis
                logging.info(f"Loaded portfolio from {portfolio_file}")
            else:
                logging.info(f"No portfolio file found at {portfolio_file}")
        except Exception as e:
            logging.error(f"Error loading portfolio: {e}")
            self.day_portfolio = {}
            self.swing_portfolio = {}
            self.day_cost_basis = {}
            self.swing_cost_basis = {}
            self.portfolio = self.day_portfolio
            self.cost_basis = self.day_cost_basis	
            
# Snippet 57: Fix fetch_stocks_thread
    def fetch_stocks_thread(self):
        logging.debug("Fetching screener stocks in thread")
        try:
            stocks = self.fetch_screener_stocks()
            self.stocks = sorted(set(self.day_portfolio.keys()) | set(self.swing_portfolio.keys()) | set(self.added_stocks) | set(stocks))
            logging.debug(f"Stocks after fetch: {self.stocks}")
            self.fetch_queue.put((self.create_tabs, None))
            self.fetch_queue.put((self.update_portfolio_table, None))
            for stock in self.stocks:
                if stock not in ["***", "Backtest"]:
                    self.fetch_queue.put((self.update_tab_signal, (stock,)))
        except Exception as e:
            logging.error(f"Error fetching screener stocks: {e}")
            self.fetch_queue.put((lambda: self.status_label.config(text="Error fetching screener stocks"), None))          
			
            # Snippet 6b: Replace toggle_group_global for global group sync
    # Snippet 6b: Replace toggle_group_global for global group sync
    def toggle_group_global(self, group):
        logging.debug("Toggling global group {}".format(group))
        try:
            is_on = self.group_visibility[group].get()
            groups = {
                "Basic": ["mfi", "ema13" if self.interval_var.get() == "3min" else "sma13", "macd", "demand_zone"],
                "Advanced 1": ["stochastic", "cci", "obv", "vwap"],
                "Advanced 2": ["adx", "atr", "momentum"],
                "Advanced 3": ["stochastic_rsi", "williams_%r", "bollinger_bands"]
            }
            if group not in groups:
                logging.warning("Invalid group {}".format(group))
                return
            for indicator in groups[group]:
                if indicator in self.indicator_visibility:
                    self.indicator_visibility[indicator].set(is_on)
                    logging.debug("Set global {} to {}".format(indicator, is_on))
            for stock in self.stocks:
                if stock in ["***", "Backtest"]:
                    continue
                if stock not in self.tabs:
                    self.create_tab_for_stock(stock, placeholder=False)
                for indicator in groups[group]:
                    indicator_key = "{}_{}".format(stock, indicator)
                    if indicator_key not in self.indicator_visibility:
                        self.indicator_visibility[indicator_key] = tk.BooleanVar(value=is_on)
                    self.indicator_visibility[indicator_key].set(is_on)
                # Clear and refresh table
                if stock in self.indicator_tables:
                    for item in self.indicator_tables[stock].get_children():
                        self.indicator_tables[stock].delete(item)
                    self.update_tab_signal(stock)
            logging.info("Toggled global group {} to {}".format(group, 'on' if is_on else 'off'))
            self.root.after(0, lambda: self.status_label.config(text="Group {} {}".format(group, 'enabled' if is_on else 'disabled')))
            self.root.after(0, beep)
        except Exception as e:
            logging.error("Error toggling global group {}: {}".format(group, e))
            self.root.after(0, lambda: self.status_label.config(text="Error toggling {}".format(group)))
            self.root.after(0, beep)
			
    # Snippet 6c: Replace toggle_indicator_global for global indicator sync
    def toggle_indicator_global(self, indicator):
        logging.debug("Toggling global indicator {}".format(indicator))
        try:
            if indicator not in self.indicator_visibility:
                logging.warning("Global indicator {} not found".format(indicator))
                return
            is_on = self.indicator_visibility[indicator].get()
            for stock in self.stocks:
                if stock in ["***", "Backtest"]:
                    continue
                indicator_key = "{}_{}".format(stock, indicator)
                if indicator_key not in self.indicator_visibility:
                    self.indicator_visibility[indicator_key] = tk.BooleanVar(value=is_on)
                self.indicator_visibility[indicator_key].set(is_on)
                if stock in self.indicator_tables:
                    for item in self.indicator_tables[stock].get_children():
                        self.indicator_tables[stock].delete(item)
                    self.update_tab_signal(stock)
            logging.info("Toggled global {} to {}".format(indicator, 'on' if is_on else 'off'))
            self.root.after(0, lambda: self.status_label.config(text="Indicator {} {}".format(indicator, 'enabled' if is_on else 'disabled')))
            self.root.after(0, beep)
        except Exception as e:
            logging.error("Error toggling global indicator {}: {}".format(indicator, e))
            self.root.after(0, lambda: self.status_label.config(text="Error toggling {}".format(indicator)))
            self.root.after(0, beep)
			
    def update_indicator(self, stock, indicator):
        logging.debug(f"Updating indicator {indicator} for {stock}")
        try:
            cache_key = f"{stock}_{self.interval_var.get()}"
            df = self.data_cache.get(cache_key, pd.DataFrame())
            if not df.empty and 'Close' in df.columns and not df['Close'].isna().all():
                df = self.calculate_indicators(df, stock)
                self.data_cache[cache_key] = df
            self.update_tab_signal(stock)
            self.root.after_idle(lambda: self.root.update_idletasks())
            logging.info(f"Updated {indicator} for {stock}, state: {self.indicator_visibility[indicator].get()}")
            self.status_label.config(text=f"Updated indicator {indicator} for {stock}")
            beep()
        except Exception as e:
            logging.error(f"Error updating indicator {indicator} for {stock}: {e}")
            self.status_label.config(text=f"Error updating {indicator}")
            beep()		

    def confirm_backtest(self):
        logging.debug("Prompting for backtest confirmation")
        try:
            if messagebox.askyesno("Confirm Backtest", "Run backtest on all stocks? This may take some time."):
                self.run_backtest()
                logging.info("Backtest initiated")
            else:
                logging.info("Backtest cancelled by user")
                self.status_label.config(text="Backtest cancelled")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Backtest cancelled")
                beep()
        except Exception as e:
            logging.error(f"Error in confirm_backtest: {e}")
            self.status_label.config(text="Error initiating backtest")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error initiating backtest")
            beep()
            
    def manual_refresh_data(self):
        logging.debug("Manual data refresh initiated")
        try:
            self.data_fetch_manual_override = not self.data_fetch_manual_override
            self.refresh_data_button.config(text="Data On (Manual)" if self.data_fetch_manual_override else "Data Off")
            if self.data_fetch_manual_override:
                logging.info("Manual data fetch enabled")
                self.status_label.config(text="Manual data fetch enabled")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Manual data fetch enabled")
                self.update_data(first_fetch=True)
            else:
                logging.info("Manual data fetch disabled")
                self.status_label.config(text="Manual data fetch disabled")
                if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                    self.speak("Manual data fetch disabled")
            beep()
        except Exception as e:
            logging.error(f"Error in manual data refresh: {e}")
            self.status_label.config(text="Error in manual data refresh")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error in manual data refresh")
            beep()            
			
    def run_backtest(self):
        logging.debug("Running backtest")
        try:
            if not self.is_market_open():
                logging.debug("Backtest skipped: market closed")
                self.root.after(5000, self.run_backtest)
                return
            current_time = datetime.now(pytz.timezone("America/New_York")).timestamp()
            today = datetime.now(pytz.timezone("America/New_York")).date()
            csv_file = os.path.join(r"C:\Users\dad\StockApp\logs", f"all_backtest_trades_{today.strftime('%Y-%m-%d')}.csv")
            run_id = datetime.now(pytz.timezone("America/New_York")).strftime('%Y%m%d_%H%M%S')
            for stock in self.stocks:
                if stock in ["***", "Backtest"]:
                    continue
                cache_key = f"{stock}_{self.interval_var.get()}"
                df = self.data_cache.get(cache_key, pd.DataFrame())
                if df.empty or 'Close' not in df.columns or df['Close'].isna().all() or len(df) < 100:
                    df = self.fetch_data(stock, self.interval_var.get(), force_fetch=True)
                    self.data_cache[cache_key] = df
                    if df.empty or 'Close' not in df.columns or df['Close'].isna().all() or len(df) < 100:
                        logging.warning(f"No valid data for {stock} in backtest, skipping")
                        continue
                df = self.calculate_indicators(df, stock)
                price = df['Close'].iloc[-1]
                avg_volume = df["Volume"].rolling(window=14, min_periods=1).mean().iloc[-1]
                min_volume = 500 if price < 5 else 1000
                if avg_volume < min_volume:
                    logging.debug(f"Skipping {stock}: average volume {avg_volume} below {min_volume}")
                    continue
                buy_signals = sum(1 for ind in ["mfi", "macd", "stochastic", "ema13", "cci", "obv", "vwap", "demand_zone"] if
                                  self.indicator_visibility.get(f"{stock}_{ind}", tk.BooleanVar(value=True)).get() and ind in df.columns and
                                  not pd.isna(df[ind].iloc[-1]) and (
                                      (ind == "mfi" and df[ind].iloc[-1] < 20) or
                                      (ind == "macd" and df[ind].iloc[-1] > 1e-6) or
                                      (ind == "stochastic" and df[ind].iloc[-1] < 20) or
                                      (ind == "ema13" and df["Close"].iloc[-1] > df[ind].iloc[-1]) or
                                      (ind == "cci" and df[ind].iloc[-1] < -50) or
                                      (ind == "obv" and df[ind].diff().iloc[-1] > 0) or
                                      (ind == "vwap" and df["Close"].iloc[-1] < df[ind].iloc[-1]) or
                                      (ind == "demand_zone" and df["Close"].iloc[-1] < df[ind].iloc[-1])))
                active_indicators = sum(1 for ind in ["mfi", "macd", "stochastic", "ema13", "cci", "obv", "vwap", "demand_zone"] if
                                        self.indicator_visibility.get(f"{stock}_{ind}", tk.BooleanVar(value=True)).get() and ind in df.columns and
                                        not pd.isna(df[ind].iloc[-1]))
                supply = df["supply_zone"].iloc[-1] if "supply_zone" in df.columns and not pd.isna(df["supply_zone"].iloc[-1]) else price * 1.20
                demand = df["demand_zone"].iloc[-1] if "demand_zone" in df.columns and not pd.isna(df["demand_zone"].iloc[-1]) else price * 0.80
                risk_reward_ratio = (supply - price) / (price - demand) if (price - demand) > 0 else 0
                if risk_reward_ratio < 1:
                    logging.debug(f"Skipping {stock}: risk-reward ratio {risk_reward_ratio:.1f}:1 below 1:1")
                    continue
                risk_amount = self.base_cash * 0.01
                shares_to_trade = min(max(int(risk_amount / price), 1), 1000)
                if buy_signals >= self.buy_threshold.get():
                    logging.debug(f"Backtest buy condition passed for {stock}")
                    self.backtest_logger.info(f"Backtest Trade {self.trade_counter}: {stock} Buy ${price:.2f} (shares: {shares_to_trade}, signals: {buy_signals}, ratio: {risk_reward_ratio:.1f}:1)")
                    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        if f.tell() == 0:
                            writer.writerow(['Run ID', 'Trade ID', 'Stock', 'Action', 'Buy Price', 'Sell Price', 'Percent Gain', 'Profit', 'Trailing Stop', 'Sell Time', 'Ratio'])
                        writer.writerow([
                            run_id,
                            self.trade_counter,
                            stock,
                            'Buy',
                            f"${price:.2f}",
                            '',
                            '',
                            '',
                            'no',
                            '',
                            f"{risk_reward_ratio:.1f}:1"
                        ])
                    # Simulate sell at target or stop
                    target = supply
                    stop_loss = demand
                    simulated_price = df['Close'].iloc[-1]
                    if simulated_price >= target:
                        percent_gain = ((target - price) / price * 100)
                        profit = (target - price) * shares_to_trade
                        self.backtest_logger.info(f"Backtest Trade {self.trade_counter}: {stock} Sell ${target:.2f} (shares: {shares_to_trade}, % gain: {percent_gain:.2f}%, profit: ${profit:.2f}, trailing: no)")
                        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                run_id,
                                self.trade_counter,
                                stock,
                                'Sell',
                                f"${price:.2f}",
                                f"${target:.2f}",
                                f"{percent_gain:.2f}%",
                                f"${profit:.2f}",
                                'no',
                                datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S"),
                                f"{risk_reward_ratio:.1f}:1"
                            ])
                    elif simulated_price <= stop_loss:
                        percent_gain = ((stop_loss - price) / price * 100)
                        profit = (stop_loss - price) * shares_to_trade
                        self.backtest_logger.info(f"Backtest Trade {self.trade_counter}: {stock} Sell ${stop_loss:.2f} (shares: {shares_to_trade}, % gain: {percent_gain:.2f}%, profit: ${profit:.2f}, trailing: no)")
                        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                run_id,
                                self.trade_counter,
                                stock,
                                'Sell',
                                f"${price:.2f}",
                                f"${stop_loss:.2f}",
                                f"{percent_gain:.2f}%",
                                f"${profit:.2f}",
                                'no',
                                datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S"),
                                f"{risk_reward_ratio:.1f}:1"
                            ])
                    self.trade_counter += 1
            self.root.after(5000, self.run_backtest)
        except Exception as e:
            logging.error(f"Error in backtest: {e}")
            self.root.after(5000, self.run_backtest)
			
    def run_backtest_filter(self):
        logging.debug(f"Applying backtest filter: {self.backtest_filter_var.get()}")
        try:
            # Always recreate the Backtest tab to avoid widget reference errors
            if "Backtest" in self.tabs:
                self.notebook.forget(self.tabs["Backtest"])
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text="Backtest")
            self.tabs["Backtest"] = tab
            columns = ("Trade", "Percent", "Filler")
            tree_widget = ttk.Treeview(tab, columns=columns, show="headings", height=12, style="Custom.Treeview")
            tree_widget.heading("Trade", text="Trade", anchor="center")
            tree_widget.heading("Percent", text="Percent", anchor="center")
            tree_widget.column("Trade", width=600, anchor="center")
            tree_widget.column("Percent", width=100, anchor="center")
            tree_widget.column("Filler", width=0, stretch=False)
            tree_widget.tag_configure("profit", background="lightgreen", foreground="black")
            tree_widget.tag_configure("loss", background="lightcoral", foreground="black")
            tree_widget.pack(fill="both", expand=True, padx=5, pady=5)
            self.backtest_summary_label = ttk.Label(tab, text="Total Trades: 0, Win Rate: 0.00%", style="Status.TLabel")
            self.backtest_summary_label.pack(anchor="w", pady=5)
            self.indicator_tables["Backtest"] = tree_widget
            filter_type = self.backtest_filter_var.get()
            filtered_trades = []
            if filter_type == "All Trades":
                filtered_trades = self.backtest_trade_pairs
            elif filter_type == "Non-Zero Trades":
                filtered_trades = [t for t in self.backtest_trade_pairs if t["profit"] != 0]
            elif filter_type == "Winning Trades":
                filtered_trades = [t for t in self.backtest_trade_pairs if t["profit"] > 0]
            elif filter_type == "Losing Trades":
                filtered_trades = [t for t in self.backtest_trade_pairs if t["profit"] < 0]
            total_trades = len(filtered_trades)
            winning_trades = len([t for t in filtered_trades if t["profit"] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            logging.debug(f"Populating Backtest tab: {total_trades} trades, {winning_trades} wins")
            for trade in filtered_trades:
                percent_str = f"+{trade['percent']:.2f}%" if trade['percent'] >= 0 else f"{trade['percent']:.2f}%"
                tag = "profit" if trade["profit"] > 0 else "loss" if trade["profit"] < 0 else ""
                self.indicator_tables["Backtest"].insert("", "end", values=(
                    f"{trade['stock']} {trade['buy_price']:.2f} -> {trade['sell_price']:.2f} @ {trade['sell_time'].strftime('%Y-%m-%d %H:%M:%S')}",
                    percent_str, ""
                ), tags=(tag,))
            self.backtest_summary_label.config(text=f"Total Trades: {total_trades}, Win Rate: {win_rate:.2f}%")
            self.root.update_idletasks()
            self.notebook.select(self.tabs["Backtest"])
            logging.info(f"Backtest filter applied: {filter_type}, {total_trades} trades, {win_rate:.2f}% win rate")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak(f"Backtest filter applied: {total_trades} trades, {win_rate:.2f}% win rate")
            beep()
        except Exception as e:
            logging.error(f"Error applying backtest filter: {e}")
            self.status_label.config(text="Error applying backtest filter")
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error applying backtest filter")
            beep()
            
    # Snippet 267: Full export_backtest_to_csv with daily Excel sheets and ratio reporting (replace existing in part 9, after replay_transactions)
    def export_backtest_to_csv(self, trade_pairs):
        import pandas as pd
        excel_file = os.path.join(r"C:\Users\dad\StockApp\logs", "backtest_results.xlsx")
        os.makedirs(os.path.dirname(excel_file), exist_ok=True)
        run_id = datetime.now(pytz.timezone("America/New_York")).strftime('%Y%m%d_%H%M%S')
        current_date = datetime.now(pytz.timezone("America/New_York")).strftime('%Y-%m-%d')
        total_trades = len(trade_pairs)
        winning_trades = len([trade for trade in trade_pairs if trade["profit"] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_profit = sum(trade['profit'] for trade in trade_pairs)
        # Prepare data for Excel
        data = []
        data.append({
            'Run ID': run_id,
            'Trade ID': 'SUMMARY',
            'Stock': f"Trades: {total_trades}",
            'Buy Price': f"Win Rate: {win_rate:.2f}%",
            'Sell Price': f"Profit: ${total_profit:.2f}",
            'Percent Gain': '',
            'Profit': '',
            'Trailing Stop': '',
            'Sell Time': '',
            'Ratio': ''
        })
        for i, trade in enumerate(sorted(trade_pairs, key=lambda x: x['profit'], reverse=True), 1):
            percent_str = f"+{trade['percent']:.2f}%" if trade['percent'] >= 0 else f"{trade['percent']:.2f}%"
            trailing_str = trade.get('trailing_stop', 'no')
            ratio_str = trade.get('ratio', 'N/A')
            data.append({
                'Run ID': run_id,
                'Trade ID': f"{i:>6}",
                'Stock': f"{trade['stock']:<8}",
                'Buy Price': f"${trade['buy_price']:>8.2f}",
                'Sell Price': f"${trade['sell_price']:>8.2f}",
                'Percent Gain': f"{percent_str:>10}",
                'Profit': f"${trade['profit']:>8.2f}",
                'Trailing Stop': f"{trailing_str:<8}",
                'Sell Time': trade['sell_time'],
                'Ratio': f"{ratio_str:<8}"
            })
        df = pd.DataFrame(data)
        # Load existing Excel file or create new
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=current_date, index=False)
        except FileNotFoundError:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=current_date, index=False)
        logging.info(f"Appended backtest to Excel sheet {current_date} in {excel_file}")
        return excel_file
			
    # Snippet 282: replay_transactions with counters for possible trades and executed buys, 1:1 ratio threshold, robust obv handling, exact demand stop, 0.995 supply target, old supply as new stop, trailing stop at 99% of old supply, 15-minute zones, 3-minute signals, and ADX fix
    def replay_transactions(self, stock, df):
        logging.debug("Replaying transactions for {}".format(stock))
        try:
            if df.empty or 'Close' not in df.columns or df['Close'].isna().all():
                logging.warning("No valid data for {} in replay_transactions".format(stock))
                return
            df = self.calculate_indicators(df, stock)
            interval_mapping = {"3min": "ema13", "4hour": "sma13"}
            ma_indicator = interval_mapping.get(self.interval_var.get(), "sma13")
            indicators = [
                ("mfi", lambda x: "Buy" if x < 20 else "Sell" if x > 80 else ""),
                ("macd", lambda x: "Buy" if x > 0 else "Sell" if x < 0 else ""),
                ("stochastic", lambda x: "Buy" if x < 20 else "Sell" if x > 80 else ""),
                (ma_indicator, lambda x: "Buy" if df_slice.iloc[-1]["Close"] > x else "Sell" if df_slice.iloc[-1]["Close"] < x else ""),
                ("cci", lambda x: "Buy" if x < -50 else "Sell" if x > 50 else ""),
                ("obv", lambda x: "Buy" if len(df_slice) > 1 and "obv" in df_slice.columns and not pd.isna(df_slice["obv"].iloc[-1]) and df_slice["obv"].diff().iloc[-1] > 0 else "Sell" if len(df_slice) > 1 and "obv" in df_slice.columns and not pd.isna(df_slice["obv"].iloc[-1]) and df_slice["obv"].diff().iloc[-1] < 0 else ""),
                ("vwap", lambda x: "Buy" if df_slice.iloc[-1]["Close"] < x else "Sell" if df_slice.iloc[-1]["Close"] > x else ""),
                ("adx", lambda x: "Buy" if x > 25 else ""),
                ("atr", lambda x: ""),
                ("momentum", lambda x: "Buy" if x > 0 else "Sell" if x < 0 else ""),
                ("stochastic_rsi", lambda x: "Buy" if x < 20 else "Sell" if x > 80 else ""),
                ("williams_%r", lambda x: "Buy" if x < -80 else "Sell" if x > -20 else ""),
                ("bollinger_bands", lambda x: "Buy" if df_slice.iloc[-1]["Close"] < df_slice.iloc[-1]["bb_lower"] else "Sell" if df_slice.iloc[-1]["Close"] > df_slice.iloc[-1]["bb_upper"] else ""),
                ("demand_zone", lambda x: "Buy" if df_slice.iloc[-1]["Close"] < x else "")
            ]
            buy_price = None
            last_buy_index = None
            buy_cost_basis = []
            buy_shares = []
            trailing_active = False
            total_entries = 0
            below_2_to_1 = 0
            one_to_two_to_1 = 0
            total_possible_trades = 0
            total_buys = 0
            for index, row in df.iterrows():
                total_entries += 1
                df_slice = df.loc[:index]
                zones = self.calculate_zones(df_slice, self.zone_period)
                supply = zones["supply_zone"]
                demand = zones["demand_zone"]
                price = df_slice.iloc[-1]["Close"]
                risk_reward_ratio = (supply - price) / (price - demand) if (price - demand) > 0 else 0
                logging.debug("Trade check for {} at {}: price=${:.4f}, supply=${:.4f}, demand=${:.4f}, ratio={:.1f}:1".format(stock, index, price, supply, demand, risk_reward_ratio))
                if risk_reward_ratio < 1:
                    below_2_to_1 += 1
                elif 1 <= risk_reward_ratio < 2:
                    one_to_two_to_1 += 1
                    below_2_to_1 += 1
                signal_counts = {"buy": 0}
                active_indicators = 0
                signal_log = []
                for indicator, signal_func in indicators:
                    indicator_key = "{}_{}".format(stock, indicator)
                    if indicator_key in self.indicator_visibility and self.indicator_visibility[indicator_key].get():
                        if indicator in df_slice.columns and not pd.isna(df_slice.iloc[-1][indicator]):
                            active_indicators += 1
                            signal = signal_func(df_slice.iloc[-1][indicator])
                            if signal == "Buy":
                                signal_counts["buy"] += 1
                            signal_log.append("{}: {} (value={:.2f})".format(indicator, signal, df_slice.iloc[-1][indicator]))
                            if indicator == ma_indicator:
                                signal_log.append("EMA13 Close={:.2f}, EMA={:.2f}".format(df_slice.iloc[-1]["Close"], df_slice.iloc[-1][indicator]))
                adx_key = "{}_adx".format(stock)
                adx_visible = adx_key in self.indicator_visibility and self.indicator_visibility[adx_key].get()
                adx_valid = adx_visible and 'adx' in df_slice.columns and not pd.isna(df_slice.iloc[-1]["adx"]) and df_slice.iloc[-1]["adx"] > 25
                buy_ratio = signal_counts["buy"] / active_indicators if active_indicators > 0 else 0
                logging.debug("Signal details for {} at {}: buy_signals={}, active_indicators={}, buy_ratio={:.2f} (threshold={:.2f}), adx_valid={}, signals=[{}]".format(
                    stock, index, signal_counts["buy"], active_indicators, buy_ratio, self.buy_threshold.get(), adx_valid, "; ".join(signal_log)))
                if risk_reward_ratio < 1 or risk_reward_ratio <= 0:
                    logging.debug("Skipping {} at {}: risk-reward ratio {:.1f}:1 below 1:1 or invalid (buy_ratio={:.2f}, ADX={})".format(
                        stock, index, risk_reward_ratio, buy_ratio, "valid" if adx_valid else "invalid"))
                    continue
                total_possible_trades += 1  # Count entries with valid ratio (>= 1:1)
                if active_indicators > 0 and (not adx_visible or adx_valid) and buy_ratio >= self.buy_threshold.get():
                    logging.info("Buy signal met for {} at {}: ratio={:.2f} >= {:.2f}, ADX valid={}".format(stock, index, buy_ratio, self.buy_threshold.get(), adx_valid))
                    shares = int(self.shares_entry.get()) if self.shares_entry.get().isdigit() else 1
                    cost = shares * price + 0.01 * shares
                    if cost <= self.mock_base_cash:
                        self.mock_base_cash -= cost
                        self.mock_portfolio[stock] = self.mock_portfolio.get(stock, 0) + shares
                        buy_cost_basis.append(price + 0.01)
                        buy_shares.append(shares)
                        self.mock_transaction_history.setdefault(stock, []).append({
                            "action": "Buy",
                            "shares": shares,
                            "price": price,
                            "time": index.strftime("%Y-%m-%d %H:%M:%S"),
                            "ratio": "{:.1f}:1".format(risk_reward_ratio)
                        })
                        buy_price = price
                        last_buy_index = index
                        trailing_active = False
                        total_buys += 1
                        logging.info("Backtest buy: {} shares of {} at ${:.2f} on {}, cost_basis=${:.2f}, ratio={:.1f}:1".format(
                            shares, stock, price, index, buy_cost_basis[-1], risk_reward_ratio))
                    else:
                        logging.debug("Insufficient mock cash for {}: cost={:.2f}, available={:.2f}".format(stock, cost, self.mock_base_cash))
                if stock in self.mock_portfolio and self.mock_portfolio[stock] > 0 and index != last_buy_index:
                    old_supply = supply
                    target_hit = price >= supply * 0.995
                    if target_hit:
                        if not trailing_active:
                            demand = old_supply
                            trailing_active = True
                            logging.info("Target hit for {} at {}: price=${:.4f} >= supply*0.995=${:.4f}, new_stop=old_supply=${:.4f}, trailing_active=True".format(
                                stock, index, price, supply * 0.995, demand))
                        if price > supply:
                            supply = price
                            demand = old_supply * 0.99
                            logging.info("Trailing update for {} at {}: price=${:.4f} > supply=${:.4f}, new_supply=${:.4f}, new_stop=${:.4f}".format(
                                stock, index, price, old_supply, supply, demand))
                    sell_trigger = price >= supply * 0.995 or price <= demand
                    trigger_reason = []
                    if price >= supply * 0.995:
                        trigger_reason.append("supply target hit")
                    if price <= demand:
                        trigger_reason.append("demand stop hit")
                    if trailing_active:
                        trigger_reason.append("trailing stop active")
                    logging.debug("Sell check for {} at {}: price=${:.2f}, supply=${:.2f}, demand=${:.2f}, buy_price=${:.2f}, sell_trigger={}, triggers={}".format(
                        stock, index, price, supply, demand, buy_price if buy_price else 0.0, sell_trigger, ", ".join(trigger_reason)))
                    if sell_trigger:
                        total_shares = self.mock_portfolio[stock]
                        total_profit = 0
                        shares_to_sell = total_shares
                        for i, (cost_basis, shares) in enumerate(zip(buy_cost_basis, buy_shares)):
                            if shares_to_sell <= 0:
                                break
                            sell_shares = min(shares, shares_to_sell)
                            proceeds = sell_shares * price - 0.01 * sell_shares
                            pl = (price - cost_basis) * sell_shares
                            total_profit += pl
                            self.mock_base_cash += proceeds
                            self.mock_transaction_history.setdefault(stock, []).append({
                                "action": "Sell",
                                "shares": sell_shares,
                                "price": price,
                                "time": index.strftime("%Y-%m-%d %H:%M:%S"),
                                "ratio": "{:.1f}:1".format(risk_reward_ratio)
                            })
                            self.backtest_trade_pairs.append({
                                "stock": stock,
                                "buy_price": cost_basis - 0.01,
                                "sell_price": price,
                                "percent": ((price - (cost_basis - 0.01)) / (cost_basis - 0.01) * 100) if (cost_basis - 0.01) else 0,
                                "profit": pl,
                                "sell_time": index,
                                "trailing_stop": "yes" if trailing_active and ("demand stop hit" in trigger_reason or "trailing stop active" in trigger_reason) else "no",
                                "trigger": ", ".join(trigger_reason),
                                "ratio": "{:.1f}:1".format(risk_reward_ratio)
                            })
                            logging.info("Backtest sell: {} shares of {} at ${:.2f} on {}, profit={:.2f}, trailing={}, triggers={}, ratio={:.1f}:1".format(
                                sell_shares, stock, price, index, pl, trailing_active, ", ".join(trigger_reason), risk_reward_ratio))
                            shares_to_sell -= sell_shares
                            buy_shares[i] -= sell_shares
                        buy_cost_basis = [cb for i, cb in enumerate(buy_cost_basis) if buy_shares[i] > 0]
                        buy_shares = [s for s in buy_shares if s > 0]
                        self.mock_portfolio[stock] = 0
                        logging.debug("Backtest sell: {} shares of {} at ${:.2f}, total_profit={:.2f}".format(total_shares, stock, price, total_profit))
                        buy_price = None
                        last_buy_index = None
                        trailing_active = False
            logging.info("Trade summary for {}: total_entries={}, below_2:1={}, between_1:1_and_2:1={}, possible_trades={}, buys={}".format(
                stock, total_entries, below_2_to_1, one_to_two_to_1, total_possible_trades, total_buys))
            if "Backtest" in self.indicator_tables:
                self.indicator_tables["Backtest"].delete(*self.indicator_tables["Backtest"].get_children())
                for stock_tx, transactions in self.mock_transaction_history.items():
                    for t in transactions:
                        if t["action"] == "Sell":
                            pl = sum(trade["profit"] for trade in self.backtest_trade_pairs if trade["stock"] == stock_tx and trade["sell_time"] == t["time"])
                            tag = "profit" if pl > 0 else "loss" if pl < 0 else ""
                            self.indicator_tables["Backtest"].insert("", "end", values=(
                                "{} {} {} @ ${:.2f} on {}".format(t["action"], stock_tx, t["shares"], t["price"], t["time"]),
                                "{:.2f}".format(pl), ""
                            ), tags=(tag,))
            self.update_portfolio_table()
        except KeyError as e:
            if str(e) == "'Backtest'":
                logging.warning("Backtest tab not ready during replay for {}; skipping tree ops".format(stock))
            else:
                raise
        except Exception as e:
            logging.error("Error replaying transactions for {}: {}".format(stock, e))
            self.status_label.config(text="Error replaying transactions for {}".format(stock))
            beep()
			
    def clear_entry_frame(self):
        self.target_entry.delete(0, tk.END)
        self.stop_loss_entry.delete(0, tk.END)
        self.entry_frame.pack_forget()		
		
    # Snippet 258: Fixed main method indentation (ensure it's inside the class, replace the def main block)
    def main(self):
        logging.debug("Starting main loop")
        try:
            self.root.mainloop()
        except Exception as e:
            logging.error("Error in main loop: {}".format(e))
            if hasattr(self, 'speech_engine') and self.speech_engine and not self.is_muted.get():
                self.speak("Error in main loop")
            beep()
			
if __name__ == "__main__":
    root = tk.Tk()
    app = StockSignalsApp(root)

    app.main()			
