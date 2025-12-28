#!/usr/bin/env python3
"""
CRM система версии 2.0 с кликабельными ячейками календаря и системой статусов
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import hashlib

# Импорт утилит для работы с часовым поясом
try:
    from timezone_utils import get_local_today, get_local_now
    USE_TIMEZONE = True
except ImportError:
    # Если модуль не найден, используем стандартные функции
    get_local_today = date.today
    get_local_now = datetime.now
    USE_TIMEZONE = False
from database import (
    get_connection, search_clients, create_client, get_client_by_id,
    get_all_doctors, get_services_by_doctor, get_all_services, create_appointment,
    get_appointment_by_id, update_appointment_status, get_appointments_by_date_range,
    delete_appointment, log_audit_action,
    add_service_to_appointment, remove_service_from_appointment,
    get_appointment_services, get_total_appointment_cost,
    add_payment_to_service, get_appointment_payments_summary, update_appointment_payment_status
)
from auth import get_status_color, get_status_emoji

def get_doctor_color(doctor_name):
    """Генерация уникального ЯРКОГО и ЗАМЕТНОГО цвета для врача"""
    hash_object = hashlib.md5(doctor_name.encode())
    hex_dig = hash_object.hexdigest()
    
    # Преобразуем в RGB
    r = int(hex_dig[0:2], 16)
    g = int(hex_dig[2:4], 16)
    b = int(hex_dig[4:6], 16)
    
    # Делаем НАСЫЩЕННЫМ но СВЕТЛЫМ (хорошо видно на белом фоне)
    # Формула: (color + 255) / 2 для ярких пастельных тонов
    r = int((r + 255) / 2)
    g = int((g + 255) / 2)
    b = int((b + 255) / 2)
    
    # Увеличиваем насыщенность: отодвигаем от серого
    avg = (r + g + b) / 3
    r = int(r + (r - avg) * 0.3)
    g = int(g + (g - avg) * 0.3)
    b = int(b + (b - avg) * 0.3)
    
    # Ограничиваем диапазон
    r = max(100, min(255, r))  # не темнее 100, не светлее 255
    g = max(100, min(255, g))
    b = max(100, min(255, b))
    
    return f"#{r:02x}{g:02x}{b:02x}"

def get_initials(full_name):
    """Форматирование имени как 'И. Фамилия'"""
    parts = full_name.split()
    if len(parts) >= 2:
        return f"{parts[0][0].upper()}. {parts[1]}"
    return full_name

def show_appointment_form(appointment_id=None, selected_date=None, selected_time=None, selected_doctor_id=None):
    """Форма регистрации/редактирования приема"""
    st.subheader("📝 Регистрация приема" if not appointment_id else "✏️ Редактирование приема")
    
    # Получаем данные приема если редактируем
    appointment_data = None
    if appointment_id:
        appointment_data = get_appointment_by_id(appointment_id)
        if not appointment_data:
            st.error("❌ Прием не найден")
            return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Поиск пациента с выпадающим списком
        if appointment_data:
            client_query = f"{appointment_data[10]} {appointment_data[11]}"
            selected_client_id = appointment_data[1]
            st.info(f"👤 Пациент: {appointment_data[10]} {appointment_data[11]} ({appointment_data[12]})")
        else:
            # Получаем всех клиентов для выпадающего списка
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, first_name, last_name, phone FROM clients ORDER BY last_name, first_name')
            all_clients = cursor.fetchall()
            conn.close()
            
            client_options = ["-- Выберите пациента или начните печатать --"] + [
                f"{client[1]} {client[2]} ({client[3]})" for client in all_clients
            ]
            client_ids = {f"{client[1]} {client[2]} ({client[3]})": client[0] for client in all_clients}
            
            # Выпадающий список с поиском
            selected_client_option = st.selectbox(
                "👤 Выберите пациента:",
                options=client_options,
                key="client_select_dropdown",
                help="Начните печатать для поиска пациента"
            )
            
            if selected_client_option != "-- Выберите пациента или начните печатать --":
                selected_client_id = client_ids[selected_client_option]
                st.session_state['selected_client_id'] = selected_client_id
                
                # Показываем выбранного пациента
                client_data = get_client_by_id(selected_client_id)
                if client_data:
                    st.success(f"✅ Выбран: {client_data[1]} {client_data[2]} ({client_data[4]})")
            else:
                selected_client_id = st.session_state.get('selected_client_id')
        
        # Форма создания нового пациента
        if not selected_client_id and not appointment_data:
            st.markdown("**Создать нового пациента:**")
            with st.form("create_client_form"):
                new_first_name = st.text_input("Имя *:", key="new_first_name")
                new_last_name = st.text_input("Фамилия *:", key="new_last_name")
                new_birth_date = st.date_input(
                    "Дата рождения:", 
                    key="new_birth_date",
                    min_value=datetime(1910, 1, 1).date(),
                    max_value=datetime(2025, 12, 31).date(),
                    help="Выберите дату рождения (1910-2025)"
                )
                new_phone = st.text_input("Телефон *:", key="new_phone", help="Введите номер без +7 (например: 7011234567)")
                new_email = st.text_input("Email (необязательно):", key="new_email")
                
                if st.form_submit_button("➕ Создать пациента", use_container_width=True):
                    if new_first_name and new_last_name and new_phone:
                        client_id = create_client(new_first_name, new_last_name, new_birth_date, new_phone, new_email)
                        if client_id:
                            st.success("✅ Пациент создан!")
                            st.session_state['selected_client_id'] = client_id
                            st.rerun()
                        else:
                            st.error("❌ Ошибка создания пациента (возможно, телефон уже существует)")
                    else:
                        st.error("❌ Заполните обязательные поля")
        
    with col2:
        # Выбор врача
        doctors = get_all_doctors()
        doctor_options = {f"{doc[1]} {doc[2]}": doc[0] for doc in doctors}
        
        if appointment_data:
            selected_doctor_name = f"{appointment_data[13]} {appointment_data[14]}"
            selected_doctor_id = appointment_data[2]
        else:
            selected_doctor_name = st.selectbox(
                "👨‍⚕️ Выберите врача:",
                options=list(doctor_options.keys()),
                key="doctor_select"
            )
            selected_doctor_id = doctor_options.get(selected_doctor_name)
            # Сохраняем в session_state
            st.session_state['selected_doctor_id'] = selected_doctor_id
        
        # Выбор услуги
        if selected_doctor_id:
            services = get_services_by_doctor(selected_doctor_id)
            service_options = {f"{srv[1]} ({srv[3]} KZT)": srv[0] for srv in services}
            
            if appointment_data:
                selected_service_name = appointment_data[16]
                selected_service_id = appointment_data[3]
            else:
                if services:
                    selected_service_name = st.selectbox(
                        "🏥 Выберите услугу:",
                        options=list(service_options.keys()),
                        key="service_select"
                    )
                    selected_service_id = service_options.get(selected_service_name)
                    # Сохраняем в session_state
                    st.session_state['selected_service_id'] = selected_service_id
                else:
                    st.warning("У этого врача нет доступных услуг")
                    selected_service_id = None
    
    # Форма приема
    with st.form("appointment_form"):
        # Дата и время
        col3, col4 = st.columns(2)
        with col3:
            if appointment_data:
                appointment_date = datetime.strptime(appointment_data[4], '%Y-%m-%d').date()
            else:
                appointment_date = st.date_input(
                    "📅 Дата приема:",
                    value=selected_date or get_local_today(),
                    key="appointment_date"
                )
        
        with col4:
            if appointment_data:
                appointment_time = datetime.strptime(appointment_data[5], '%H:%M:%S').time()
            else:
                appointment_time = st.time_input(
                    "🕐 Время приема:",
                    value=selected_time or time(9, 0),
                    key="appointment_time"
                )
        
        # Статус приема (только для редактирования)
        if appointment_data:
            status_options = ['записан', 'на приеме', 'прием завершен', 'не явился']
            current_status = appointment_data[6]
            new_status = st.selectbox(
                "📊 Статус приема:",
                options=status_options,
                index=status_options.index(current_status),
                key="appointment_status"
            )
        
        # Заметки
        notes = st.text_area(
            "📝 Заметки:",
            value=appointment_data[7] if appointment_data else "",
            key="appointment_notes"
        )
        
        # Источник пациента (новое поле в v2.7)
        source_options = [
            "Повторное посещение",
            "Интернет реклама",
            "Рекомендация",
            "2ГИС",
            "Instagram",
            "Facebook",
            "Другое"
        ]
        
        # Получаем текущий источник для редактирования или дефолтный для создания
        if appointment_data and len(appointment_data) > 17:
            current_source = appointment_data[17] if appointment_data[17] else "Повторное посещение"
        else:
            current_source = "Повторное посещение"
        
        source = st.selectbox(
            "🌐 Откуда узнали о нас:",
            options=source_options,
            index=source_options.index(current_source) if current_source in source_options else 0,
            key="appointment_source",
            help="Источник, из которого пациент узнал о клинике"
        )
        
        # Кнопки
        if appointment_id:
            # Для редактирования - три кнопки
            col5, col6, col7 = st.columns(3)
        else:
            # Для создания - две кнопки
            col5, col6 = st.columns(2)
            col7 = None
        
        with col5:
            if st.form_submit_button("💾 Сохранить", use_container_width=True):
                # Защита от двойных кликов
                if 'saving_appointment' not in st.session_state:
                    st.session_state['saving_appointment'] = False
                
                if st.session_state['saving_appointment']:
                    st.warning("⏳ Сохранение в процессе...")
                    return
                
                st.session_state['saving_appointment'] = True
                
                if appointment_id:
                    # Обновление существующего приема
                    update_appointment_status(appointment_id, new_status)
                    st.success("✅ Прием обновлен!")
                    log_audit_action(st.session_state['user_id'], 'UPDATE', 'appointments', appointment_id)
                    st.session_state['saving_appointment'] = False
                else:
                    # Создание нового приема
                    # Получаем значения из session_state
                    client_id_to_use = selected_client_id or st.session_state.get('selected_client_id')
                    doctor_id_to_use = selected_doctor_id or st.session_state.get('selected_doctor_id')
                    service_id_to_use = selected_service_id or st.session_state.get('selected_service_id')
                    
                    if client_id_to_use and doctor_id_to_use and service_id_to_use:
                        new_appointment_id = create_appointment(
                            client_id_to_use, doctor_id_to_use, service_id_to_use,
                            appointment_date, appointment_time, notes, source
                        )
                        if new_appointment_id:
                            st.success("✅ Прием создан!")
                            log_audit_action(st.session_state['user_id'], 'CREATE', 'appointments', new_appointment_id)
                            
                            # Очищаем session_state
                            for key in ['selected_client_id', 'selected_doctor_id', 'selected_service_id',
                                       'new_appointment_date', 'new_appointment_time', 'edit_appointment_id', 'saving_appointment']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.rerun()
                        else:
                            st.error("❌ Ошибка создания приема")
                            st.session_state['saving_appointment'] = False
                    else:
                        missing = []
                        if not client_id_to_use:
                            missing.append("пациента")
                        if not doctor_id_to_use:
                            missing.append("врача")
                        if not service_id_to_use:
                            missing.append("услугу")
                        st.error(f"❌ Пожалуйста, выберите: {', '.join(missing)}")
                
                # Очищаем после обновления
                if appointment_id:
                    for key in ['selected_client_id', 'selected_doctor_id', 'selected_service_id',
                               'new_appointment_date', 'new_appointment_time', 'edit_appointment_id']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        
            with col6:
                if st.form_submit_button("❌ Отмена", use_container_width=True):
                    # Очищаем все ключи session_state
                    for key in ['selected_client_id', 'selected_doctor_id', 'selected_service_id',
                               'new_appointment_date', 'new_appointment_time', 'edit_appointment_id', 'saving_appointment']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        
        # Кнопка удаления (только для редактирования)
        if col7:
            with col7:
                if st.form_submit_button("🗑️ Удалить", use_container_width=True, type="secondary"):
                    st.session_state['confirm_delete_appointment'] = appointment_id
    
    # Обработка подтверждения удаления (вне формы)
    if 'confirm_delete_appointment' in st.session_state:
        delete_id = st.session_state['confirm_delete_appointment']
        st.warning(f"⚠️ Вы уверены, что хотите удалить этот прием?")
        
        col_confirm1, col_confirm2, col_confirm3 = st.columns(3)
        with col_confirm1:
            if st.button("✅ Да, удалить", key="confirm_delete_yes", use_container_width=True):
                if delete_appointment(delete_id):
                    st.success("✅ Прием успешно удален!")
                    log_audit_action(st.session_state['user_id'], 'DELETE', 'appointments', delete_id)
                    
                    # Очищаем все ключи
                    for key in ['selected_client_id', 'selected_doctor_id', 'selected_service_id',
                               'new_appointment_date', 'new_appointment_time', 'edit_appointment_id',
                               'confirm_delete_appointment']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()
                else:
                    st.error("❌ Ошибка при удалении приема")
        
        with col_confirm2:
            if st.button("❌ Отмена", key="confirm_delete_no", use_container_width=True):
                del st.session_state['confirm_delete_appointment']
                st.rerun()
    
    # Управление услугами (только для редактирования или после создания)
    if appointment_id:
        st.markdown("---")
        st.subheader("🏥 Управление услугами")
        
        # Показываем текущие услуги с редактируемой ценой (v2.7)
        current_services = get_appointment_services(appointment_id)
        if current_services:
            st.write("**Текущие услуги:**")
            
            for service in current_services:
                appointment_service_id = service[0]
                service_id = service[1]
                service_name = service[2]
                service_description = service[3]
                actual_price = service[4]  # Фактическая цена (из appointment_services)
                base_price = service[5]  # Базовая цена (из services)
                duration = service[6]
                doctor_name = f"{service[7]} {service[8]}"
                
                with st.form(f"service_edit_form_{appointment_service_id}"):
                    col_srv1, col_srv2, col_srv3, col_srv4, col_srv5 = st.columns([2, 2, 1.5, 1, 1])
                    
                    with col_srv1:
                        st.write(f"📋 {service_name}")
                    with col_srv2:
                        st.write(f"👨‍⚕️ {doctor_name}")
                    with col_srv3:
                        # Редактируемая цена с подсказкой базовой цены
                        new_price = st.number_input(
                            "Цена (₸)",
                            value=float(actual_price),
                            min_value=0.0,
                            step=100.0,
                            key=f"price_{appointment_service_id}",
                            help=f"Базовая цена: {base_price} ₸",
                            label_visibility="collapsed"
                        )
                    with col_srv4:
                        if st.form_submit_button("💾", help="Сохранить цену"):
                            if new_price != actual_price:
                                # Обновляем цену в БД
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE appointment_services 
                                    SET price = ? 
                                    WHERE id = ?
                                ''', (new_price, appointment_service_id))
                                conn.commit()
                                conn.close()
                                
                                # Логируем изменение цены
                                log_audit_action(
                                    st.session_state['user_id'], 
                                    'UPDATE', 
                                    'appointment_services', 
                                    appointment_service_id,
                                    old_values={'price': actual_price},
                                    new_values={'price': new_price}
                                )
                                
                                st.success(f"✅ Цена обновлена: {actual_price} → {new_price} ₸")
                                st.rerun()
                    with col_srv5:
                        if st.form_submit_button("🗑️", help="Удалить услугу"):
                            if remove_service_from_appointment(appointment_id, appointment_service_id):
                                st.success("✅ Услуга удалена")
                                log_audit_action(st.session_state['user_id'], 'DELETE', 'appointment_services', appointment_service_id)
                                st.rerun()
            
            # Показываем общую стоимость
            total_cost = get_total_appointment_cost(appointment_id)
            st.info(f"💰 **Общая стоимость:** {total_cost} KZT")
        else:
            st.info("Услуги еще не добавлены")
        
        # Форма добавления услуги
        st.markdown("**Добавить услугу:**")
        
        # Получаем все доступные услуги
        all_services = get_all_services()
        if all_services:
            service_options = {
                f"{srv[1]} - {srv[5]} {srv[6]} ({srv[3]} KZT)": (srv[0], srv[3]) 
                for srv in all_services
            }
            
            selected_new_service = st.selectbox(
                "Выберите услугу для добавления:",
                options=["-- Выберите услугу --"] + list(service_options.keys()),
                key="add_service_select"
            )
            
            if selected_new_service != "-- Выберите услугу --":
                service_id_to_add, service_price = service_options[selected_new_service]
                
                col_add1, col_add2 = st.columns([1, 3])
                with col_add1:
                    if st.button("➕ Добавить услугу", use_container_width=True):
                        if add_service_to_appointment(appointment_id, service_id_to_add, service_price):
                            st.success("✅ Услуга добавлена")
                            log_audit_action(st.session_state['user_id'], 'CREATE', 'appointment_services', appointment_id)
                            st.rerun()
                        else:
                            st.error("❌ Услуга уже добавлена или ошибка")
        else:
            st.warning("Нет доступных услуг")
    
    # Секция оплаты (v2.7) - ВЫНЕСЕНА ИЗ БЛОКА УПРАВЛЕНИЯ УСЛУГАМИ
    if appointment_id:
        current_services = get_appointment_services(appointment_id)
        
        st.markdown("---")
        st.subheader("💳 Управление оплатой")
        
        if current_services:
            # Получаем общую стоимость
            total_cost = get_total_appointment_cost(appointment_id)
            
            # Получаем сводку по оплатам
            payments_summary = get_appointment_payments_summary(appointment_id)
            total_paid = sum([p[1] for p in payments_summary]) if payments_summary else 0.0
            remaining = total_cost - total_paid
            
            # Показываем статус оплаты
            col_pay1, col_pay2, col_pay3 = st.columns(3)
            
            with col_pay1:
                st.metric("💰 Общая стоимость", f"{total_cost:,.0f} ₸")
            with col_pay2:
                st.metric("✅ Оплачено", f"{total_paid:,.0f} ₸")
            with col_pay3:
                delta_color = "normal" if remaining == 0 else ("inverse" if remaining > 0 else "off")
                st.metric("📊 Остаток", f"{remaining:,.0f} ₸")
            
            # Показываем детали оплат
            if payments_summary:
                st.markdown("**Детали оплаты:**")
                for payment in payments_summary:
                    method_icon = {
                        "Карта": "💳",
                        "Наличные": "💵",
                        "Kaspi QR": "📱",
                        "Перевод": "💸"
                    }.get(payment[0], "💰")
                    st.write(f"{method_icon} **{payment[0]}:** {payment[1]:,.0f} ₸")
            
            # Форма добавления оплаты
            if remaining > 0:
                st.markdown("**Добавить оплату:**")
                
                # Выбор методов оплаты (вне формы для динамического обновления)
                payment_methods = st.multiselect(
                    "Выберите методы оплаты:",
                    ["Kaspi QR", "Карта", "Наличные", "Перевод"],
                    default=["Kaspi QR"],
                    key="payment_methods_select"
                )
                
                # Суммы для каждого метода (вне формы)
                payment_amounts = {}
                total_payment_input = 0.0
                
                if payment_methods:
                    st.markdown("**Укажите суммы:**")
                    
                    cols = st.columns(len(payment_methods))
                    for idx, method in enumerate(payment_methods):
                        with cols[idx]:
                            # Если только один метод, предлагаем полную сумму
                            default_amount = remaining if len(payment_methods) == 1 else 0.0
                            
                            amount = st.number_input(
                                f"{method}:",
                                min_value=0.0,
                                max_value=float(remaining),
                                value=float(default_amount),
                                step=100.0,
                                key=f"payment_amount_{method}"
                            )
                            payment_amounts[method] = amount
                            total_payment_input += amount
                
                # Показываем итоговую сумму и остаток
                if payment_methods:
                    col_sum1, col_sum2, col_sum3 = st.columns(3)
                    with col_sum1:
                        st.info(f"**Итого к оплате:** {total_payment_input:,.0f} ₸")
                    with col_sum2:
                        if total_payment_input < remaining:
                            st.warning(f"**Осталось:** {remaining - total_payment_input:,.0f} ₸")
                        elif total_payment_input == remaining:
                            st.success("**Полная оплата**")
                        else:
                            st.error(f"**Переплата:** {total_payment_input - remaining:,.0f} ₸")
                    with col_sum3:
                        st.write("")
                else:
                    st.warning("Выберите хотя бы один метод оплаты")
                
                # Форма для сохранения
                with st.form("add_payment_form"):
                    # Кнопка сохранения
                    if st.form_submit_button("Сохранить оплату", use_container_width=True):
                        if not payment_methods:
                            st.error("Выберите хотя бы один метод оплаты")
                        elif total_payment_input > remaining:
                            st.error("Сумма оплаты превышает остаток!")
                        elif total_payment_input == 0:
                            st.warning("Укажите сумму оплаты")
                        else:
                            # Сохраняем платежи для каждой услуги
                            success_count = 0
                            for service in current_services:
                                appointment_service_id = service[0]  # ID из таблицы appointment_services
                                service_price = service[4]  # Фактическая цена услуги
                                service_proportion = service_price / total_cost
                                
                                # Распределяем каждый метод оплаты пропорционально
                                for method, total_method_amount in payment_amounts.items():
                                    if total_method_amount > 0:
                                        service_payment_amount = total_method_amount * service_proportion
                                        
                                        payment_success = add_payment_to_service(appointment_service_id, method, service_payment_amount)
                                        if payment_success:
                                            success_count += 1
                            
                            if success_count > 0:
                                # Обновляем статус оплаты приема
                                new_total_paid = total_paid + total_payment_input
                                
                                if update_appointment_payment_status(appointment_id, new_total_paid, total_cost):
                                    # Логируем действие
                                    log_audit_action(st.session_state['user_id'], 'CREATE', 'appointment_service_payments', appointment_id)
                                    
                                    # ВАЖНО: Сохраняем appointment_id перед rerun
                                    # чтобы форма снова открылась с обновленными данными
                                    st.session_state['edit_appointment_id'] = appointment_id
                                    
                                    # Успешное сообщение
                                    st.success(f"Оплата {total_payment_input:,.0f} ₸ успешно добавлена! Новый баланс: {new_total_paid:,.0f} ₸ из {total_cost:,.0f} ₸")
                                    
                                    # Перезагружаем страницу для обновления данных
                                    st.rerun()
                                else:
                                    st.error("❌ Ошибка обновления статуса оплаты")
                            else:
                                st.error(f"❌ Ошибка при сохранении оплаты")
            else:
                if remaining == 0:
                    st.success("✅ Прием полностью оплачен!")
                else:
                    st.info("💵 Переплата зафиксирована")
        else:
            st.info("Добавьте услуги для управления оплатой")

def show_calendar_view():
    """Календарное представление с кликабельными ячейками"""
    st.subheader("📅 Календарь приемов")
    
    # Навигация по неделям
    col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1, 1, 1.5])
    
    with col1:
        if st.button("⬅️ Предыдущая неделя", key="prev_week_v2"):
            if 'current_week_offset' not in st.session_state:
                st.session_state['current_week_offset'] = 0
            st.session_state['current_week_offset'] -= 1
            st.rerun()
    
    with col2:
        if st.button("Следующая неделя ➡️", key="next_week_v2"):
            if 'current_week_offset' not in st.session_state:
                st.session_state['current_week_offset'] = 0
            st.session_state['current_week_offset'] += 1
            st.rerun()
    
    with col3:
        if st.button("📅 Сегодня", key="today_view_v2"):
            st.session_state['current_week_offset'] = 0
            st.session_state['view_mode'] = 'today'
            st.rerun()
    
    with col4:
        if st.button("📆 Неделя", key="week_view_v2"):
            st.session_state['view_mode'] = 'week'
            st.rerun()
    
    with col5:
        if st.button("➕ Добавить прием", key="add_appointment_v2", type="primary"):
            # Открываем форму для создания нового приема
            st.session_state['new_appointment_date'] = get_local_today()
            st.session_state['new_appointment_time'] = time(9, 0)
            st.rerun()
    
    # Получаем текущую дату и смещение
    today = get_local_today()
    current_week_offset = st.session_state.get('current_week_offset', 0)
    view_mode = st.session_state.get('view_mode', 'week')
    
    # Фильтр врачей и настройки отображения
    col_filter1, col_filter2 = st.columns([3, 1])
    
    with col_filter1:
        doctors = get_all_doctors()
        doctor_options = {f"{doc[1]} {doc[2]}": doc[0] for doc in doctors}
        
        selected_doctors = st.multiselect(
            "👨‍⚕️ Выберите врачей:",
            options=list(doctor_options.keys()),
            default=list(doctor_options.keys()),
            key="doctor_filter_v2"
        )
    
    with col_filter2:
        st.markdown("<br>", unsafe_allow_html=True)  # Выравнивание по вертикали
        color_coding_enabled = st.checkbox(
            "🎨 Цветовое кодирование",
            value=False,
            key="color_coding_toggle",
            help="Включить/выключить цвета врачей в календаре"
        )
    
    selected_doctor_ids = [doctor_options[doc] for doc in selected_doctors]
    
    # Легенда цветов врачей (если включено и выбрано несколько врачей)
    if color_coding_enabled and len(selected_doctors) > 1:
        # Добавляем expander для длинных списков врачей (6+)
        if len(selected_doctors) > 5:
            with st.expander("🎨 Легенда цветов врачей", expanded=True):
                legend_cols = st.columns(min(len(selected_doctors), 4))
                
                for idx, doctor_name in enumerate(selected_doctors):
                    col_idx = idx % 4
                    with legend_cols[col_idx]:
                        doctor_color = get_doctor_color(doctor_name)
                        st.markdown(f"""
                        <div style="
                            display: inline-block;
                            background-color: {doctor_color};
                            padding: 5px 10px;
                            border-radius: 4px;
                            margin: 2px;
                            font-size: 12px;
                            border: 1px solid #ccc;
                        ">
                            {doctor_name}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown("**🎨 Легенда цветов:**")
            legend_cols = st.columns(min(len(selected_doctors), 4))
            
            for idx, doctor_name in enumerate(selected_doctors):
                col_idx = idx % 4
                with legend_cols[col_idx]:
                    doctor_color = get_doctor_color(doctor_name)
                    st.markdown(f"""
                    <div style="
                        display: inline-block;
                        background-color: {doctor_color};
                        padding: 5px 10px;
                        border-radius: 4px;
                        margin: 2px;
                        font-size: 12px;
                        border: 1px solid #ccc;
                    ">
                        {doctor_name}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Определяем диапазон дат
    if view_mode == 'today':
        start_date = today
        end_date = today
        st.subheader(f"📅 Записи на {today.strftime('%d.%m.%Y')}")
    else:
        week_start = today + timedelta(days=-today.weekday() + (current_week_offset * 7))
        start_date = week_start
        end_date = week_start + timedelta(days=6)
        st.subheader(f"📅 Неделя с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}")
    
    # Получаем приемы
    appointments = get_appointments_by_date_range(start_date, end_date)
    
    # Фильтруем по врачам
    if selected_doctor_ids:
        appointments = [apt for apt in appointments if apt[2] in selected_doctor_ids]
    
    # Создаем словарь приемов по дате и времени
    appointments_dict = {}
    for apt in appointments:
        # Конвертируем строку даты в объект date
        if isinstance(apt[4], str):
            apt_date = datetime.strptime(apt[4], '%Y-%m-%d').date()
        else:
            apt_date = apt[4]
        
        apt_time = apt[5]
        
        if apt_date not in appointments_dict:
            appointments_dict[apt_date] = {}
        
        # Храним список приемов для каждого времени
        if apt_time not in appointments_dict[apt_date]:
            appointments_dict[apt_date][apt_time] = []
        
        appointments_dict[apt_date][apt_time].append(apt)
    
    # Временные слоты (15-минутные интервалы)
    time_slots = []
    for hour in range(9, 18):
        for minute in [0, 15, 30, 45]:
            time_slots.append(time(hour, minute))
    
    if view_mode == 'today':
        # Показываем только сегодня
        show_day_appointments(today, appointments_dict, time_slots, color_coding_enabled)
    else:
        # Показываем неделю
        show_week_appointments(start_date, appointments_dict, time_slots, today, color_coding_enabled)

def show_day_appointments(day, appointments_dict, time_slots, color_coding_enabled=True):
    """Показать записи за день"""
    st.markdown("---")
    
    # Заголовок дня
    day_name = day.strftime('%A')
    day_names = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник', 
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }
    
    st.markdown(f"### {day_names.get(day_name, day_name)} {day.strftime('%d.%m.%Y')}")
    
    # Показываем временные слоты
    for time_slot in time_slots:
        time_str = time_slot.strftime('%H:%M')
        
        # Ищем приемы в этом временном слоте
        day_appointments = appointments_dict.get(day, {})
        slot_appointments = []
        
        for apt_time, appointment_list in day_appointments.items():
            apt_time_obj = datetime.strptime(apt_time, '%H:%M:%S').time()
            if apt_time_obj == time_slot:
                # appointment_list теперь список приемов
                slot_appointments.extend(appointment_list)
        
        # Создаем кликабельную ячейку
        if slot_appointments:
            # Есть приемы
            if len(slot_appointments) == 1:
                # Один прием
                appointment = slot_appointments[0]
                status = appointment[6]
                status_color = get_status_color(status)
                status_emoji = get_status_emoji(status)
                
                client_name = get_initials(f"{appointment[10]} {appointment[11]}")
                doctor_name = get_initials(f"{appointment[13]} {appointment[14]}")
                doctor_full_name = f"{appointment[13]} {appointment[14]}"
                
                # Определяем цвет фона
                if color_coding_enabled:
                    doctor_bg_color = get_doctor_color(doctor_full_name)
                else:
                    doctor_bg_color = "#f0f0f0"  # Серый по умолчанию
                
                # Уникальный ключ для ячейки
                cell_key = f"day_apt_{appointment[0]}_{time_slot.strftime('%H%M')}"
                
                # Укороченный текст для ячейки
                client_short = client_name if len(client_name) <= 15 else client_name[:13] + "."
                doctor_short = doctor_name if len(doctor_name) <= 15 else doctor_name[:13] + "."
                button_text = f"{status_emoji} {time_str}\n👤 {client_short}\n👨‍⚕️ {doctor_short}"
                full_text = f"{time_str} | {client_name} → {doctor_name}"
                
                # РЕШЕНИЕ: Кликабельная карточка через форму
                with st.form(key=f"form_{cell_key}"):
                    # HTML карточка с данными
                    card_html = f"""
                    <div style="
                        background-color: {doctor_bg_color};
                        border: 3px solid {status_color};
                        border-radius: 8px;
                        padding: 6px 5px;
                        margin: 2px 0px;
                        min-height: 78px;
                        max-height: 78px;
                        height: 78px;
                        box-sizing: border-box;
                        overflow: hidden;
                        display: flex;
                        flex-direction: column;
                        align-items: flex-start;
                        justify-content: flex-start;
                        font-size: 11px;
                        line-height: 1.2;
                        color: #000000;
                        white-space: pre-line;
                        transition: transform 0.1s;
                    " title="{full_text}">
                        <div style="font-weight: 600;">{status_emoji} {time_str}</div>
                        <div style="margin-top: 2px;">👤 {client_short}</div>
                        <div style="opacity: 0.85;">👨‍⚕️ {doctor_short}</div>
                    </div>
                    """
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Очень маленькая кнопка редактирования
                    edit_btn_key = f"edit_btn_day_{appointment[0]}"
                    
                    # Применяем глобальные стили для маленьких кнопок редактирования
                    st.markdown("""
                        <style>
                        /* Маленькие кнопки редактирования в календаре */
                        div[data-testid="column"] button[type="submit"] {
                            font-size: 8px !important;
                            padding: 1px 3px !important;
                            height: 16px !important;
                            min-height: 16px !important;
                            max-height: 16px !important;
                            line-height: 1 !important;
                            width: auto !important;
                            min-width: 24px !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    if st.form_submit_button("✏️", type="secondary", key=edit_btn_key):
                        st.session_state['edit_appointment_id'] = appointment[0]
                        st.rerun()
            else:
                # Несколько приемов
                appointments_info = f"📋 {len(slot_appointments)} приема в {time_str}:\n"
                for apt in slot_appointments:
                    client = get_initials(f"{apt[10]} {apt[11]}")
                    doctor = get_initials(f"{apt[13]} {apt[14]}")
                    appointments_info += f"• {client} → {doctor}\n"
                
                # Кнопка с множественными приемами
                if st.button(
                    appointments_info.strip(),
                    key=f"day_multi_{time_slot}",
                    help="Нажмите для выбора приема",
                    use_container_width=True
                ):
                    st.session_state['multi_appointment_slot'] = {
                        'date': day,
                        'time': time_slot,
                        'appointments': slot_appointments
                    }
                    st.rerun()
        else:
            # Пустой слот - с подсказкой "+"
            empty_card_html = f"""
            <div style="
                min-height: 78px;
                height: 78px;
                width: 100%;
                box-sizing: border-box;
                margin: 2px;
                padding: 6px 5px;
                border: 2px dashed #ddd;
                background-color: #f9f9f9;
                border-radius: 8px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                color: #999;
                font-size: 11px;
            ">
                <div style="font-size: 20px; color: #ccc;">+</div>
                <div style="font-size: 10px; margin-top: 4px;">{time_str}</div>
            </div>
            """
            st.markdown(empty_card_html, unsafe_allow_html=True)

def show_week_appointments(start_date, appointments_dict, time_slots, today, color_coding_enabled=True):
    """Показать записи за неделю"""
    st.markdown("---")
    
    # Заголовки: колонка времени + дни недели
    day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    cols = st.columns([0.7, 1, 1, 1, 1, 1, 1, 1])  # Первая колонка уже для времени
    
    # Заголовок колонки времени
    with cols[0]:
        st.markdown("""
        <div style="
            padding: 8px;
            text-align: center;
            font-weight: bold;
            font-size: 12px;
        ">
            Время
        </div>
        """, unsafe_allow_html=True)
    
    # Заголовки дней недели
    for i, col in enumerate(cols[1:], start=0):
        current_day = start_date + timedelta(days=i)
        is_today = current_day == today
        
        with col:
            if is_today:
                # Выделяем текущий день
                st.markdown(f"""
                <div style="
                    background-color: #FFD700;
                    border: 2px solid #FFA500;
                    padding: 8px;
                    border-radius: 8px;
                    text-align: center;
                    font-weight: bold;
                ">
                    {day_names[i]}<br>{current_day.strftime('%d.%m')}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    padding: 8px;
                    text-align: center;
                ">
                    {day_names[i]}<br>{current_day.strftime('%d.%m')}
                </div>
                """, unsafe_allow_html=True)
    
    # Показываем временные слоты
    for time_slot in time_slots:
        time_str = time_slot.strftime('%H:%M')
        cols = st.columns([0.7, 1, 1, 1, 1, 1, 1, 1])
        
        # Колонка с временем
        with cols[0]:
            st.markdown(f"""
            <div style="
                padding: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
                color: #555;
                background-color: #f0f0f0;
                border-radius: 4px;
            ">
                {time_str}
            </div>
            """, unsafe_allow_html=True)
        
        # Колонки с днями
        for i, col in enumerate(cols[1:], start=0):
            current_day = start_date + timedelta(days=i)
            day_appointments = appointments_dict.get(current_day, {})
            
            with col:
                # Ищем приемы в этом временном слоте
                slot_appointments = []
                for apt_time, appointment_list in day_appointments.items():
                    apt_time_obj = datetime.strptime(apt_time, '%H:%M:%S').time()
                    if apt_time_obj == time_slot:
                        # appointment_list теперь список приемов
                        slot_appointments.extend(appointment_list)
                
                if slot_appointments:
                    # Есть приемы - объединяем в одну карточку если их несколько
                    if len(slot_appointments) == 1:
                        # Один прием
                        appointment = slot_appointments[0]
                        status = appointment[6]
                        status_color = get_status_color(status)
                        status_emoji = get_status_emoji(status)
                        
                        client_name = get_initials(f"{appointment[10]} {appointment[11]}")
                        doctor_name = get_initials(f"{appointment[13]} {appointment[14]}")
                        doctor_full_name = f"{appointment[13]} {appointment[14]}"
                        
                        # Определяем цвет фона
                        if color_coding_enabled:
                            doctor_bg_color = get_doctor_color(doctor_full_name)
                            # DEBUG: показываем что цвет генерируется
                            # st.write(f"DEBUG: {doctor_full_name} → {doctor_bg_color}")
                        else:
                            doctor_bg_color = "#f0f0f0"  # Серый по умолчанию
                        
                        # Уникальный ID для ячейки
                        cell_key = f"week_apt_{appointment[0]}_{current_day.strftime('%Y%m%d')}_{time_slot.strftime('%H%M')}"
                        
                        # Укороченный текст для ячейки
                        client_short = client_name if len(client_name) <= 12 else client_name[:10] + "."
                        doctor_short = doctor_name if len(doctor_name) <= 12 else doctor_name[:10] + "."
                        button_text = f"{status_emoji}\n{client_short}\n{doctor_short}"
                        full_text = f"{status_emoji} {client_name} → {doctor_name}"
                        
                        # РЕШЕНИЕ: Кликабельная карточка через форму (bypass Streamlit ограничения)
                        with st.form(key=f"form_{cell_key}"):
                            # HTML карточка с данными
                            card_html = f"""
                            <div style="
                                background-color: {doctor_bg_color};
                                border: 2px solid {status_color};
                                border-radius: 6px;
                                padding: 4px 3px;
                                margin: 1px 0px;
                                min-height: 65px;
                                max-height: 65px;
                                height: 65px;
                                box-sizing: border-box;
                                overflow: hidden;
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: center;
                                font-size: 9px;
                                line-height: 1.1;
                                color: #000000;
                                text-align: center;
                                white-space: pre-line;
                                transition: transform 0.1s;
                            " title="{full_text}">
                                <div>{status_emoji}</div>
                                <div style="font-weight: 500;">{client_short}</div>
                                <div style="opacity: 0.8;">{doctor_short}</div>
                            </div>
                            """
                            
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            # Очень маленькая кнопка редактирования
                            edit_btn_key_week = f"edit_btn_week_{appointment[0]}"
                            
                            if st.form_submit_button("✏️", type="secondary", key=edit_btn_key_week):
                                st.session_state['edit_appointment_id'] = appointment[0]
                                st.rerun()
                    else:
                        # Несколько приемов - компактный список
                        appointments_text = f"{len(slot_appointments)} приема:\n"
                        for apt in slot_appointments:
                            client = get_initials(f"{apt[10]} {apt[11]}")
                            appointments_text += f"• {client}\n"
                        
                        # Используем цвет первого врача для фона
                        first_doctor = f"{slot_appointments[0][13]} {slot_appointments[0][14]}"
                        bg_color = get_doctor_color(first_doctor)
                        
                        # Кнопка с несколькими приемами
                        if st.button(
                            f"📋 {len(slot_appointments)}\n{appointments_text.strip()}",
                            key=f"week_multi_{current_day}_{time_slot}",
                            help="Нажмите для просмотра",
                            use_container_width=True
                        ):
                            # Показываем список для выбора
                            st.session_state['multi_appointment_slot'] = {
                                'date': current_day,
                                'time': time_slot,
                                'appointments': slot_appointments
                            }
                            st.rerun()
                else:
                    # Пустой слот - с подсказкой "+"
                    st.markdown("""
                    <div style="
                        min-height: 65px;
                        height: 65px;
                        width: 100%;
                        box-sizing: border-box;
                        margin: 1px;
                        padding: 4px 3px;
                        border: 1px dashed #ddd;
                        background-color: #f9f9f9;
                        border-radius: 6px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                        color: #ccc;
                        text-align: center;
                    ">
                        +
                    </div>
                    """, unsafe_allow_html=True)

def main():
    """Основная функция CRM системы версии 2.0"""
    st.set_page_config(
        page_title="CRM Система v2.0 - Медицинский Центр",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        from auth import login_page
        login_page()
        return
    
    # Основной интерфейс
    st.title("🏥 CRM Система v2.0 - Медицинский Центр")
    st.markdown("---")
    
    # Проверяем, нужно ли показать выбор из нескольких приемов
    if 'multi_appointment_slot' in st.session_state:
        slot_info = st.session_state['multi_appointment_slot']
        st.subheader(f"📋 Выберите прием для редактирования")
        st.info(f"Дата: {slot_info['date'].strftime('%d.%m.%Y')} | Время: {slot_info['time'].strftime('%H:%M')}")
        
        for appointment in slot_info['appointments']:
            status = appointment[6]
            status_emoji = get_status_emoji(status)
            client_name = f"{appointment[10]} {appointment[11]}"
            doctor_name = f"{appointment[13]} {appointment[14]}"
            service_name = appointment[16]
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{status_emoji} **{client_name}** | Врач: {doctor_name} | {service_name}")
            with col2:
                if st.button("✏️ Редактировать", key=f"select_apt_{appointment[0]}"):
                    st.session_state['edit_appointment_id'] = appointment[0]
                    del st.session_state['multi_appointment_slot']
                    st.rerun()
        
        if st.button("❌ Закрыть", key="close_multi_select"):
            del st.session_state['multi_appointment_slot']
            st.rerun()
    
    # Проверяем, нужно ли показать форму приема
    elif 'edit_appointment_id' in st.session_state:
        show_appointment_form(appointment_id=st.session_state['edit_appointment_id'])
        if st.button("❌ Закрыть", key="close_edit_form"):
            del st.session_state['edit_appointment_id']
            st.rerun()
    elif 'new_appointment_date' in st.session_state and 'new_appointment_time' in st.session_state:
        show_appointment_form(
            selected_date=st.session_state['new_appointment_date'],
            selected_time=st.session_state['new_appointment_time']
        )
        if st.button("❌ Закрыть", key="close_new_form"):
            del st.session_state['new_appointment_date']
            del st.session_state['new_appointment_time']
            st.rerun()
    else:
        # Показываем календарь
        show_calendar_view()

if __name__ == "__main__":
    main()
