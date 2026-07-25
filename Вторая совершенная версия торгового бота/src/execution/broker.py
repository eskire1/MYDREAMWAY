"""
src/execution/broker.py
Взаимодействие с BingX (swap/futures API) с retry и корректным testnet URL.
"""

import os
import time
import hmac
import hashlib
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode
from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL_PROD = "https://open-api.bingx.com"
BASE_URL_VST = "https://open-api-vst.bingx.com"


@dataclass
class OrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    leverage: int = 1
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class OrderResponse:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: Optional[float]
    status: str
    timestamp: datetime


class BingXBroker:
    """Брокер BingX swap API."""

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key or os.getenv("BINGX_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINGX_API_SECRET", "")
        self.testnet = testnet if testnet is not None else (
            os.getenv("BINGX_TESTNET", "true").lower() == "true"
        )
        self.base_url = BASE_URL_VST if self.testnet else BASE_URL_PROD

        self.session = requests.Session()
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST", "DELETE"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=8)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": "ApexV5/1.0",
            "Accept": "application/json",
        })

        if not self.api_key or not self.api_secret:
            logger.warning("API ключи BingX не заданы — приватные методы недоступны.")
        logger.info(f"BingX broker: {'VST/testnet' if self.testnet else 'production'} → {self.base_url}")

        self._price_cache: Dict[str, float] = {}
        self._spread_cache: Dict[str, float] = {}

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """ETH-USDT / ETHUSDT → ETH-USDT."""
        s = symbol.upper().replace("/", "-")
        if "-" not in s and s.endswith("USDT"):
            base = s[:-4]
            return f"{base}-USDT"
        return s

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        sorted_keys = sorted(params.keys())
        query_string = "&".join([f"{k}={params[k]}" for k in sorted_keys])
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        signed: bool = False,
    ) -> Dict:
        url = f"{self.base_url}{endpoint}"
        request_params = dict(params or {})

        headers: Dict[str, str] = {}
        if signed:
            if not self.api_key or not self.api_secret:
                raise ValueError("Для подписанных запросов нужны API ключи.")
            request_params["timestamp"] = int(time.time() * 1000)
            request_params["signature"] = self._generate_signature(request_params)
            headers["X-BX-APIKEY"] = self.api_key

        last_error: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                if method == "GET":
                    response = self.session.get(
                        url, params=request_params, headers=headers, timeout=(10, 30)
                    )
                elif method == "POST":
                    headers["Content-Type"] = "application/json"
                    response = self.session.post(
                        url, headers=headers, json=request_params, timeout=(10, 30)
                    )
                elif method == "DELETE":
                    headers["Content-Type"] = "application/json"
                    response = self.session.delete(
                        url, headers=headers, json=request_params, timeout=(10, 30)
                    )
                else:
                    raise ValueError(f"Неподдерживаемый метод: {method}")

                response.raise_for_status()
                data = response.json()

                if data.get("code") and data["code"] != 0:
                    error_msg = data.get("msg", "Неизвестная ошибка API")
                    logger.error(f"BingX API code {data['code']}: {error_msg}")
                    raise Exception(f"BingX API Error: {error_msg}")

                return data

            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                last_error = e
                wait = attempt * 2
                logger.warning(
                    f"BingX сеть (попытка {attempt}/3) {endpoint}: {e}. Повтор через {wait}с…"
                )
                time.sleep(wait)
            except requests.exceptions.RequestException as e:
                logger.error(f"Сетевая ошибка BingX {endpoint}: {e}")
                raise

        logger.error(f"BingX: исчерпаны попытки для {endpoint}: {last_error}")
        raise last_error  # type: ignore[misc]

    def test_connection(self, symbol: str = "ETH-USDT") -> bool:
        """Проверка публичного API (свечи)."""
        try:
            klines = self.get_klines(symbol, limit=2)
            return len(klines) > 0
        except Exception as e:
            logger.error(f"test_connection failed: {e}")
            return False

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        params = {"symbol": symbol}
        data = self._make_request("GET", "/openApi/swap/v2/quote/ticker", params)
        ticker = data.get("data", {})
        if isinstance(ticker, list):
            ticker = ticker[0] if ticker else {}
        return {
            "symbol": symbol,
            "bid": float(ticker.get("bidPrice", ticker.get("bid", 0)) or 0),
            "ask": float(ticker.get("askPrice", ticker.get("ask", 0)) or 0),
            "last": float(ticker.get("lastPrice", ticker.get("last", 0)) or 0),
            "spread": 0.0,
            "timestamp": datetime.now(),
        }

    def get_klines(self, symbol: str, interval: str = "15m", limit: int = 100) -> List[Dict]:
        symbol = self._normalize_symbol(symbol)
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        data = self._make_request("GET", "/openApi/swap/v2/quote/klines", params)
        klines = data.get("data", [])
        formatted = []
        for k in klines:
            if isinstance(k, dict):
                formatted.append({
                    "timestamp": datetime.fromtimestamp(k["time"] / 1000),
                    "open": float(k["open"]),
                    "high": float(k["high"]),
                    "low": float(k["low"]),
                    "close": float(k["close"]),
                    "volume": float(k["volume"]),
                })
            elif isinstance(k, (list, tuple)) and len(k) >= 6:
                formatted.append({
                    "timestamp": datetime.fromtimestamp(k[0] / 1000),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                })
        return formatted

    def get_account_balance(self) -> Dict[str, float]:
        data = self._make_request("GET", "/openApi/swap/v2/user/balance", signed=True)
        balance_info = data.get("data", {}).get("balance", data.get("data", {}))
        if isinstance(balance_info, list) and balance_info:
            balance_info = balance_info[0]
        asset = balance_info.get("asset", "USDT") if isinstance(balance_info, dict) else "USDT"
        free = balance_info.get("balance", balance_info.get("free", 0)) if isinstance(balance_info, dict) else 0
        return {asset: float(free)}

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        balances = self.get_account_balance()
        base_asset = symbol.replace("-USDT", "")
        if base_asset in balances:
            return {"symbol": symbol, "asset": base_asset, "amount": balances[base_asset]}
        return None

    def send_order(self, request: OrderRequest) -> OrderResponse:
        params = {
            "symbol": self._normalize_symbol(request.symbol),
            "side": request.side,
            "type": request.order_type,
            "quantity": str(request.quantity),
        }
        if request.leverage:
            params["leverage"] = str(request.leverage)
        if request.stop_loss:
            params["stopLossPrice"] = str(request.stop_loss)
        if request.take_profit:
            params["takeProfitPrice"] = str(request.take_profit)

        data = self._make_request("POST", "/openApi/swap/v2/trade/order", params, signed=True)
        order_data = data.get("data", {})
        return OrderResponse(
            order_id=str(order_data.get("orderId", "")),
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            status=order_data.get("status", "UNKNOWN"),
            timestamp=datetime.now(),
        )

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        params = {"orderId": order_id, "symbol": self._normalize_symbol(symbol)}
        try:
            self._make_request("DELETE", "/openApi/swap/v2/trade/order", params, signed=True)
            return True
        except Exception as e:
            logger.error(f"Не удалось отменить ордер {order_id}: {e}")
            return False

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        params = {"symbol": self._normalize_symbol(symbol), "leverage": str(leverage)}
        try:
            self._make_request("POST", "/openApi/swap/v2/trade/leverage", params, signed=True)
            return True
        except Exception as e:
            logger.warning(f"set_leverage: {e}")
            return False

    def get_current_price(self, symbol: str) -> float:
        t = self.get_ticker(symbol)
        t["spread"] = t["ask"] - t["bid"] if t["ask"] and t["bid"] else 0.0
        return t["last"]

    def get_spread(self, symbol: str) -> float:
        t = self.get_ticker(symbol)
        return t["ask"] - t["bid"]

    def get_atr(self, symbol: str, period: int = 50) -> float:
        klines = self.get_klines(symbol, interval="15m", limit=period + 1)
        if len(klines) < period:
            return 0.0
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        closes = [k["close"] for k in klines]
        trs = []
        for i in range(1, len(klines)):
            trs.append(max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            ))
        return sum(trs[-period:]) / period
