"""
Integration Utils - Közös segédfüggvények integrációkhoz.

Ez a modul tartalmazza az ismétlődő integrációs logikákat és segédfüggvényeket.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import aiohttp
from pydantic import BaseModel

from ..config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class APIConfig:
    """API konfiguráció közös struktúra."""
    api_key: str
    base_url: str
    timeout: int = 30
    retries: int = 3
    retry_delay: float = 1.0
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ChatBuddy-MVP/1.0'
            }


@dataclass
class APIResponse:
    """API válasz közös struktúra."""
    success: bool
    status_code: int
    data: Optional[Any] = None
    error_message: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    response_time: Optional[float] = None


class BaseAPIClient(ABC):
    """Közös API kliens alaposztály."""

    def __init__(self, config: APIConfig):
        """
        API kliens inicializálása.

        Args:
            config: API konfiguráció
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager belépés."""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager kilépés."""
        await self._close_session()

    async def _create_session(self):
        """HTTP session létrehozása."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                headers=self.config.headers,
                timeout=timeout
            )

    async def _close_session(self):
        """HTTP session lezárása."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        HTTP kérés végrehajtása retry logikával.

        Args:
            method: HTTP metódus
            endpoint: API végpont
            data: Kérés body
            params: URL paraméterek

        Returns:
            API válasz
        """
        await self._create_session()

        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.config.retries):
            start_time = time.time()

            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                ) as response:
                    response_time = time.time() - start_time
                    response_data = None

                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()

                    # Retry on 5xx once more if allowed
                    if 500 <= response.status < 600 and attempt < self.config.retries - 1:
                        # fall-through to retry delay
                        pass
                    else:
                        return APIResponse(
                            success=response.status < 400,
                            status_code=response.status,
                            data=response_data,
                            headers=dict(response.headers),
                            response_time=response_time,
                            error_message=None if response.status < 400 else f"HTTP {response.status}"
                        )

            except asyncio.TimeoutError:
                error_msg = f"Timeout on attempt {attempt + 1}/{self.config.retries}"
                logger.warning(error_msg)

                if attempt == self.config.retries - 1:
                    return APIResponse(
                        success=False,
                        status_code=408,
                        error_message="Request timeout",
                        response_time=time.time() - start_time
                    )

            except Exception as e:
                error_msg = f"Request failed on attempt {attempt + 1}/{self.config.retries}: {str(e)}"
                logger.warning(error_msg)

                if attempt == self.config.retries - 1:
                    return APIResponse(
                        success=False,
                        status_code=500,
                        error_message=str(e),
                        response_time=time.time() - start_time
                    )

            # Retry delay
            if attempt < self.config.retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> APIResponse:
        """GET kérés."""
        return await self._make_request('GET', endpoint, params=params)

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> APIResponse:
        """POST kérés."""
        return await self._make_request('POST', endpoint, data=data)

    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> APIResponse:
        """PUT kérés."""
        return await self._make_request('PUT', endpoint, data=data)

    async def delete(self, endpoint: str) -> APIResponse:
        """DELETE kérés."""
        return await self._make_request('DELETE', endpoint)


class ErrorHandler:
    """Közös hibakezelési logika."""

    @staticmethod
    def handle_api_error(response: APIResponse, context: str = "API call") -> Optional[Exception]:
        """
        API hiba kezelése.

        Args:
            response: API válasz
            context: Hiba kontextus

        Returns:
            Exception ha volt hiba, egyébként None
        """
        if response.success:
            return None

        error_msg = f"{context} failed"

        if response.error_message:
            error_msg += f": {response.error_message}"

        if response.status_code:
            error_msg += f" (HTTP {response.status_code})"

        logger.error(error_msg)

        # Különböző hibatípusok kezelése
        if response.status_code == 401:
            return PermissionError("Authentication failed")
        elif response.status_code == 403:
            return PermissionError("Access forbidden")
        elif response.status_code == 404:
            return FileNotFoundError("Resource not found")
        elif response.status_code == 429:
            return ConnectionError("Rate limit exceeded")
        elif response.status_code >= 500:
            return ConnectionError("Server error")
        else:
            return Exception(error_msg)

    @staticmethod
    async def with_error_handling(
        func: Callable,
        context: str = "Operation",
        default_return: Any = None,
        raise_on_error: bool = False
    ) -> Any:
        """
        Funkció végrehajtása hibakezelési wrapper-rel.

        Args:
            func: Végrehajtandó függvény
            context: Hiba kontextus
            default_return: Alapértelmezett visszatérési érték hiba esetén
            raise_on_error: Dobja-e újra a hibát

        Returns:
            Függvény eredménye vagy default_return
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except Exception as e:
            logger.error(f"{context} failed: {str(e)}")

            if raise_on_error:
                raise

            return default_return


class CacheHelper:
    """Cache segédosztály."""

    @staticmethod
    def generate_cache_key(*args, prefix: str = "cache") -> str:
        """
        Cache kulcs generálása.

        Args:
            *args: Kulcs elemek
            prefix: Kulcs prefix

        Returns:
            Hash alapú cache kulcs
        """
        key_data = ":".join(str(arg) for arg in args)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    @staticmethod
    def serialize_for_cache(data: Any) -> str:
        """
        Adat szerializálása cache-hez.

        Args:
            data: Szerializálandó adat

        Returns:
            JSON string
        """
        try:
            if isinstance(data, BaseModel):
                return data.model_dump_json()
            elif hasattr(data, '__dict__'):
                if hasattr(data, '__dataclass_fields__'):
                    return json.dumps(asdict(data), default=str)
                else:
                    return json.dumps(data.__dict__, default=str)
            else:
                return json.dumps(data, default=str)
        except Exception as e:
            logger.warning(f"Serialization failed: {e}, returning empty dict")
            return json.dumps({})

    @staticmethod
    def deserialize_from_cache(data: str, target_type: Optional[type] = None) -> Any:
        """
        Adat deszerializálása cache-ből.

        Args:
            data: JSON string
            target_type: Célitpus (opcionális)

        Returns:
            Deszerializált adat
        """
        try:
            parsed_data = json.loads(data)

            if target_type and hasattr(target_type, '__dataclass_fields__'):
                return target_type(**parsed_data)
            elif target_type and issubclass(target_type, BaseModel):
                return target_type.model_validate(parsed_data)
            else:
                return parsed_data
        except Exception as e:
            logger.warning(f"Deserialization failed: {e}, returning empty dict")
            return {}


class ConfigManager:
    """Konfiguráció kezelő segédosztály."""

    @staticmethod
    def load_api_config(
        service_name: str,
        required_keys: Optional[List[str]] = None,
        env_prefix: Optional[str] = None
    ) -> APIConfig:
        """
        API konfiguráció betöltése environment változókból.

        Args:
            service_name: Szolgáltatás neve
            required_keys: Kötelező kulcsok
            env_prefix: Environment prefix

        Returns:
            API konfiguráció
        """
        import os

        prefix = env_prefix or service_name.upper()
        required_keys = required_keys or ['API_KEY', 'BASE_URL']

        config_data = {}
        for key in required_keys:
            env_key = f"{prefix}_{key}"
            value = os.getenv(env_key)

            if not value:
                raise ValueError(f"Missing required environment variable: {env_key}")

            config_data[key.lower()] = value

        # Optional konfigurációk
        config_data['timeout'] = int(os.getenv(f"{prefix}_TIMEOUT", "30"))
        config_data['retries'] = int(os.getenv(f"{prefix}_RETRIES", "3"))
        config_data['retry_delay'] = float(os.getenv(f"{prefix}_RETRY_DELAY", "1.0"))

        return APIConfig(**config_data)

    @staticmethod
    def validate_config(config: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Konfiguráció validálása.

        Args:
            config: Konfiguráció dictionary
            required_fields: Kötelező mezők

        Returns:
            Valid-e a konfiguráció
        """
        missing_fields = []

        for field in required_fields:
            if field not in config or config[field] is None:
                missing_fields.append(field)

        if missing_fields:
            logger.error(f"Missing required config fields: {missing_fields}")
            return False

        return True


class DataTransformer:
    """Adat transzformációs segédosztály."""

    @staticmethod
    def normalize_keys(data: Dict[str, Any], key_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Dictionary kulcsok normalizálása.

        Args:
            data: Eredeti adat
            key_mapping: Kulcs mapping (opcionális)

        Returns:
            Normalizált adat
        """
        if not isinstance(data, dict):
            return data

        normalized = {}

        for key, value in data.items():
            # Kulcs mapping alkalmazása
            new_key = key_mapping.get(key, key) if key_mapping else key

            # Snake_case konverzió
            new_key = new_key.lower().replace(' ', '_').replace('-', '_')

            # Nested dictionary kezelése
            if isinstance(value, dict):
                normalized[new_key] = DataTransformer.normalize_keys(value, key_mapping)
            elif isinstance(value, list):
                normalized[new_key] = [
                    DataTransformer.normalize_keys(item, key_mapping) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[new_key] = value

        return normalized

    @staticmethod
    def flatten_dict(data: Dict[str, Any], separator: str = '.', prefix: str = '') -> Dict[str, Any]:
        """
        Nested dictionary laposítása.

        Args:
            data: Eredeti adat
            separator: Kulcs elválasztó
            prefix: Kulcs prefix

        Returns:
            Lapos dictionary
        """
        flattened = {}

        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key

            if isinstance(value, dict):
                flattened.update(
                    DataTransformer.flatten_dict(value, separator, new_key)
                )
            else:
                flattened[new_key] = value

        return flattened

    @staticmethod
    def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None, separator: str = '.') -> Any:
        """
        Biztonságos nested érték lekérése.

        Args:
            data: Adat dictionary
            path: Elérési út (pl. "user.profile.name")
            default: Alapértelmezett érték
            separator: Út elválasztó

        Returns:
            Érték vagy default
        """
        try:
            keys = path.split(separator)
            current_data = data

            for key in keys:
                if isinstance(current_data, dict) and key in current_data:
                    current_data = current_data[key]
                else:
                    return default

            return current_data
        except Exception:
            return default


class RateLimiter:
    """Egyszerű rate limiter implementáció."""

    def __init__(self, max_calls: int, time_window: int):
        """
        Rate limiter inicializálása.

        Args:
            max_calls: Maximum hívások száma
            time_window: Időablak másodpercekben
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    async def can_proceed(self) -> bool:
        """
        Ellenőrzi, hogy folytatható-e a művelet.

        Returns:
            True ha folytatható
        """
        now = time.time()

        # Lejárt bejegyzések törlése
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

        # Rate limit ellenőrzése
        if len(self.calls) >= self.max_calls:
            return False

        # Jelenlegi hívás rögzítése
        self.calls.append(now)
        return True

    async def wait_if_needed(self):
        """Vár ha szükséges a rate limit miatt."""
        if not await self.can_proceed():
            # Számítás: mikor lesz szabad hely
            oldest_call = min(self.calls)
            wait_time = self.time_window - (time.time() - oldest_call) + 0.1

            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)


# Közös validátor funkciók
def validate_email(email: str) -> bool:
    """Email cím validálása."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Telefonszám validálása (magyar formátum)."""
    import re
    # Magyar mobil: +36 XX XXX XXXX vagy 06 XX XXX XXXX
    patterns = [
        r'^\+36\s?[0-9]{2}\s?[0-9]{3}\s?[0-9]{4}$',
        r'^06\s?[0-9]{2}\s?[0-9]{3}\s?[0-9]{4}$',
        r'^[0-9]{11}$'
    ]

    return any(re.match(pattern, phone.replace(' ', '').replace('-', '')) for pattern in patterns)


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Input szöveg megtisztítása és korlátozása."""
    if not isinstance(text, str):
        text = str(text)

    # HTML tagek eltávolítása
    import re
    text = re.sub(r'<[^>]+>', '', text)

    # Whitespace normalizálás
    text = ' '.join(text.split())

    # Hossz korlátozása
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'

    return text.strip()
