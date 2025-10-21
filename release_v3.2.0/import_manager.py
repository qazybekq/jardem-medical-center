#!/usr/bin/env python3
"""
Управление импортом данных из Excel
"""

import streamlit as st
import pandas as pd
import os
from database import get_connection, create_client, create_appointment

def main():
    """Главная функция управления импортом"""
    st.title("📥 Импорт данных")
    
    tab1, tab2, tab3 = st.tabs(["📤 Импорт", "📋 Шаблоны", "📖 Инструкция"])
    
    with tab1:
        show_import_data()
    
    with tab2:
        show_templates()
    
    with tab3:
        show_instructions()

def show_import_data():
    """Импорт данных"""
    st.subheader("📤 Импорт данных из Excel")
    
    import_type = st.radio(
        "Что вы хотите импортировать?",
        options=["Клиенты", "Врачи", "Услуги", "Приемы"],
        key="import_type"
    )
    
    uploaded_file = st.file_uploader(
        f"Загрузите Excel файл с данными ({import_type}):",
        type=['xlsx', 'xls'],
        key="import_file"
    )
    
    if uploaded_file is not None:
        try:
            # Читаем файл
            df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Файл загружен: {len(df)} записей")
            
            # Показываем превью
            st.subheader("📋 Превью данных")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            
            # Настройки импорта
            st.subheader("⚙️ Настройки импорта")
            
            col1, col2 = st.columns(2)
            
            with col1:
                skip_duplicates = st.checkbox(
                    "Пропускать дубликаты",
                    value=True,
                    key="skip_duplicates"
                )
            
            with col2:
                show_errors = st.checkbox(
                    "Показывать ошибки",
                    value=True,
                    key="show_errors"
                )
            
            st.markdown("---")
            
            # Кнопка импорта
            col1, col2, col3 = st.columns(3)
            
            with col2:
                if st.button("🚀 Начать импорт", type="primary", use_container_width=True):
                    import_data(df, import_type, skip_duplicates, show_errors)
        
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {e}")

def import_data(df, import_type, skip_duplicates, show_errors):
    """Импорт данных в базу"""
    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, row in df.iterrows():
        status_text.text(f"Импорт {i+1} из {len(df)}...")
        
        try:
            if import_type == "Клиенты":
                result = import_client(row, skip_duplicates)
            elif import_type == "Врачи":
                result = import_doctor(row, skip_duplicates)
            elif import_type == "Услуги":
                result = import_service(row, skip_duplicates)
            elif import_type == "Приемы":
                result = import_appointment(row, skip_duplicates)
            else:
                result = False
            
            if result == "skip":
                skip_count += 1
            elif result:
                success_count += 1
            else:
                error_count += 1
                errors.append((i+1, row.to_dict()))
        
        except Exception as e:
            error_count += 1
            errors.append((i+1, str(e)))
        
        progress_bar.progress((i + 1) / len(df))
    
    status_text.empty()
    progress_bar.empty()
    
    # Результаты
    st.markdown("---")
    st.subheader("📊 Результаты импорта")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Успешно", success_count)
    
    with col2:
        st.metric("⏭️ Пропущено", skip_count)
    
    with col3:
        st.metric("❌ Ошибок", error_count)
    
    if show_errors and errors:
        st.markdown("---")
        st.subheader("❌ Детали ошибок")
        
        for row_num, error_data in errors[:10]:  # Показываем первые 10
            st.error(f"Строка {row_num}: {error_data}")

def import_client(row, skip_duplicates):
    """Импорт клиента"""
    try:
        # Проверка обязательных полей
        if pd.isna(row.get('first_name')) or pd.isna(row.get('last_name')) or pd.isna(row.get('phone')):
            return False
        
        # Проверка дубликатов
        if skip_duplicates:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM clients WHERE phone = ?', (row['phone'],))
            if cursor.fetchone():
                conn.close()
                return "skip"
            conn.close()
        
        # Импорт
        client_id = create_client(
            row['first_name'],
            row['last_name'],
            row.get('birth_date'),
            row['phone'],
            row.get('email')
        )
        
        return client_id is not None
    
    except Exception:
        return False

def import_doctor(row, skip_duplicates):
    """Импорт врача"""
    st.info("⏳ Импорт врачей будет добавлен в следующей версии")
    return "skip"

def import_service(row, skip_duplicates):
    """Импорт услуги"""
    st.info("⏳ Импорт услуг будет добавлен в следующей версии")
    return "skip"

def import_appointment(row, skip_duplicates):
    """Импорт приема"""
    st.info("⏳ Импорт приемов будет добавлен в следующей версии")
    return "skip"

def show_templates():
    """Показать шаблоны для импорта"""
    st.subheader("📋 Шаблоны для импорта")
    
    st.info("""
    💡 **Используйте готовые шаблоны для импорта данных.**
    
    Шаблоны находятся в папке `excel_templates/`:
    - `1_clients_template.xlsx` - Клиенты
    - `2_doctors_template.xlsx` - Врачи
    - `3_services_template.xlsx` - Услуги
    - `4_appointments_template.xlsx` - Приемы
    """)
    
    st.markdown("---")
    
    # Показываем структуру таблиц
    st.subheader("📊 Структура таблиц")
    
    with st.expander("👥 Клиенты (Clients)"):
        st.code("""
Поля:
- first_name (обязательно) - Имя
- last_name (обязательно) - Фамилия
- birth_date - Дата рождения (YYYY-MM-DD)
- phone (обязательно, уникально) - Телефон (+7XXXXXXXXXX)
- email - Email
        """)
    
    with st.expander("👨‍⚕️ Врачи (Doctors)"):
        st.code("""
Поля:
- first_name (обязательно) - Имя
- last_name (обязательно) - Фамилия
- specialization - Специализация
- phone - Телефон
- email - Email
        """)
    
    with st.expander("🏥 Услуги (Services)"):
        st.code("""
Поля:
- name (обязательно) - Название
- description - Описание
- price (обязательно) - Цена (число)
- duration_minutes - Длительность в минутах
- doctor_id (обязательно) - ID врача
        """)
    
    with st.expander("📅 Приемы (Appointments)"):
        st.code("""
Поля:
- client_id (обязательно) - ID клиента
- doctor_id (обязательно) - ID врача
- service_id (обязательно) - ID услуги
- appointment_date (обязательно) - Дата (YYYY-MM-DD)
- appointment_time (обязательно) - Время (HH:MM:SS)
- status - Статус (записан/на приеме/прием завершен/не явился)
- notes - Заметки
        """)

def show_instructions():
    """Показать инструкцию"""
    st.subheader("📖 Инструкция по импорту")
    
    st.markdown("""
    ## Пошаговая инструкция
    
    ### Шаг 1: Подготовка файла
    1. Скачайте шаблон Excel из папки `excel_templates/`
    2. Заполните данные согласно структуре
    3. Убедитесь, что обязательные поля заполнены
    4. Проверьте формат данных (даты, телефоны)
    
    ### Шаг 2: Загрузка
    1. Перейдите на вкладку "Импорт"
    2. Выберите тип данных
    3. Загрузите Excel файл
    4. Проверьте превью данных
    
    ### Шаг 3: Настройки
    1. Выберите "Пропускать дубликаты" для избежания ошибок
    2. Включите "Показывать ошибки" для отладки
    
    ### Шаг 4: Импорт
    1. Нажмите кнопку "Начать импорт"
    2. Дождитесь завершения
    3. Проверьте результаты
    
    ## ⚠️ Важные примечания
    
    - **Телефоны** должны быть в формате: `+7XXXXXXXXXX`
    - **Даты** должны быть в формате: `YYYY-MM-DD`
    - **Email** должен быть валидным
    - **Дубликаты** определяются по телефону для клиентов
    
    ## 💡 Советы
    
    - Начните с небольшого файла для проверки
    - Проверяйте данные перед импортом
    - Создавайте резервную копию перед массовым импортом
    - Импортируйте данные в порядке: Врачи → Услуги → Клиенты → Приемы
    """)

if __name__ == "__main__":
    main()

