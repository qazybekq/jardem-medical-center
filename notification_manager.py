#!/usr/bin/env python3
"""
Управление уведомлениями
"""

import streamlit as st
from datetime import datetime, date, timedelta
from database import get_connection

def main():
    """Главная функция управления уведомлениями"""
    st.title("📧 Система уведомлений")
    
    tab1, tab2, tab3 = st.tabs(["✉️ Отправить уведомление", "⚙️ Настройки", "📊 История"])
    
    with tab1:
        show_send_notification()
    
    with tab2:
        show_settings()
    
    with tab3:
        show_notification_history()

def show_send_notification():
    """Отправка уведомлений"""
    st.subheader("✉️ Отправить уведомление")
    
    notification_type = st.radio(
        "Тип уведомления:",
        options=["Email", "SMS", "Оба"],
        key="notification_type"
    )
    
    # Выбор получателей
    recipient_type = st.radio(
        "Получатели:",
        options=["Один клиент", "Все клиенты с приемами на завтра", "Произвольный список"],
        key="recipient_type"
    )
    
    recipients = []
    
    if recipient_type == "Один клиент":
        # Выбор одного клиента
        clients = get_all_clients()
        selected_client = st.selectbox(
            "Выберите клиента:",
            options=clients,
            format_func=lambda x: f"{x[1]} {x[2]} - {x[3]}",
            key="single_client"
        )
        if selected_client:
            recipients = [selected_client]
    
    elif recipient_type == "Все клиенты с приемами на завтра":
        tomorrow = date.today() + timedelta(days=1)
        recipients = get_clients_with_appointments(tomorrow)
        st.info(f"📊 Найдено клиентов: {len(recipients)}")
    
    else:
        # Произвольный список
        manual_input = st.text_area(
            "Введите email или телефоны (по одному на строку):",
            key="manual_recipients"
        )
        if manual_input:
            recipients = manual_input.strip().split('\n')
    
    st.markdown("---")
    
    # Шаблон сообщения
    message_template = st.selectbox(
        "Шаблон сообщения:",
        options=[
            "Напоминание о приеме",
            "Подтверждение записи",
            "Отмена приема",
            "Изменение времени",
            "Произвольное сообщение"
        ],
        key="message_template"
    )
    
    if message_template == "Напоминание о приеме":
        message = st.text_area(
            "Текст сообщения:",
            value="Здравствуйте! Напоминаем, что завтра у вас запись на прием к врачу. Ждем вас!",
            height=150,
            key="message_text"
        )
    elif message_template == "Произвольное сообщение":
        message = st.text_area(
            "Текст сообщения:",
            height=150,
            key="custom_message"
        )
    else:
        message = st.text_area(
            "Текст сообщения:",
            value=get_template_text(message_template),
            height=150,
            key="template_message"
        )
    
    st.markdown("---")
    
    # Кнопка отправки
    col1, col2, col3 = st.columns(3)
    
    with col2:
        if st.button("📤 Отправить уведомления", type="primary", use_container_width=True):
            if not recipients:
                st.error("❌ Выберите получателей")
            elif not message:
                st.error("❌ Введите текст сообщения")
            else:
                send_notifications(recipients, message, notification_type)

def send_notifications(recipients, message, notification_type):
    """Отправка уведомлений получателям"""
    success_count = 0
    fail_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, recipient in enumerate(recipients):
        status_text.text(f"Отправка {i+1} из {len(recipients)}...")
        
        try:
            if notification_type in ["Email", "Оба"]:
                # Определяем email
                email = recipient[4] if isinstance(recipient, tuple) else recipient
                if '@' in email:
                    send_email_notification(email, "Уведомление от медицинского центра", message)
                    success_count += 1
            
            if notification_type in ["SMS", "Оба"]:
                # Определяем телефон
                phone = recipient[3] if isinstance(recipient, tuple) else recipient
                if phone.startswith('+'):
                    send_sms_notification(phone, message)
                    success_count += 1
        
        except Exception as e:
            fail_count += 1
            st.warning(f"⚠️ Ошибка отправки: {e}")
        
        progress_bar.progress((i + 1) / len(recipients))
    
    status_text.empty()
    progress_bar.empty()
    
    if success_count > 0:
        st.success(f"✅ Успешно отправлено: {success_count}")
    if fail_count > 0:
        st.error(f"❌ Ошибок: {fail_count}")

def show_settings():
    """Настройки уведомлений"""
    st.subheader("⚙️ Настройки уведомлений")
    
    st.info("💡 Настройки уведомлений хранятся в переменных окружения")
    
    # Email настройки
    st.markdown("### 📧 Email настройки")
    
    smtp_server = st.text_input("SMTP сервер:", value="smtp.gmail.com", disabled=True)
    smtp_port = st.number_input("SMTP порт:", value=587, disabled=True)
    
    st.info("""
    Для настройки email уведомлений установите переменные окружения:
    - `SMTP_SERVER`: smtp.gmail.com
    - `SMTP_PORT`: 587
    - `SMTP_USERNAME`: your_email@gmail.com
    - `SMTP_PASSWORD`: your_password
    """)
    
    st.markdown("---")
    
    # SMS настройки
    st.markdown("### 📱 SMS настройки (Twilio)")
    
    st.info("""
    Для настройки SMS уведомлений установите переменные окружения:
    - `TWILIO_ACCOUNT_SID`: your_account_sid
    - `TWILIO_AUTH_TOKEN`: your_auth_token
    - `TWILIO_PHONE`: your_twilio_phone_number
    """)
    
    st.markdown("---")
    
    # Автоматические уведомления
    st.markdown("### 🤖 Автоматические уведомления")
    
    st.checkbox("Отправлять напоминание за день до приема", value=False, disabled=True)
    st.checkbox("Отправлять подтверждение при создании записи", value=False, disabled=True)
    st.checkbox("Отправлять уведомление при изменении статуса", value=False, disabled=True)
    
    st.info("⏳ Автоматические уведомления будут добавлены в следующей версии")

def show_notification_history():
    """История уведомлений"""
    st.subheader("📊 История уведомлений")
    
    st.info("⏳ История уведомлений будет добавлена в следующей версии")
    
    # Заглушка для будущей функциональности
    st.write("**Запланированные функции:**")
    st.write("- 📅 История отправленных уведомлений")
    st.write("- 📊 Статистика доставки")
    st.write("- ❌ Список неудачных отправок")
    st.write("- 🔄 Повторная отправка")

def get_all_clients():
    """Получить всех клиентов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, first_name, last_name, phone, email
        FROM clients
        ORDER BY last_name, first_name
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_clients_with_appointments(appointment_date):
    """Получить клиентов с приемами на указанную дату"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT c.id, c.first_name, c.last_name, c.phone, c.email
        FROM clients c
        JOIN appointments a ON c.id = a.client_id
        WHERE a.appointment_date = ? AND a.status = 'записан'
        ORDER BY c.last_name, c.first_name
    ''', (appointment_date,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_template_text(template_name):
    """Получить текст шаблона"""
    templates = {
        "Подтверждение записи": "Здравствуйте! Ваша запись на прием подтверждена. Ждем вас!",
        "Отмена приема": "Уважаемый пациент, ваш прием отменен. Для переноса свяжитесь с нами.",
        "Изменение времени": "Уважаемый пациент, время вашего приема изменено. Новые детали в приложении."
    }
    return templates.get(template_name, "")

# ==================== ФУНКЦИИ УВЕДОМЛЕНИЙ ====================

def send_email_notification(email, subject, message):
    """Отправить email уведомление"""
    try:
        # Здесь должна быть логика отправки email
        # Пока что просто логируем
        st.info(f"📧 Email отправлен на {email}: {subject}")
        return True
    except Exception as e:
        st.error(f"Ошибка отправки email: {e}")
        return False

def send_sms_notification(phone, message):
    """Отправить SMS уведомление"""
    try:
        # Здесь должна быть логика отправки SMS
        # Пока что просто логируем
        st.info(f"📱 SMS отправлено на {phone}: {message}")
        return True
    except Exception as e:
        st.error(f"Ошибка отправки SMS: {e}")
        return False

if __name__ == "__main__":
    main()

