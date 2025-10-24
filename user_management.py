#!/usr/bin/env python3
"""
Модуль управления пользователями системы
Доступен только для владельца (owner) и администратора (admin)
"""

import streamlit as st
import secrets
import string
from database import (
    get_all_users, create_user, update_user_password, 
    update_user_access_level, delete_user, reset_user_password,
    log_audit_action
)

def main():
    """Главная функция модуля управления пользователями"""
    st.header("👥 Управление пользователями")
    st.markdown("---")
    
    # Проверяем права доступа
    user_access_level = st.session_state.get('access_level', '')
    if user_access_level not in ['owner', 'admin']:
        st.error("❌ У вас нет прав для управления пользователями")
        return
    
    # Создаем вкладки
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Список пользователей", 
        "➕ Создать пользователя", 
        "✏️ Управление пользователем",
        "🔐 Сброс паролей"
    ])
    
    with tab1:
        show_users_list()
    
    with tab2:
        show_create_user_form()
    
    with tab3:
        show_user_management()
    
    with tab4:
        show_password_reset()

def show_users_list():
    """Показать список всех пользователей"""
    st.subheader("📋 Список пользователей системы")
    
    users = get_all_users()
    
    if users:
        # Статистика
        total_users = len(users)
        owners = len([u for u in users if u[2] == 'owner'])
        admins = len([u for u in users if u[2] == 'admin'])
        crm_users = len([u for u in users if u[2] == 'crm'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Всего пользователей", total_users)
        with col2:
            st.metric("👑 Владельцы", owners)
        with col3:
            st.metric("👨‍💼 Администраторы", admins)
        with col4:
            st.metric("👥 CRM менеджеры", crm_users)
        
        st.markdown("---")
        
        # Таблица пользователей
        import pandas as pd
        
        df_data = []
        for user in users:
            df_data.append({
                "ID": user[0],
                "Имя пользователя": user[1],
                "Уровень доступа": get_access_level_display(user[2]),
                "Создан": user[3] if user[3] else "Неизвестно",
                "Последний вход": user[4] if user[4] else "Никогда"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
    else:
        st.info("💼 Пользователи не найдены")

def show_create_user_form():
    """Форма создания нового пользователя"""
    st.subheader("➕ Создать нового пользователя")
    
    # Кнопка генерации пароля (вне формы)
    col_gen, col_info = st.columns([1, 2])
    with col_gen:
        if st.button("🎲 Сгенерировать безопасный пароль", key="generate_password_btn"):
            generated_password = generate_secure_password()
            st.session_state['generated_password'] = generated_password
            st.success(f"Сгенерированный пароль: {generated_password}")
    
    with col_info:
        if 'generated_password' in st.session_state:
            st.info(f"💡 Используйте сгенерированный пароль: {st.session_state['generated_password']}")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "👤 Имя пользователя",
                placeholder="Введите имя пользователя",
                help="Уникальное имя для входа в систему"
            )
            
            name = st.text_input(
                "👤 Полное имя",
                placeholder="Введите полное имя пользователя",
                help="Отображаемое имя пользователя"
            )
            
            access_level = st.selectbox(
                "🔐 Уровень доступа",
                ["crm", "admin", "owner"],
                format_func=lambda x: get_access_level_display(x),
                help="Выберите уровень доступа для пользователя"
            )
        
        with col2:
            password = st.text_input(
                "🔑 Пароль",
                type="password",
                placeholder="Введите пароль",
                help="Минимум 8 символов"
            )
            
            confirm_password = st.text_input(
                "🔑 Подтвердите пароль",
                type="password",
                placeholder="Повторите пароль"
            )
        
        # Кнопка создания
        if st.form_submit_button("➕ Создать пользователя", use_container_width=True):
            if not username or not password:
                st.error("❌ Заполните все обязательные поля")
            elif password != confirm_password:
                st.error("❌ Пароли не совпадают")
            elif len(password) < 8:
                st.error("❌ Пароль должен содержать минимум 8 символов")
            else:
                success, message = create_user(username, password, access_level, name)
                
                if success:
                    # Логируем действие
                    log_audit_action(
                        st.session_state.get('user_id', 0),
                        'CREATE',
                        'user',
                        username,
                        f"Создан пользователь {username} с уровнем доступа {access_level}"
                    )
                    
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

def show_user_management():
    """Управление существующими пользователями"""
    st.subheader("✏️ Управление пользователем")
    
    users = get_all_users()
    
    if not users:
        st.info("💼 Пользователи не найдены")
        return
    
    # Выбор пользователя
    user_options = {f"{user[1]} ({get_access_level_display(user[2])})": user[1] for user in users}
    selected_user_display = st.selectbox(
        "👤 Выберите пользователя для управления",
        list(user_options.keys()),
        key="user_management_select"
    )
    
    if selected_user_display:
        selected_username = user_options[selected_user_display]
        
        # Получаем информацию о пользователе
        user_info = next((u for u in users if u[1] == selected_username), None)
        
        if user_info:
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**👤 Пользователь:** {user_info[1]}")
                st.write(f"**🔐 Уровень доступа:** {get_access_level_display(user_info[2])}")
                st.write(f"**📅 Создан:** {user_info[3] if user_info[3] else 'Неизвестно'}")
                st.write(f"**🕐 Последний вход:** {user_info[4] if user_info[4] else 'Никогда'}")
            
            with col2:
                # Форма изменения пароля
                st.subheader("🔑 Изменить пароль")
                with st.form("change_password_form"):
                    new_password = st.text_input(
                        "Новый пароль",
                        type="password",
                        key="new_password_input"
                    )
                    confirm_new_password = st.text_input(
                        "Подтвердите новый пароль",
                        type="password",
                        key="confirm_new_password_input"
                    )
                    
                    if st.form_submit_button("🔄 Обновить пароль"):
                        if new_password and confirm_new_password:
                            if new_password == confirm_new_password:
                                if len(new_password) >= 8:
                                    success, message = update_user_password(selected_username, new_password)
                                    if success:
                                        log_audit_action(
                                            st.session_state.get('user_id', 0),
                                            'UPDATE',
                                            'user_password',
                                            selected_username,
                                            f"Изменен пароль пользователя {selected_username}"
                                        )
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                else:
                                    st.error("❌ Пароль должен содержать минимум 8 символов")
                            else:
                                st.error("❌ Пароли не совпадают")
                        else:
                            st.error("❌ Заполните все поля")
                
                # Форма изменения уровня доступа
                st.subheader("🔐 Изменить уровень доступа")
                with st.form("change_access_form"):
                    current_level = user_info[2]
                    new_access_level = st.selectbox(
                        "Новый уровень доступа",
                        ["crm", "admin", "owner"],
                        index=["crm", "admin", "owner"].index(current_level),
                        format_func=lambda x: get_access_level_display(x),
                        key="new_access_level_select"
                    )
                    
                    if st.form_submit_button("🔄 Обновить уровень доступа"):
                        if new_access_level != current_level:
                            success, message = update_user_access_level(selected_username, new_access_level)
                            if success:
                                log_audit_action(
                                    st.session_state.get('user_id', 0),
                                    'UPDATE',
                                    'user_access_level',
                                    selected_username,
                                    f"Изменен уровень доступа пользователя {selected_username} с {current_level} на {new_access_level}"
                                )
                                st.success(f"✅ {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        else:
                            st.warning("⚠️ Выберите другой уровень доступа")
                
                # Удаление пользователя
                st.subheader("🗑️ Удалить пользователя")
                if st.button("🗑️ Удалить пользователя", type="secondary", key="delete_user_btn"):
                    if st.button("⚠️ Подтвердить удаление", type="primary", key="confirm_delete_btn"):
                        success, message = delete_user(selected_username)
                        if success:
                            log_audit_action(
                                st.session_state.get('user_id', 0),
                                'DELETE',
                                'user',
                                selected_username,
                                f"Удален пользователь {selected_username}"
                            )
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

def show_password_reset():
    """Сброс паролей пользователей"""
    st.subheader("🔐 Сброс паролей")
    
    users = get_all_users()
    
    if not users:
        st.info("💼 Пользователи не найдены")
        return
    
    st.info("💡 При сбросе пароля будет сгенерирован новый временный пароль")
    
    # Выбор пользователя для сброса
    user_options = {f"{user[1]} ({get_access_level_display(user[2])})": user[1] for user in users}
    selected_user_display = st.selectbox(
        "👤 Выберите пользователя для сброса пароля",
        list(user_options.keys()),
        key="password_reset_select"
    )
    
    if selected_user_display:
        selected_username = user_options[selected_user_display]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Сбросить пароль", type="primary", key="reset_password_btn"):
                success, message = reset_user_password(selected_username)
                if success:
                    log_audit_action(
                        st.session_state.get('user_id', 0),
                        'UPDATE',
                        'user_password_reset',
                        selected_username,
                        f"Сброшен пароль пользователя {selected_username}"
                    )
                    st.success(f"✅ {message}")
                    
                    # Показываем временный пароль
                    temp_password = message.split(": ")[-1]
                    st.warning(f"⚠️ **Временный пароль:** {temp_password}")
                    st.info("💡 Сохраните этот пароль! Пользователь должен сменить его при первом входе.")
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            if st.button("🎲 Сгенерировать новый пароль", key="generate_new_password_btn"):
                new_password = generate_secure_password()
                success, message = update_user_password(selected_username, new_password)
                if success:
                    log_audit_action(
                        st.session_state.get('user_id', 0),
                        'UPDATE',
                        'user_password',
                        selected_username,
                        f"Установлен новый пароль для пользователя {selected_username}"
                    )
                    st.success(f"✅ Пароль обновлен")
                    st.warning(f"⚠️ **Новый пароль:** {new_password}")
                else:
                    st.error(f"❌ {message}")

def get_access_level_display(level):
    """Получить отображаемое название уровня доступа"""
    levels = {
        'owner': '👑 Владелец',
        'admin': '👨‍💼 Администратор', 
        'crm': '👥 CRM менеджер'
    }
    return levels.get(level, level)

def generate_secure_password(length=12):
    """Генерировать безопасный пароль"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

if __name__ == "__main__":
    main()
