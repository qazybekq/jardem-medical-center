#!/usr/bin/env python3
"""
Модуль для автоматической синхронизации базы данных с Git
Автоматически коммитит и пушит изменения в репозиторий
"""

import subprocess
import os
import time
from datetime import datetime

# Попытка импорта streamlit (может быть недоступен)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Флаг для включения/выключения Git синхронизации
# Проверяем переменные окружения и Streamlit secrets
GIT_SYNC_ENABLED = os.getenv('GIT_SYNC_ENABLED', 'true').lower() == 'true'
if STREAMLIT_AVAILABLE:
    try:
        if hasattr(st, 'secrets') and 'GIT_SYNC_ENABLED' in st.secrets:
            GIT_SYNC_ENABLED = str(st.secrets['GIT_SYNC_ENABLED']).lower() == 'true'
    except:
        pass

GIT_BRANCH = os.getenv('GIT_BRANCH', 'main')
GIT_REMOTE = os.getenv('GIT_REMOTE', 'origin')
DB_FILE = 'medical_center.db'

# Настройка Git (для Streamlit Cloud)
GIT_USER_NAME = os.getenv('GIT_USER_NAME', 'Streamlit Cloud')
GIT_USER_EMAIL = os.getenv('GIT_USER_EMAIL', 'streamlit@cloud.com')

if STREAMLIT_AVAILABLE:
    try:
        if hasattr(st, 'secrets'):
            if 'GIT_USER_NAME' in st.secrets:
                GIT_USER_NAME = st.secrets['GIT_USER_NAME']
            if 'GIT_USER_EMAIL' in st.secrets:
                GIT_USER_EMAIL = st.secrets['GIT_USER_EMAIL']
            if 'GIT_BRANCH' in st.secrets:
                GIT_BRANCH = st.secrets['GIT_BRANCH']
            if 'GIT_REMOTE' in st.secrets:
                GIT_REMOTE = st.secrets['GIT_REMOTE']
    except:
        pass


def setup_git_config():
    """Настройка Git конфигурации"""
    try:
        subprocess.run(
            ['git', 'config', 'user.name', GIT_USER_NAME],
            check=True,
            capture_output=True,
            timeout=5
        )
        subprocess.run(
            ['git', 'config', 'user.email', GIT_USER_EMAIL],
            check=True,
            capture_output=True,
            timeout=5
        )
        return True
    except Exception as e:
        print(f"Warning: Could not setup git config: {e}")
        return False


def is_git_repo():
    """Проверка, является ли директория Git репозиторием"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def git_add_and_commit(message="Auto-commit: Database update"):
    """Добавить изменения в Git и создать коммит"""
    if not GIT_SYNC_ENABLED:
        print("Git sync is disabled, skipping commit")
        return False
    
    if not is_git_repo():
        print("Not a git repository, skipping commit")
        return False
    
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found, skipping commit")
        return False
    
    try:
        # Настройка Git
        setup_git_config()
        
        # Проверяем статус перед добавлением
        result = subprocess.run(
            ['git', 'status', '--porcelain', DB_FILE],
            capture_output=True,
            timeout=5,
            text=True
        )
        
        # Добавляем файл базы данных
        print(f"Adding {DB_FILE} to git...")
        result = subprocess.run(
            ['git', 'add', DB_FILE],
            capture_output=True,
            timeout=10,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Git add failed: {result.stderr}")
            return False
        
        # Проверяем, есть ли изменения для коммита
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Нет изменений в staged area
            print("No changes to commit (file unchanged)")
            return True
        
        # Создаем коммит
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message} - {timestamp}"
        
        print(f"Committing changes: {commit_message}")
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            capture_output=True,
            timeout=10,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            print(f"❌ Git commit failed: {error_msg}")
            return False
        
        print(f"✅ Git commit successful: {commit_message}")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Git operation timed out")
        return False
    except Exception as e:
        print(f"❌ Git commit error: {e}")
        import traceback
        traceback.print_exc()
        return False


def git_push():
    """Отправить изменения в удаленный репозиторий"""
    if not GIT_SYNC_ENABLED:
        print("Git sync is disabled, skipping push")
        return False
    
    if not is_git_repo():
        print("Not a git repository, skipping push")
        return False
    
    try:
        # Настройка Git
        setup_git_config()
        
        # Получаем текущую ветку
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            timeout=5,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Could not get current branch: {result.stderr}")
            return False
        
        current_branch = result.stdout.strip()
        print(f"Current branch: {current_branch}")
        
        # Проверяем, есть ли что коммитить
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            timeout=5,
            text=True
        )
        
        if result.returncode == 0 and not result.stdout.strip():
            # Нет изменений для коммита
            print("No changes to commit")
            # Но все равно проверяем, есть ли что пушить
            result = subprocess.run(
                ['git', 'log', '--oneline', f'{GIT_REMOTE}/{current_branch}..HEAD'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if not result.stdout.strip():
                print("Nothing to push")
                return True
        
        # Сначала делаем pull, чтобы избежать конфликтов
        print("Pulling latest changes...")
        try:
            pull_result = subprocess.run(
                ['git', 'pull', GIT_REMOTE, current_branch, '--no-edit', '--no-rebase', '--no-ff'],
                capture_output=True,
                timeout=20,
                text=True
            )
            if pull_result.returncode != 0:
                print(f"Pull warning: {pull_result.stderr}")
            else:
                print("Pull successful")
        except Exception as e:
            print(f"Pull error (continuing anyway): {e}")
        
        # Пушим изменения
        print(f"Pushing to {GIT_REMOTE}/{current_branch}...")
        result = subprocess.run(
            ['git', 'push', GIT_REMOTE, current_branch],
            capture_output=True,
            timeout=30,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            print(f"❌ Git push failed: {error_msg}")
            print(f"Return code: {result.returncode}")
            return False
        
        print(f"✅ Git push successful!")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Git push timed out")
        return False
    except Exception as e:
        print(f"❌ Git push error: {e}")
        import traceback
        traceback.print_exc()
        return False


def sync_database_to_git(message="Auto-commit: Database update", push=True):
    """
    Синхронизировать базу данных с Git
    
    Args:
        message: Сообщение коммита
        push: Отправлять ли изменения в удаленный репозиторий
    
    Returns:
        bool: Успешно ли выполнена синхронизация
    """
    if not GIT_SYNC_ENABLED:
        print("Git sync is disabled")
        return False
    
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found")
        return False
    
    # Коммитим изменения
    if not git_add_and_commit(message):
        print(f"Failed to commit changes: {message}")
        return False
    
    # Пушим изменения, если требуется
    if push:
        # Небольшая задержка перед push (на случай множественных операций)
        time.sleep(0.5)
        push_result = git_push()
        if push_result:
            print(f"✅ Successfully synced to Git: {message}")
        else:
            print(f"⚠️ Failed to push to Git: {message}")
        return push_result
    
    return True


def sync_database_to_git_async(message="Auto-commit: Database update", push=True):
    """
    Асинхронная синхронизация (не блокирует основной поток)
    Запускается в фоновом режиме
    """
    import threading
    
    def sync_thread():
        try:
            result = sync_database_to_git(message, push)
            if result:
                print(f"✅ Git sync successful: {message}")
            else:
                print(f"⚠️ Git sync failed: {message}")
        except Exception as e:
            print(f"❌ Async git sync error: {e}")
            import traceback
            traceback.print_exc()
    
    thread = threading.Thread(target=sync_thread, daemon=True)
    thread.start()
    return thread


def sync_database_to_git_sync(message="Auto-commit: Database update", push=True):
    """
    Синхронная синхронизация (блокирует до завершения)
    Используется для критических операций
    """
    return sync_database_to_git(message, push)


def pull_database_from_git():
    """
    Получить последнюю версию базы данных из Git
    Используется при старте приложения
    """
    if not GIT_SYNC_ENABLED:
        return False
    
    if not is_git_repo():
        return False
    
    try:
        # Настройка Git
        setup_git_config()
        
        # Получаем изменения из удаленного репозитория
        result = subprocess.run(
            ['git', 'pull', GIT_REMOTE, GIT_BRANCH, '--no-edit'],
            capture_output=True,
            timeout=30,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Git pull failed: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("Git pull timed out")
        return False
    except Exception as e:
        print(f"Git pull error: {e}")
        return False


# Проверка доступности Git при импорте модуля
if GIT_SYNC_ENABLED:
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            print("Warning: Git is not available")
            GIT_SYNC_ENABLED = False
    except Exception:
        print("Warning: Git is not available")
        GIT_SYNC_ENABLED = False

