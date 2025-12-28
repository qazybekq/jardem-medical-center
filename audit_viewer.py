#!/usr/bin/env python3
"""
Просмотр аудита действий пользователей
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_connection

def main():
    """Главная функция просмотра аудита"""
    st.title("📋 Аудит действий пользователей")
    
    # Фильтры
    with st.sidebar:
        st.header("🔍 Фильтры")
        
        # Период
        try:
            from timezone_utils import get_local_today
            today = get_local_today()
        except ImportError:
            today = date.today()
        
        date_range = st.date_input(
            "Выберите период:",
            value=(today - timedelta(days=7), today),
            key="audit_date_range"
        )
        
        # Пользователи
        users = get_all_users()
        selected_users = st.multiselect(
            "Выберите пользователей:",
            options=[u[0] for u in users],
            default=[u[0] for u in users],
            format_func=lambda x: next((u[1] for u in users if u[0] == x), x),
            key="audit_users"
        )
        
        # Действия
        actions = ['LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE']
        selected_actions = st.multiselect(
            "Выберите действия:",
            options=actions,
            default=actions,
            key="audit_actions"
        )
    
    # Получаем данные
    if len(date_range) == 2:
        start_date, end_date = date_range
        df = get_audit_data(start_date, end_date, selected_users, selected_actions)
        
        if df.empty:
            st.warning("📭 Нет данных за выбранный период")
            return
        
        # Статистика
        show_audit_statistics(df)
        
        st.markdown("---")
        
        # Таблица событий
        show_audit_table(df)
        
    else:
        st.info("Выберите период дат в боковой панели")

def get_all_users():
    """Получить всех пользователей"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, username
        FROM users
        ORDER BY name
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_audit_data(start_date, end_date, user_ids, actions):
    """Получить данные аудита"""
    conn = get_connection()
    
    # Конвертируем даты в datetime для сравнения
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    query = '''
        SELECT 
            al.id,
            al.timestamp,
            al.action,
            al.table_name,
            al.record_id,
            al.old_values,
            al.new_values,
            u.name as user_name,
            u.username
        FROM audit_log al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE DATE(al.timestamp) BETWEEN DATE(?) AND DATE(?)
    '''
    
    params = [start_date, end_date]
    
    if user_ids:
        placeholders = ','.join(['?' for _ in user_ids])
        query += f' AND al.user_id IN ({placeholders})'
        params.extend(user_ids)
    
    if actions:
        placeholders = ','.join(['?' for _ in actions])
        query += f' AND al.action IN ({placeholders})'
        params.extend(actions)
    
    query += ' ORDER BY al.timestamp DESC'
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def show_audit_statistics(df):
    """Показать статистику аудита"""
    st.subheader("📊 Статистика активности")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Всего событий
    with col1:
        total_events = len(df)
        st.metric("Всего событий", total_events)
    
    # Уникальные пользователи
    with col2:
        unique_users = df['user_name'].nunique()
        st.metric("Активных пользователей", unique_users)
    
    # Создано записей
    with col3:
        created = len(df[df['action'] == 'CREATE'])
        st.metric("Создано", created)
    
    # Удалено записей
    with col4:
        deleted = len(df[df['action'] == 'DELETE'])
        st.metric("Удалено", deleted)
    
    # Графики активности
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # График по действиям
        st.subheader("📈 По типу действий")
        action_counts = df['action'].value_counts()
        st.bar_chart(action_counts)
    
    with col_chart2:
        # График по пользователям
        st.subheader("👥 По пользователям")
        user_counts = df['user_name'].value_counts()
        st.bar_chart(user_counts)

def show_audit_table(df):
    """Показать таблицу аудита"""
    st.subheader("📋 Журнал действий")
    
    # Форматируем данные для отображения
    display_df = df[[
        'timestamp', 'user_name', 'action', 'table_name', 'record_id'
    ]].copy()
    
    display_df.columns = [
        'Время', 'Пользователь', 'Действие', 'Таблица', 'ID записи'
    ]
    
    # Раскраска действий
    def highlight_action(row):
        action = row['Действие']
        if action == 'CREATE':
            return ['background-color: #d4edda'] * len(row)
        elif action == 'DELETE':
            return ['background-color: #f8d7da'] * len(row)
        elif action == 'UPDATE':
            return ['background-color: #fff3cd'] * len(row)
        elif action == 'LOGIN':
            return ['background-color: #d1ecf1'] * len(row)
        else:
            return [''] * len(row)
    
    # Показываем с пагинацией
    items_per_page = 50
    total_pages = (len(display_df) - 1) // items_per_page + 1
    
    page = st.number_input(
        "Страница",
        min_value=1,
        max_value=total_pages,
        value=1,
        key="audit_page"
    )
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    st.dataframe(
        display_df.iloc[start_idx:end_idx].style.apply(highlight_action, axis=1),
        use_container_width=True,
        hide_index=True
    )
    
    st.info(f"Показано {start_idx + 1}-{min(end_idx, len(display_df))} из {len(display_df)} записей")
    
    # Детали выбранной записи
    st.markdown("---")
    st.subheader("🔍 Детали события")
    
    selected_id = st.number_input(
        "Введите ID события для просмотра деталей:",
        min_value=1,
        max_value=len(df),
        value=1,
        key="audit_detail_id"
    )
    
    if selected_id and selected_id <= len(df):
        event = df.iloc[selected_id - 1]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Время:**", event['timestamp'])
            st.write("**Пользователь:**", event['user_name'])
            st.write("**Действие:**", event['action'])
        
        with col2:
            st.write("**Таблица:**", event['table_name'])
            st.write("**ID записи:**", event['record_id'])
        
        if pd.notna(event['old_values']) and event['old_values']:
            st.write("**Старые значения:**")
            st.code(event['old_values'], language='json')
        
        if pd.notna(event['new_values']) and event['new_values']:
            st.write("**Новые значения:**")
            st.code(event['new_values'], language='json')

if __name__ == "__main__":
    main()

