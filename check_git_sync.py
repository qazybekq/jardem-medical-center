#!/usr/bin/env python3
"""
Скрипт для проверки работы Git синхронизации
"""

import os
import subprocess

def check_git_sync():
    """Проверить настройку Git синхронизации"""
    print("=" * 80)
    print("🔍 ПРОВЕРКА GIT СИНХРОНИЗАЦИИ")
    print("=" * 80)
    
    # Проверка переменных окружения
    print("\n1. Проверка переменных окружения:")
    git_sync_enabled = os.getenv('GIT_SYNC_ENABLED', 'true').lower() == 'true'
    print(f"   GIT_SYNC_ENABLED: {git_sync_enabled}")
    
    # Проверка Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'GIT_SYNC_ENABLED' in st.secrets:
            git_sync_enabled = str(st.secrets['GIT_SYNC_ENABLED']).lower() == 'true'
            print(f"   GIT_SYNC_ENABLED (from secrets): {git_sync_enabled}")
    except:
        pass
    
    # Проверка Git репозитория
    print("\n2. Проверка Git репозитория:")
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("   ✅ Git репозиторий найден")
        else:
            print("   ❌ Git репозиторий не найден")
            return
    except Exception as e:
        print(f"   ❌ Ошибка проверки Git: {e}")
        return
    
    # Проверка базы данных
    print("\n3. Проверка базы данных:")
    db_file = 'medical_center.db'
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f"   ✅ База данных найдена ({size} bytes)")
    else:
        print("   ❌ База данных не найдена")
        return
    
    # Проверка статуса Git
    print("\n4. Проверка статуса Git:")
    try:
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.stdout.strip():
            print(f"   ⚠️  Есть незакоммиченные изменения:")
            print(f"   {result.stdout}")
        else:
            print("   ✅ Нет незакоммиченных изменений")
    except Exception as e:
        print(f"   ❌ Ошибка проверки статуса: {e}")
    
    # Проверка удаленного репозитория
    print("\n5. Проверка удаленного репозитория:")
    try:
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✅ Удаленные репозитории:")
            print(f"   {result.stdout}")
        else:
            print("   ❌ Не удалось получить список удаленных репозиториев")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест синхронизации
    print("\n6. Тест синхронизации:")
    try:
        from git_sync import sync_database_to_git_sync
        print("   Попытка синхронизации...")
        result = sync_database_to_git_sync("Test sync", push=True)
        if result:
            print("   ✅ Синхронизация успешна!")
        else:
            print("   ⚠️  Синхронизация не выполнена (возможно, нет изменений)")
    except Exception as e:
        print(f"   ❌ Ошибка синхронизации: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Проверка завершена")
    print("=" * 80)

if __name__ == "__main__":
    check_git_sync()

