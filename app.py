#!/usr/bin/env python3
"""
Главный файл приложения версии 2.0
"""

import streamlit as st
from auth import login_page, show_user_info, check_access, logout
import crm_system
import analytics_dashboard
import directories
import audit_viewer
import backup_manager
import notification_manager
import import_manager
import user_management
from database import init_database, create_default_users, create_default_data, migrate_old_appointments

def main():
    """Главная функция приложения версии 2.0"""
    st.set_page_config(
        page_title="Jardem - Система CRM и управления данными Медицинского центра",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Инициализация базы данных при первом запуске
    if 'db_initialized' not in st.session_state:
        # Пытаемся получить последнюю версию базы данных из Git
        try:
            from git_sync import pull_database_from_git
            pull_result = pull_database_from_git()
            if pull_result:
                st.success("📥 База данных обновлена из Git")
            else:
                st.info("ℹ️ База данных не обновлена из Git (возможно, нет изменений)")
        except Exception as e:
            st.warning(f"⚠️ Не удалось обновить базу данных из Git: {e}")
        
        init_database()
        create_default_users()
        create_default_data()
        # Миграция старых приемов в новую структуру
        migrate_old_appointments()
        st.session_state['db_initialized'] = True
        
        # Синхронизируем начальное состояние с Git (синхронно для надежности)
        try:
            from git_sync import sync_database_to_git_sync
            sync_result = sync_database_to_git_sync("Initial database setup", push=True)
            if sync_result:
                st.success("✅ База данных синхронизирована с Git")
            else:
                st.warning("⚠️ Не удалось синхронизировать базу данных с Git")
        except Exception as e:
            st.warning(f"⚠️ Ошибка синхронизации с Git: {e}")
    
    # Выполняем миграции при каждом запуске для обеспечения совместимости
    try:
        from migrate_database import migrate_database
        migrate_database()
    except Exception as e:
        st.error(f"Ошибка миграции базы данных: {e}")
    
    # Проверяем аутентификацию
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        login_page()
        return
    
    # Проверяем, нужно ли показать форму смены пароля
    if st.session_state.get('show_change_password', False):
        from change_password import main as change_password_main
        change_password_main()
        return
    
    # Получаем уровень доступа пользователя
    user_access_level = st.session_state.get('access_level', '')
    
    # Навигация в sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("Навигация")
        
        # Создаем список страниц в зависимости от уровня доступа
        # CRM Система теперь первая во всех списках
        if user_access_level == 'owner':
            pages = ["CRM Система", "Аналитика", "Справочники", "Управление пользователями"]
        elif user_access_level == 'admin':
            pages = [
                "CRM Система",
                "Аналитика",
                "Справочники",
                "Управление пользователями",
                "Аудит",
                "Уведомления",
                "Резервные копии",
                "Импорт данных"
            ]
        elif user_access_level == 'crm':
            pages = ["CRM Система", "Аналитика (сегодня)", "Справочники"]
        else:
            pages = []
            
        # Radio buttons для навигации
        if pages:
            page = st.radio(
                "Выберите модуль:",
                pages,
                label_visibility="collapsed"
            )
        else:
            st.error("❌ Неизвестный уровень доступа")
            return
        
        # Показываем информацию о пользователе
        show_user_info()
    
    # Главное меню
    st.title("Jardem - Система CRM и управления данными Медицинского центра")
    st.markdown("---")
    
    # Проверяем, нужно ли показать форму смены пароля
    if st.session_state.get('show_change_password', False):
        from change_password import main as change_password_main
        change_password_main()
        return
    
    # Роутинг страниц
    if page == "Аналитика":
        analytics_dashboard.main()
    elif page == "Аналитика (сегодня)":
        # Для CRM пользователей показываем аналитику только за сегодня
        st.session_state['analytics_today_only'] = True
        analytics_dashboard.main()
    elif page == "CRM Система":
        crm_system.main()
    elif page == "Справочники":
        directories.main()
    elif page == "Управление пользователями":
        user_management.main()
    elif page == "Аудит":
        audit_viewer.main()
    elif page == "Уведомления":
        notification_manager.main()
    elif page == "Резервные копии":
        backup_manager.main()
    elif page == "Импорт данных":
        import_manager.main()

if __name__ == "__main__":
    main()
