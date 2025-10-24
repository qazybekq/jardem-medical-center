#!/usr/bin/env python3
"""
Модуль управления справочниками медицинского центра v3.0
Реализует CRUD операции для клиентов, услуг и врачей
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_connection, log_audit_action
from auth import check_access

def main():
    """Главная функция модуля справочников"""

    # Проверка прав доступа
    if not check_access(['owner', 'admin']):
        st.error("❌ У вас нет прав доступа к управлению справочниками")
        return

    st.title("📚 Управление справочниками")
    st.markdown("---")

    # Подменю для справочников
    tab1, tab2, tab3 = st.tabs(["👥 Пациенты", "💼 Услуги", "👨‍⚕️ Врачи"])

    with tab1:
        show_clients_management()

    with tab2:
        show_services_management()

    with tab3:
        show_doctors_management()

def show_clients_management():
    """Управление клиентами (пациентами)"""

    st.header("👥 Управление клиентами")

    # Кнопка добавления нового клиента
    if st.button("➕ Добавить клиента", type="primary"):
        st.session_state['show_client_form'] = True
        st.session_state['edit_client_id'] = None

    # Показать форму добавления/редактирования если нужно
    if st.session_state.get('show_client_form'):
        client_id = st.session_state.get('edit_client_id')
        show_client_form(is_edit=client_id is not None, client_id=client_id)

    # Показать таблицу клиентов
    show_clients_table()

def show_client_form(is_edit=False, client_id=None):
    """Форма добавления/редактирования клиента"""

    if is_edit:
        st.subheader("✏️ Редактирование клиента")
    else:
        st.subheader("➕ Добавление клиента")

    # Загрузка данных для редактирования
    client_data = None
    if is_edit and client_id:
        client_data = get_client_by_id(client_id)

    with st.form("client_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input(
                "Имя *",
                value=client_data[1] if client_data else "",
                help="Обязательное поле"
            )

            phone = st.text_input(
                "Телефон *",
                value=client_data[4] if client_data else "",
                help="Введите номер без +7 (например: 7011234567)"
            )

        with col2:
            last_name = st.text_input(
                "Фамилия",
                value=client_data[2] if client_data else "",
                help="Необязательное поле"
            )

            birth_date = st.date_input(
                "Дата рождения",
                value=datetime.strptime(client_data[3], '%Y-%m-%d').date() if client_data and client_data[3] else None,
                min_value=datetime(1910, 1, 1).date(),
                max_value=datetime(2025, 12, 31).date(),
                help="Выберите дату рождения (1910-2025)"
            )

        email = st.text_input(
            "Email",
            value=client_data[5] if client_data else "",
            help="Необязательное поле"
        )

        # Кнопки формы
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.form_submit_button("💾 Сохранить", type="primary"):
                # Валидация
                if not first_name.strip():
                    st.error("❌ Имя обязательно для заполнения")
                    return

                if not phone.strip():
                    st.error("❌ Телефон обязателен для заполнения")
                    return

                # Сохранение
                if is_edit:
                    success = update_client(client_id, first_name, last_name, birth_date, phone, email)
                else:
                    success = add_client(first_name, last_name, birth_date, phone, email)

                if success:
                    st.success("✅ Пациент успешно сохранен!")
                    st.session_state['show_client_form'] = False
                    st.rerun()
                else:
                    st.error("❌ Ошибка при сохранении клиента")

        with col2:
            if st.form_submit_button("❌ Отмена"):
                st.session_state['show_client_form'] = False
                st.session_state['edit_client_id'] = None
                st.rerun()

def show_clients_table():
    """Таблица клиентов с поиском и действиями"""

    # Поиск
    search_query = st.text_input("🔍 Поиск клиентов", placeholder="Введите имя, фамилию или телефон...")

    # Фильтры
    col1, col2 = st.columns(2)

    with col1:
        show_active_only = st.checkbox("Показывать только активных", value=True, key="clients_active_only")

    with col2:
        # Заглушка для будущих фильтров
        st.write("")

    # Получение данных
    clients = get_clients(search_query, show_active_only)

    if clients:
        # Статистика
        total_clients = len(clients)
        active_clients = len([c for c in clients if c[6]])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Всего клиентов", total_clients)
        with col2:
            st.metric("Активных клиентов", active_clients)

        # Таблица
        st.subheader("📋 Список клиентов")

        # Преобразование данных для отображения
        display_data = []
        for client in clients:
            status = "✅ Активен" if client[6] else "❌ Деактивирован"
            display_data.append({
                "ID": client[0],
                "Имя": client[1],
                "Фамилия": client[2] or "-",
                "Телефон": client[4],
                "Email": client[5] or "-",
                "Дата рождения": client[3] or "-",
                "Статус": status,
                "Создан": client[7] if isinstance(client[7], str) else client[7].strftime("%d.%m.%Y")
            })

        df = pd.DataFrame(display_data)

        # Показать таблицу
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", format="%d"),
                "Имя": st.column_config.TextColumn("Имя"),
                "Фамилия": st.column_config.TextColumn("Фамилия"),
                "Телефон": st.column_config.TextColumn("Телефон"),
                "Email": st.column_config.TextColumn("Email"),
                "Дата рождения": st.column_config.TextColumn("Дата рождения"),
                "Статус": st.column_config.TextColumn("Статус"),
                "Создан": st.column_config.TextColumn("Создан")
            }
        )

        # Действия с клиентами
        st.subheader("⚙️ Действия")

        selected_client_ids = st.multiselect(
            "Выберите клиентов для действий:",
            options=[c[0] for c in clients],
            format_func=lambda x: next(f"{c[1]} {c[2] or ''}".strip() for c in clients if c[0] == x)
        )

        if selected_client_ids:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Редактировать выбранных", key="edit_clients_btn"):
                    if len(selected_client_ids) == 1:
                        st.session_state['edit_client_id'] = selected_client_ids[0]
                        st.session_state['show_client_form'] = True
                        st.rerun()
                    else:
                        st.warning("Выберите только одного клиента для редактирования")

            with col2:
                if st.button("🗑️ Деактивировать выбранных", type="secondary", key="deactivate_clients_btn"):
                    if st.button("Подтвердить деактивацию", type="primary", key="confirm_deactivate_clients_btn"):
                        for client_id in selected_client_ids:
                            deactivate_client(client_id)
                        st.success(f"✅ Деактивировано клиентов: {len(selected_client_ids)}")
                        st.rerun()
    else:
        st.info("👤 Пациентов не найдено")

def show_services_management():
    """Управление услугами"""

    st.header("💼 Управление услугами")

    # Кнопка добавления новой услуги
    if st.button("➕ Добавить услугу", type="primary"):
        st.session_state['show_service_form'] = True
        st.session_state['edit_service_id'] = None

    # Показать форму добавления/редактирования если нужно
    if st.session_state.get('show_service_form'):
        service_id = st.session_state.get('edit_service_id')
        show_service_form(is_edit=service_id is not None, service_id=service_id)

    # Показать таблицу услуг
    show_services_table()

def show_service_form(is_edit=False, service_id=None):
    """Форма добавления/редактирования услуги"""

    if is_edit:
        st.subheader("✏️ Редактирование услуги")
    else:
        st.subheader("➕ Добавление услуги")

    # Загрузка данных для редактирования
    service_data = None
    if is_edit and service_id:
        service_data = get_service_by_id(service_id)

    # Получение списка активных врачей
    doctors = get_active_doctors()

    with st.form("service_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Название услуги *",
                value=service_data[1] if service_data else "",
                help="Обязательное поле"
            )

            doctor_id = st.selectbox(
                "Врач *",
                options=[d[0] for d in doctors],
                format_func=lambda x: next(f"{d[1]} {d[2]}" for d in doctors if d[0] == x),
                index=0 if not service_data else next(i for i, d in enumerate(doctors) if d[0] == service_data[3])
            )

        with col2:
            price = st.number_input(
                "Цена *",
                value=float(service_data[4]) if service_data else 0.0,
                min_value=0.0,
                step=100.0,
                help="Обязательное поле"
            )

            duration = st.number_input(
                "Длительность (мин) *",
                value=service_data[5] if service_data else 30,
                min_value=5,
                max_value=480,
                step=5,
                help="Обязательное поле"
            )

        description = st.text_area(
            "Описание",
            value=service_data[2] if service_data else "",
            help="Необязательное поле"
        )

        # Кнопки формы
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.form_submit_button("💾 Сохранить", type="primary"):
                # Валидация
                if not name.strip():
                    st.error("❌ Название обязательно для заполнения")
                    return

                if price <= 0:
                    st.error("❌ Цена должна быть больше нуля")
                    return

                if duration <= 0:
                    st.error("❌ Длительность должна быть больше нуля")
                    return

                # Сохранение
                if is_edit:
                    success = update_service(service_id, name, description, doctor_id, price, duration)
                else:
                    success = add_service(name, description, doctor_id, price, duration)

                if success:
                    st.success("✅ Услуга успешно сохранена!")
                    st.session_state['show_service_form'] = False
                    st.rerun()
                else:
                    st.error("❌ Ошибка при сохранении услуги")

        with col2:
            if st.form_submit_button("❌ Отмена"):
                st.session_state['show_service_form'] = False
                st.session_state['edit_service_id'] = None
                st.rerun()

def show_services_table():
    """Таблица услуг с поиском и действиями"""

    # Поиск
    search_query = st.text_input("🔍 Поиск услуг", placeholder="Введите название услуги...")

    # Фильтры
    col1, col2 = st.columns(2)

    with col1:
        selected_doctor = st.selectbox(
            "Фильтр по врачу",
            options=["Все"] + [f"{d[1]} {d[2]}" for d in get_active_doctors()],
            index=0
        )

    with col2:
        show_active_only = st.checkbox("Показывать только активные", value=True, key="services_active_only")

    # Получение данных
    services = get_services(search_query, selected_doctor, show_active_only)

    if services:
        # Статистика
        total_services = len(services)
        active_services = len([s for s in services if s[6]])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Всего услуг", total_services)
        with col2:
            st.metric("Активных услуг", active_services)

        # Таблица
        st.subheader("📋 Список услуг")

        # Преобразование данных для отображения
        display_data = []
        for service in services:
            status = "✅ Активна" if service[6] else "❌ Деактивирована"
            display_data.append({
                "ID": service[0],
                "Название": service[1],
                "Описание": service[2] or "-",
                "Врач": f"{service[7]} {service[8]}",
                "Цена": f"{service[4]:,.0f} ₸",
                "Длительность": f"{service[5]} мин",
                "Статус": status,
                "Создано": service[9] if isinstance(service[9], str) else service[9].strftime("%d.%m.%Y")
            })

        df = pd.DataFrame(display_data)

        # Показать таблицу
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", format="%d"),
                "Название": st.column_config.TextColumn("Название"),
                "Описание": st.column_config.TextColumn("Описание"),
                "Врач": st.column_config.TextColumn("Врач"),
                "Цена": st.column_config.TextColumn("Цена"),
                "Длительность": st.column_config.TextColumn("Длительность"),
                "Статус": st.column_config.TextColumn("Статус"),
                "Создано": st.column_config.TextColumn("Создано")
            }
        )

        # Действия с услугами
        st.subheader("⚙️ Действия")

        selected_service_ids = st.multiselect(
            "Выберите услуги для действий:",
            options=[s[0] for s in services],
            format_func=lambda x: next(s[1] for s in services if s[0] == x)
        )

        if selected_service_ids:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Редактировать выбранные", key="edit_services_btn"):
                    if len(selected_service_ids) == 1:
                        st.session_state['edit_service_id'] = selected_service_ids[0]
                        st.session_state['show_service_form'] = True
                        st.rerun()
                    else:
                        st.warning("Выберите только одну услугу для редактирования")

            with col2:
                if st.button("🗑️ Деактивировать выбранные", type="secondary", key="deactivate_services_btn"):
                    if st.button("Подтвердить деактивацию", type="primary", key="confirm_deactivate_services_btn"):
                        for service_id in selected_service_ids:
                            deactivate_service(service_id)
                        st.success(f"✅ Деактивировано услуг: {len(selected_service_ids)}")
                        st.rerun()
    else:
        st.info("💼 Услуг не найдено")

def show_doctors_management():
    """Управление врачами"""

    st.header("👨‍⚕️ Управление врачами")

    # Кнопка добавления нового врача
    if st.button("➕ Добавить врача", type="primary"):
        st.session_state['show_doctor_form'] = True
        st.session_state['edit_doctor_id'] = None

    # Показать форму добавления/редактирования если нужно
    if st.session_state.get('show_doctor_form'):
        doctor_id = st.session_state.get('edit_doctor_id')
        show_doctor_form(is_edit=doctor_id is not None, doctor_id=doctor_id)

    # Показать таблицу врачей
    show_doctors_table()

def show_doctor_form(is_edit=False, doctor_id=None):
    """Форма добавления/редактирования врача"""

    if is_edit:
        st.subheader("✏️ Редактирование врача")
    else:
        st.subheader("➕ Добавление врача")

    # Загрузка данных для редактирования
    doctor_data = None
    if is_edit and doctor_id:
        doctor_data = get_doctor_by_id(doctor_id)

    # Специализации
    specializations = [
        "Терапевт", "Кардиолог", "Невролог", "Гинеколог", "Педиатр",
        "Офтальмолог", "Отоларинголог", "Дерматолог", "Хирург", "Психолог"
    ]

    with st.form("doctor_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input(
                "Имя *",
                value=doctor_data[1] if doctor_data else "",
                help="Обязательное поле"
            )

            specialization = st.selectbox(
                "Специализация *",
                options=specializations,
                index=specializations.index(doctor_data[3]) if doctor_data else 0
            )

        with col2:
            last_name = st.text_input(
                "Фамилия *",
                value=doctor_data[2] if doctor_data else "",
                help="Обязательное поле"
            )

            phone = st.text_input(
                "Телефон *",
                value=doctor_data[4] if doctor_data else "",
                help="Введите номер без +7 (например: 7011234567)"
            )

        email = st.text_input(
            "Email",
            value=doctor_data[5] if doctor_data else "",
            help="Необязательное поле"
        )

        # Кнопки формы
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.form_submit_button("💾 Сохранить", type="primary"):
                # Валидация
                if not first_name.strip():
                    st.error("❌ Имя обязательно для заполнения")
                    return

                if not last_name.strip():
                    st.error("❌ Фамилия обязательна для заполнения")
                    return

                if not phone.strip():
                    st.error("❌ Телефон обязателен для заполнения")
                    return

                # Сохранение
                if is_edit:
                    success = update_doctor(doctor_id, first_name, last_name, specialization, phone, email)
                else:
                    success = add_doctor(first_name, last_name, specialization, phone, email)

                if success:
                    st.success("✅ Врач успешно сохранен!")
                    st.session_state['show_doctor_form'] = False
                    st.rerun()
                else:
                    st.error("❌ Ошибка при сохранении врача")

        with col2:
            if st.form_submit_button("❌ Отмена"):
                st.session_state['show_doctor_form'] = False
                st.session_state['edit_doctor_id'] = None
                st.rerun()

def show_doctors_table():
    """Таблица врачей с поиском и действиями"""

    # Поиск
    search_query = st.text_input("🔍 Поиск врачей", placeholder="Введите имя, фамилию или специализацию...")

    # Фильтры
    col1, col2 = st.columns(2)

    with col1:
        selected_specialization = st.selectbox(
            "Фильтр по специализации",
            options=["Все"] + [
                "Терапевт", "Кардиолог", "Невролог", "Гинеколог", "Педиатр",
                "Офтальмолог", "Отоларинголог", "Дерматолог", "Хирург", "Психолог"
            ],
            index=0
        )

    with col2:
        show_active_only = st.checkbox("Показывать только активных", value=True, key="doctors_active_only")

    # Получение данных
    doctors = get_doctors(search_query, selected_specialization, show_active_only)

    if doctors:
        # Статистика
        total_doctors = len(doctors)
        active_doctors = len([d for d in doctors if d[6]])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Всего врачей", total_doctors)
        with col2:
            st.metric("Активных врачей", active_doctors)

        # Таблица
        st.subheader("📋 Список врачей")

        # Преобразование данных для отображения
        display_data = []
        for doctor in doctors:
            status = "✅ Активен" if doctor[6] else "❌ Деактивирован"
            display_data.append({
                "ID": doctor[0],
                "Имя": doctor[1],
                "Фамилия": doctor[2],
                "Специализация": doctor[3],
                "Телефон": doctor[4],
                "Email": doctor[5] or "-",
                "Статус": status,
                "Создан": doctor[7] if isinstance(doctor[7], str) else doctor[7].strftime("%d.%m.%Y")
            })

        df = pd.DataFrame(display_data)

        # Показать таблицу
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", format="%d"),
                "Имя": st.column_config.TextColumn("Имя"),
                "Фамилия": st.column_config.TextColumn("Фамилия"),
                "Специализация": st.column_config.TextColumn("Специализация"),
                "Телефон": st.column_config.TextColumn("Телефон"),
                "Email": st.column_config.TextColumn("Email"),
                "Статус": st.column_config.TextColumn("Статус"),
                "Создан": st.column_config.TextColumn("Создан")
            }
        )

        # Действия с врачами
        st.subheader("⚙️ Действия")

        selected_doctor_ids = st.multiselect(
            "Выберите врачей для действий:",
            options=[d[0] for d in doctors],
            format_func=lambda x: next(f"{d[1]} {d[2]} ({d[3]})" for d in doctors if d[0] == x)
        )

        if selected_doctor_ids:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Редактировать выбранных", key="edit_doctors_btn"):
                    if len(selected_doctor_ids) == 1:
                        st.session_state['edit_doctor_id'] = selected_doctor_ids[0]
                        st.session_state['show_doctor_form'] = True
                        st.rerun()
                    else:
                        st.warning("Выберите только одного врача для редактирования")

            with col2:
                if st.button("🗑️ Деактивировать выбранных", type="secondary", key="deactivate_doctors_btn"):
                    if st.button("Подтвердить деактивацию", type="primary", key="confirm_deactivate_doctors_btn"):
                        for doctor_id in selected_doctor_ids:
                            deactivate_doctor(doctor_id)
                        st.success(f"✅ Деактивировано врачей: {len(selected_doctor_ids)}")
                        st.rerun()
    else:
        st.info("👨‍⚕️ Врачей не найдено")

# Функции базы данных (заглушки для начала)

def get_clients(search_query=None, show_active_only=True):
    """Получить список клиентов"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, first_name, last_name, birth_date, phone, email, is_active, created_at
        FROM clients
        WHERE 1=1
    """

    params = []

    if search_query:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?)"
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    if show_active_only:
        query += " AND is_active = 1"

    query += " ORDER BY first_name, last_name"

    cursor.execute(query, params)
    clients = cursor.fetchall()
    conn.close()

    return clients

def get_client_by_id(client_id):
    """Получить клиента по ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, first_name, last_name, birth_date, phone, email, is_active, created_at
        FROM clients WHERE id = ?
    """, (client_id,))

    client = cursor.fetchone()
    conn.close()

    return client

def add_client(first_name, last_name, birth_date, phone, email):
    """Добавить нового клиента"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clients (first_name, last_name, birth_date, phone, email)
            VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, birth_date, phone, email))

        client_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'CREATE', 'clients', client_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при добавлении клиента: {e}")
        return False

def update_client(client_id, first_name, last_name, birth_date, phone, email):
    """Обновить данные клиента"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE clients
            SET first_name = ?, last_name = ?, birth_date = ?, phone = ?, email = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (first_name, last_name, birth_date, phone, email, client_id))

        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'UPDATE', 'clients', client_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при обновлении клиента: {e}")
        return False

def deactivate_client(client_id):
    """Деактивировать клиента"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE clients SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (client_id,))

        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'UPDATE', 'clients', client_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при деактивации клиента: {e}")
        return False

def get_active_doctors():
    """Получить список активных врачей"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, first_name, last_name FROM doctors WHERE is_active = 1 ORDER BY first_name, last_name
    """)

    doctors = cursor.fetchall()
    conn.close()

    return doctors

def get_services(search_query=None, doctor_filter="Все", show_active_only=True):
    """Получить список услуг"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT s.id, s.name, s.description, s.doctor_id, s.price, s.duration_minutes, s.is_active, s.created_at,
               d.first_name, d.last_name
        FROM services s
        JOIN doctors d ON s.doctor_id = d.id
        WHERE 1=1
    """

    params = []

    if search_query:
        query += " AND s.name LIKE ?"
        params.append(f"%{search_query}%")

    if doctor_filter != "Все":
        query += " AND (d.first_name || ' ' || d.last_name) = ?"
        params.append(doctor_filter)

    if show_active_only:
        query += " AND s.is_active = 1"

    query += " ORDER BY s.name"

    cursor.execute(query, params)
    services = cursor.fetchall()
    conn.close()

    return services

def get_service_by_id(service_id):
    """Получить услугу по ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.name, s.description, s.doctor_id, s.price, s.duration_minutes, s.is_active, s.created_at,
               d.first_name, d.last_name
        FROM services s
        JOIN doctors d ON s.doctor_id = d.id
        WHERE s.id = ?
    """, (service_id,))

    service = cursor.fetchone()
    conn.close()

    return service

def add_service(name, description, doctor_id, price, duration):
    """Добавить новую услугу"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO services (name, description, doctor_id, price, duration_minutes)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, doctor_id, price, duration))

        service_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'CREATE', 'services', service_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при добавлении услуги: {e}")
        return False

def update_service(service_id, name, description, doctor_id, price, duration):
    """Обновить данные услуги"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE services
            SET name = ?, description = ?, doctor_id = ?, price = ?, duration_minutes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, description, doctor_id, price, duration, service_id))

        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'UPDATE', 'services', service_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при обновлении услуги: {e}")
        return False

def deactivate_service(service_id):
    """Деактивировать услугу"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE services SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (service_id,))

        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'UPDATE', 'services', service_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при деактивации услуги: {e}")
        return False

def get_doctors(search_query=None, specialization_filter="Все", show_active_only=True):
    """Получить список врачей"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, first_name, last_name, specialization, phone, email, is_active, created_at
        FROM doctors
        WHERE 1=1
    """

    params = []

    if search_query:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR specialization LIKE ?)"
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    if specialization_filter != "Все":
        query += " AND specialization = ?"
        params.append(specialization_filter)

    if show_active_only:
        query += " AND is_active = 1"

    query += " ORDER BY first_name, last_name"

    cursor.execute(query, params)
    doctors = cursor.fetchall()
    conn.close()

    return doctors

def get_doctor_by_id(doctor_id):
    """Получить врача по ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, first_name, last_name, specialization, phone, email, is_active, created_at
        FROM doctors WHERE id = ?
    """, (doctor_id,))

    doctor = cursor.fetchone()
    conn.close()

    return doctor

def add_doctor(first_name, last_name, specialization, phone, email):
    """Добавить нового врача"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO doctors (first_name, last_name, specialization, phone, email)
            VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, specialization, phone, email))

        doctor_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'CREATE', 'doctors', doctor_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при добавлении врача: {e}")
        return False

def update_doctor(doctor_id, first_name, last_name, specialization, phone, email):
    """Обновить данные врача"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE doctors
            SET first_name = ?, last_name = ?, specialization = ?, phone = ?, email = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (first_name, last_name, specialization, phone, email, doctor_id))

        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'UPDATE', 'doctors', doctor_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при обновлении врача: {e}")
        return False

def deactivate_doctor(doctor_id):
    """Деактивировать врача"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE doctors SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (doctor_id,))

        conn.commit()
        conn.close()

        # Логируем действие
        log_audit_action(st.session_state['user_id'], 'UPDATE', 'doctors', doctor_id)

        return True
    except Exception as e:
        st.error(f"❌ Ошибка при деактивации врача: {e}")
        return False
