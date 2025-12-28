#!/usr/bin/env python3
"""
Утилиты для работы с часовыми поясами
"""

from datetime import datetime, date, timezone, timedelta
import os

# Часовой пояс по умолчанию (Казахстан - UTC+6)
DEFAULT_TIMEZONE_OFFSET = int(os.getenv('TIMEZONE_OFFSET', '6'))  # UTC+6 для Казахстана
DEFAULT_TIMEZONE_NAME = os.getenv('TIMEZONE_NAME', 'Asia/Almaty')

def get_local_timezone():
    """Получить локальный часовой пояс"""
    try:
        import pytz
        return pytz.timezone(DEFAULT_TIMEZONE_NAME)
    except ImportError:
        # Если pytz не установлен, используем фиксированное смещение
        return timezone(timedelta(hours=DEFAULT_TIMEZONE_OFFSET))

def get_local_now():
    """Получить текущее время в локальном часовом поясе"""
    try:
        import pytz
        tz = pytz.timezone(DEFAULT_TIMEZONE_NAME)
        return datetime.now(tz)
    except ImportError:
        # Если pytz не установлен, используем UTC + смещение
        utc_now = datetime.now(timezone.utc)
        local_tz = timezone(timedelta(hours=DEFAULT_TIMEZONE_OFFSET))
        return utc_now.astimezone(local_tz)

def get_local_today():
    """Получить текущую дату в локальном часовом поясе"""
    local_now = get_local_now()
    return local_now.date()

def get_local_datetime():
    """Получить текущую дату и время в локальном часовом поясе"""
    return get_local_now()

