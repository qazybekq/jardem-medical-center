#!/usr/bin/env python3
"""
Аналитический дашборд для медицинского центра v2.2
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import get_connection

def main():
    """Главная функция аналитического дашборда"""
    st.title("📊 Аналитический дашборд")
    
    # Проверяем, если это режим "только сегодня" для CRM пользователей
    if st.session_state.get('analytics_today_only', False):
        st.info("📅 Доступна аналитика только за сегодняшний день")
        st.session_state['quick_filter_start'] = date.today()
        st.session_state['quick_filter_end'] = date.today()
        st.session_state['active_quick_filter'] = "today"
    
    # Быстрые фильтры (над основным контентом)
    st.markdown("### ⚡ Быстрые фильтры:")
    
    # Определяем активный фильтр
    active_filter = st.session_state.get('active_quick_filter', None)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📅 Сегодня", use_container_width=True, type="primary" if active_filter == "today" else "secondary"):
            st.session_state['quick_filter_start'] = date.today()
            st.session_state['quick_filter_end'] = date.today()
            st.session_state['active_quick_filter'] = "today"
            st.rerun()
    
    with col2:
        if st.button("📆 Неделя", use_container_width=True, type="primary" if active_filter == "week" else "secondary"):
            st.session_state['quick_filter_start'] = date.today() - timedelta(days=7)
            st.session_state['quick_filter_end'] = date.today()
            st.session_state['active_quick_filter'] = "week"
            st.rerun()
    
    with col3:
        if st.button("🗓️ Месяц", use_container_width=True, type="primary" if active_filter == "month" else "secondary"):
            st.session_state['quick_filter_start'] = date.today() - timedelta(days=30)
            st.session_state['quick_filter_end'] = date.today()
            st.session_state['active_quick_filter'] = "month"
            st.rerun()
    
    with col4:
        if st.button("📊 Квартал", use_container_width=True, type="primary" if active_filter == "quarter" else "secondary"):
            st.session_state['quick_filter_start'] = date.today() - timedelta(days=90)
            st.session_state['quick_filter_end'] = date.today()
            st.session_state['active_quick_filter'] = "quarter"
            st.rerun()
    
    with col5:
        if st.button("📈 Год", use_container_width=True, type="primary" if active_filter == "year" else "secondary"):
            st.session_state['quick_filter_start'] = date.today() - timedelta(days=365)
            st.session_state['quick_filter_end'] = date.today()
            st.session_state['active_quick_filter'] = "year"
            st.rerun()
    
    st.markdown("---")
    
    # Фильтры
    with st.sidebar:
        st.header("🔍 Фильтры")
        
        # Период (с учётом быстрых фильтров)
        default_start = st.session_state.get('quick_filter_start', date.today() - timedelta(days=30))
        default_end = st.session_state.get('quick_filter_end', date.today())
        
        date_range = st.date_input(
            "Выберите период:",
            value=(default_start, default_end),
            key="analytics_date_range"
        )
        
        # Врачи
        doctors = get_all_doctors_for_filter()
        selected_doctors = st.multiselect(
            "Выберите врачей:",
            options=[d[0] for d in doctors],
            default=[d[0] for d in doctors],
            format_func=lambda x: next((f"{d[1]} {d[2]}" for d in doctors if d[0] == x), x),
            key="analytics_doctors"
        )
    
    # Получаем данные
    if len(date_range) == 2:
        start_date, end_date = date_range
        df = get_analytics_data(start_date, end_date, selected_doctors)
        
        if df.empty:
            st.warning("📭 Нет данных за выбранный период")
            st.info("💡 Попробуйте выбрать другой период или врачей")
            return
        
        # KPI метрики
        show_kpi_metrics(df)
        
        st.markdown("---")
        
        # Графики
        col1, col2 = st.columns(2)
        
        with col1:
            show_appointments_by_status(df)
            show_appointments_by_doctor(df)
        
        with col2:
            show_revenue_by_doctor(df)
            show_appointments_timeline(df)
        
        st.markdown("---")
        
        # Новые графики v2.7
        col3, col4 = st.columns(2)
        
        with col3:
            show_patient_sources(df)
        
        with col4:
            show_payment_methods(df)
        
        st.markdown("---")
        
        # Детальная таблица
        show_detailed_table(df)
    else:
        st.info("Выберите период дат в боковой панели")

@st.cache_data(ttl=300)  # Кеш на 5 минут
def get_all_doctors_for_filter():
    """Получить всех врачей для фильтра"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, first_name, last_name
        FROM doctors
        WHERE is_active = 1
        ORDER BY last_name, first_name
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

@st.cache_data(ttl=60)  # Кеш на 1 минуту
def get_analytics_data(start_date, end_date, doctor_ids):
    """Получить данные для аналитики"""
    conn = get_connection()
    
    query = '''
        SELECT 
            a.id as appointment_id,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.actual_duration_minutes,
            c.first_name || ' ' || c.last_name as client_name,
            d.first_name || ' ' || d.last_name as doctor_name,
            d.specialization,
            s.name as service_name,
            s.price as service_price,
            (SELECT COALESCE(SUM(price), 0) FROM appointment_services WHERE appointment_id = a.id) as total_cost,
            a.source,
            (SELECT GROUP_CONCAT(DISTINCT asp.payment_method, ', ') 
             FROM appointment_services aps 
             LEFT JOIN appointment_service_payments asp ON aps.id = asp.appointment_service_id 
             WHERE aps.appointment_id = a.id) as payment_methods
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN services s ON a.service_id = s.id
        WHERE a.appointment_date BETWEEN ? AND ?
    '''
    
    params = [start_date, end_date]
    
    if doctor_ids:
        placeholders = ','.join(['?' for _ in doctor_ids])
        query += f' AND a.doctor_id IN ({placeholders})'
        params.extend(doctor_ids)
    
    query += ' ORDER BY a.appointment_date, a.appointment_time'
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def show_kpi_metrics(df):
    """Показать KPI метрики с сравнением периодов"""
    st.subheader("📈 Ключевые показатели")
    
    # Получаем данные для предыдущего периода
    if 'analytics_date_range' in st.session_state:
        current_start = st.session_state['analytics_date_range'][0]
        current_end = st.session_state['analytics_date_range'][1]
        period_length = (current_end - current_start).days
        
        # Вычисляем предыдущий период
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=period_length)
        
        # Получаем данные предыдущего периода
        df_previous = get_analytics_data(previous_start, previous_end, 
                                        st.session_state.get('analytics_doctors', []))
    else:
        df_previous = pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Всего приемов
    with col1:
        total_appointments = len(df)
        if not df_previous.empty:
            prev_appointments = len(df_previous)
            delta_appointments = total_appointments - prev_appointments
            delta_pct = (delta_appointments / prev_appointments * 100) if prev_appointments > 0 else 0
            st.metric("Всего приемов", total_appointments, 
                     delta=f"{delta_pct:+.1f}%", 
                     delta_color="normal")
        else:
            st.metric("Всего приемов", total_appointments)
    
    # Общая выручка
    with col2:
        total_revenue = df['total_cost'].sum()
        if not df_previous.empty:
            prev_revenue = df_previous['total_cost'].sum()
            delta_revenue = total_revenue - prev_revenue
            delta_pct = (delta_revenue / prev_revenue * 100) if prev_revenue > 0 else 0
            st.metric("Общая выручка", f"{total_revenue:,.0f} ₸", 
                     delta=f"{delta_pct:+.1f}%",
                     delta_color="normal")
        else:
            st.metric("Общая выручка", f"{total_revenue:,.0f} ₸")
    
    # Средний чек
    with col3:
        avg_check = df['total_cost'].mean()
        if not df_previous.empty:
            prev_avg_check = df_previous['total_cost'].mean()
            delta_check = avg_check - prev_avg_check
            delta_pct = (delta_check / prev_avg_check * 100) if prev_avg_check > 0 else 0
            st.metric("Средний чек", f"{avg_check:,.0f} ₸", 
                     delta=f"{delta_pct:+.1f}%",
                     delta_color="normal")
        else:
            st.metric("Средний чек", f"{avg_check:,.0f} ₸")
    
    # Завершенные приемы
    with col4:
        total_appointments = len(df)
        completed = len(df[df['status'] == 'прием завершен'])
        completion_rate = (completed / total_appointments * 100) if total_appointments > 0 else 0
        
        if not df_previous.empty:
            prev_total = len(df_previous)
            prev_completed = len(df_previous[df_previous['status'] == 'прием завершен'])
            prev_completion_rate = (prev_completed / prev_total * 100) if prev_total > 0 else 0
            delta_rate = completion_rate - prev_completion_rate
            st.metric("Завершено", f"{completed} ({completion_rate:.1f}%)", 
                     delta=f"{delta_rate:+.1f}%",
                     delta_color="normal")
        else:
            st.metric("Завершено", f"{completed} ({completion_rate:.1f}%)")

def show_appointments_by_status(df):
    """График приемов по статусам"""
    st.subheader("📊 Приемы по статусам")
    
    status_counts = df['status'].value_counts()
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Распределение по статусам",
        color_discrete_map={
            'записан': '#808080',
            'на приеме': '#FFD700',
            'прием завершен': '#00FF00',
            'не явился': '#FF00FF'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_appointments_by_doctor(df):
    """График приемов по врачам"""
    st.subheader("👨‍⚕️ Приемы по врачам")
    
    doctor_counts = df['doctor_name'].value_counts()
    
    fig = px.bar(
        x=doctor_counts.values,
        y=doctor_counts.index,
        orientation='h',
        title="Количество приемов",
        labels={'x': 'Количество', 'y': 'Врач'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_revenue_by_doctor(df):
    """График выручки по врачам"""
    st.subheader("💰 Выручка по врачам")
    
    revenue_by_doctor = df.groupby('doctor_name')['total_cost'].sum().sort_values(ascending=True)
    
    fig = px.bar(
        x=revenue_by_doctor.values,
        y=revenue_by_doctor.index,
        orientation='h',
        title="Выручка (KZT)",
        labels={'x': 'Выручка', 'y': 'Врач'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_appointments_timeline(df):
    """График динамики приемов"""
    st.subheader("📅 Динамика приемов")
    
    df['appointment_date'] = pd.to_datetime(df['appointment_date'])
    timeline = df.groupby('appointment_date').size().reset_index(name='count')
    
    fig = px.line(
        timeline,
        x='appointment_date',
        y='count',
        title="Количество приемов по дням",
        labels={'appointment_date': 'Дата', 'count': 'Количество'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_detailed_table(df):
    """Показать детальную таблицу"""
    st.subheader("📋 Детальная информация")
    
    # Форматируем данные для отображения
    display_df = df[[
        'appointment_date', 'appointment_time', 'client_name',
        'doctor_name', 'service_name', 'total_cost', 'status', 'source', 'payment_methods'
    ]].copy()
    
    display_df.columns = [
        'Дата', 'Время', 'Пациент', 'Врач', 'Услуга', 'Стоимость', 'Статус', 'Источник', 'Методы оплаты'
    ]
    
    # Сортируем по дате
    display_df = display_df.sort_values('Дата', ascending=False)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Статистика
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Всего записей:** {len(display_df)}")
    
    with col2:
        total = display_df['Стоимость'].sum()
        st.info(f"**Общая сумма:** {total:,.0f} KZT")
    
    with col3:
        avg = display_df['Стоимость'].mean()
        st.info(f"**Средний чек:** {avg:,.0f} KZT")

def show_patient_sources(df):
    """Показать график источников пациентов (v2.7)"""
    st.subheader("🌐 Источники пациентов")
    
    if 'source' not in df.columns or df['source'].isna().all():
        st.info("📊 Данные об источниках пациентов отсутствуют")
        return
    
    # Подсчитываем количество приемов по источникам
    source_counts = df['source'].value_counts().reset_index()
    source_counts.columns = ['Источник', 'Количество']
    
    # Создаем круговую диаграмму
    fig = px.pie(
        source_counts,
        values='Количество',
        names='Источник',
        title='Распределение источников пациентов',
        hole=0.4,  # Делаем donut chart
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Приемов: %{value}<br>Доля: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        height=400,
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Таблица со статистикой
    st.markdown("**Детальная статистика:**")
    
    # Добавляем процент и выручку
    source_stats = df.groupby('source').agg({
        'appointment_id': 'count',
        'total_cost': 'sum'
    }).reset_index()
    
    source_stats.columns = ['Источник', 'Количество приемов', 'Общая выручка']
    source_stats['Процент'] = (source_stats['Количество приемов'] / source_stats['Количество приемов'].sum() * 100).round(1)
    source_stats['Средний чек'] = (source_stats['Общая выручка'] / source_stats['Количество приемов']).round(0)
    
    # Сортируем по количеству приемов
    source_stats = source_stats.sort_values('Количество приемов', ascending=False)
    
    # Форматируем числа
    source_stats['Общая выручка'] = source_stats['Общая выручка'].apply(lambda x: f"{x:,.0f} ₸")
    source_stats['Средний чек'] = source_stats['Средний чек'].apply(lambda x: f"{x:,.0f} ₸")
    source_stats['Процент'] = source_stats['Процент'].apply(lambda x: f"{x}%")
    
    st.dataframe(
        source_stats,
        use_container_width=True,
        hide_index=True
    )
    
    # Ключевые выводы
    if not source_stats.empty:
        top_source = source_stats.iloc[0]['Источник']
        top_count = source_stats.iloc[0]['Количество приемов']
        st.success(f"🏆 **Лучший источник:** {top_source} ({top_count} приемов)")

def show_payment_methods(df):
    """Показать график методов оплаты (v2.7)"""
    st.subheader("💳 Методы оплаты")
    
    # Получаем данные по оплатам из БД
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем ID приемов из текущего фильтра
    appointment_ids = tuple(df['appointment_id'].unique().tolist())
    
    if not appointment_ids:
        st.info("📊 Нет данных по оплатам")
        return
    
    # Запрос для получения оплат
    placeholders = ','.join(['?' for _ in appointment_ids])
    query = f'''
        SELECT 
            asp.payment_method,
            SUM(asp.amount) as total_amount,
            COUNT(DISTINCT asrv.appointment_id) as appointment_count
        FROM appointment_service_payments asp
        JOIN appointment_services asrv ON asp.appointment_service_id = asrv.id
        WHERE asrv.appointment_id IN ({placeholders})
        GROUP BY asp.payment_method
        ORDER BY total_amount DESC
    '''
    
    cursor.execute(query, appointment_ids)
    payment_data = cursor.fetchall()
    conn.close()
    
    if not payment_data:
        st.info("📊 Нет данных по оплатам за выбранный период")
        return
    
    # Создаем DataFrame
    payment_df = pd.DataFrame(payment_data, columns=['Метод оплаты', 'Сумма', 'Количество приемов'])
    
    # Круговая диаграмма
    fig = px.pie(
        payment_df,
        values='Сумма',
        names='Метод оплаты',
        title='Распределение оплат по методам',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Сумма: %{value:,.0f} ₸<br>Доля: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        height=400,
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Таблица со статистикой
    st.markdown("**Детальная статистика:**")
    
    # Добавляем процент
    payment_df['Процент'] = (payment_df['Сумма'] / payment_df['Сумма'].sum() * 100).round(1)
    payment_df['Средний чек'] = (payment_df['Сумма'] / payment_df['Количество приемов']).round(0)
    
    # Форматируем
    display_df = payment_df.copy()
    display_df['Сумма'] = display_df['Сумма'].apply(lambda x: f"{x:,.0f} ₸")
    display_df['Средний чек'] = display_df['Средний чек'].apply(lambda x: f"{x:,.0f} ₸")
    display_df['Процент'] = display_df['Процент'].apply(lambda x: f"{x}%")
    
    # Иконки для методов оплаты
    method_icons = {
        "Карта": "💳",
        "Наличные": "💵",
        "Kaspi QR": "📱",
        "Перевод": "💸"
    }
    
    display_df['Метод оплаты'] = display_df['Метод оплаты'].apply(
        lambda x: f"{method_icons.get(x, '💰')} {x}"
    )
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Ключевые выводы
    if not payment_df.empty:
        top_method = payment_data[0][0]
        top_amount = payment_data[0][1]
        top_icon = method_icons.get(top_method, '💰')
        st.success(f"{top_icon} **Популярный метод:** {top_method} ({top_amount:,.0f} ₸)")

if __name__ == "__main__":
    main()

