import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import requests
import os

class NotificationManager:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.getenv("NOTIFICATION_EMAIL", "your-email@gmail.com")
        self.password = os.getenv("NOTIFICATION_PASSWORD", "your-app-password")
        self.sms_api_key = os.getenv("SMS_API_KEY", "")
        self.sms_api_url = "https://api.sms.ru/sms/send"
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Отправка email уведомления"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            
            text = msg.as_string()
            server.sendmail(self.email, to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            st.error(f"Ошибка отправки email: {str(e)}")
            return False
    
    def send_sms(self, phone: str, message: str) -> bool:
        """Отправка SMS уведомления"""
        try:
            if not self.sms_api_key:
                st.warning("SMS API ключ не настроен")
                return False
            
            # Очищаем номер телефона
            clean_phone = ''.join(filter(str.isdigit, phone))
            if clean_phone.startswith('7'):
                clean_phone = clean_phone[1:]
            if not clean_phone.startswith('7'):
                clean_phone = '7' + clean_phone
            
            data = {
                'api_id': self.sms_api_key,
                'to': clean_phone,
                'msg': message,
                'json': 1
            }
            
            response = requests.post(self.sms_api_url, data=data)
            result = response.json()
            
            if result.get('status') == 'OK':
                return True
            else:
                st.error(f"Ошибка отправки SMS: {result.get('status_text', 'Неизвестная ошибка')}")
                return False
                
        except Exception as e:
            st.error(f"Ошибка отправки SMS: {str(e)}")
            return False
    
    def send_appointment_reminder(self, patient_data: dict) -> bool:
        """Отправка напоминания о записи"""
        try:
            # Формируем сообщение
            subject = f"Напоминание о записи - {patient_data['date_visit']}"
            body = f"""
Добрый день, {patient_data['full_name']}!

Напоминаем о Вашей записи:
📅 Дата: {patient_data['date_visit']}
⏰ Время: {patient_data['appointment_time']}
👨‍⚕️ Врач: {patient_data['doctor_name']}
🏥 Услуга: {patient_data['service']}

Пожалуйста, приходите за 10 минут до назначенного времени.

С уважением,
Медицинский Центр
            """
            
            # Отправляем email если есть
            email_sent = False
            if patient_data.get('email'):
                email_sent = self.send_email(patient_data['email'], subject, body)
            
            # Отправляем SMS
            sms_sent = False
            if patient_data.get('phone'):
                sms_message = f"Напоминание: запись на {patient_data['date_visit']} в {patient_data['appointment_time']} к {patient_data['doctor_name']}"
                sms_sent = self.send_sms(patient_data['phone'], sms_message)
            
            return email_sent or sms_sent
            
        except Exception as e:
            st.error(f"Ошибка отправки напоминания: {str(e)}")
            return False
    
    def send_appointment_confirmation(self, patient_data: dict) -> bool:
        """Отправка подтверждения записи"""
        try:
            subject = f"Подтверждение записи - {patient_data['date_visit']}"
            body = f"""
Добрый день, {patient_data['full_name']}!

Ваша запись подтверждена:
📅 Дата: {patient_data['date_visit']}
⏰ Время: {patient_data['appointment_time']}
👨‍⚕️ Врач: {patient_data['doctor_name']}
🏥 Услуга: {patient_data['service']}
💰 Стоимость: {patient_data.get('service_cost', 0)} ₸

Пожалуйста, приходите за 10 минут до назначенного времени.

С уважением,
Медицинский Центр
            """
            
            # Отправляем email если есть
            email_sent = False
            if patient_data.get('email'):
                email_sent = self.send_email(patient_data['email'], subject, body)
            
            # Отправляем SMS
            sms_sent = False
            if patient_data.get('phone'):
                sms_message = f"Запись подтверждена: {patient_data['date_visit']} в {patient_data['appointment_time']} к {patient_data['doctor_name']}"
                sms_sent = self.send_sms(patient_data['phone'], sms_message)
            
            return email_sent or sms_sent
            
        except Exception as e:
            st.error(f"Ошибка отправки подтверждения: {str(e)}")
            return False
    
    def send_daily_reminders(self):
        """Отправка ежедневных напоминаний"""
        try:
            db = get_database()
            df = db.get_all_patients()
            
            if df.empty:
                return
            
            # Получаем записи на завтра
            tomorrow = datetime.now().date() + timedelta(days=1)
            tomorrow_appointments = df[df['date_visit'].dt.date == tomorrow]
            
            sent_count = 0
            for _, appointment in tomorrow_appointments.iterrows():
                patient_data = {
                    'full_name': appointment['full_name'],
                    'email': appointment.get('email', ''),
                    'phone': appointment['phone'],
                    'date_visit': appointment['date_visit'].strftime('%d.%m.%Y'),
                    'appointment_time': appointment['appointment_time'],
                    'doctor_name': appointment['doctor_name'],
                    'service': appointment['service'],
                    'service_cost': appointment.get('service_cost', 0)
                }
                
                if self.send_appointment_reminder(patient_data):
                    sent_count += 1
            
            return sent_count
            
        except Exception as e:
            st.error(f"Ошибка отправки ежедневных напоминаний: {str(e)}")
            return 0

def show_notification_settings():
    """Показать настройки уведомлений"""
    st.subheader("📧 Настройки уведомлений")
    
    # Настройки email
    st.subheader("📧 Email настройки")
    
    col1, col2 = st.columns(2)
    
    with col1:
        email_enabled = st.checkbox("Включить email уведомления", value=True)
        email_address = st.text_input("Email для уведомлений", value="admin@medical-center.com")
    
    with col2:
        smtp_server = st.text_input("SMTP сервер", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP порт", value=587)
    
    # Настройки SMS
    st.subheader("📱 SMS настройки")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sms_enabled = st.checkbox("Включить SMS уведомления", value=False)
        sms_api_key = st.text_input("SMS API ключ", type="password")
    
    with col2:
        sms_provider = st.selectbox("SMS провайдер", ["sms.ru", "smsc.ru", "smsaero.ru"])
    
    # Настройки времени
    st.subheader("⏰ Настройки времени")
    
    col1, col2 = st.columns(2)
    
    with col1:
        reminder_hours = st.number_input("За сколько часов напоминать", value=24, min_value=1, max_value=168)
        daily_reminder_time = st.time_input("Время ежедневных напоминаний", value=datetime.now().time())
    
    with col2:
        confirmation_enabled = st.checkbox("Отправлять подтверждения", value=True)
        reminder_enabled = st.checkbox("Отправлять напоминания", value=True)
    
    # Кнопки действий
    st.subheader("🔧 Действия")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Тест email"):
            notification_manager = NotificationManager()
            if notification_manager.send_email(email_address, "Тест", "Это тестовое сообщение"):
                st.success("Email отправлен успешно!")
            else:
                st.error("Ошибка отправки email")
    
    with col2:
        if st.button("📱 Тест SMS"):
            phone = st.text_input("Номер телефона для теста", placeholder="+7 (777) 123-45-67")
            if phone:
                notification_manager = NotificationManager()
                if notification_manager.send_sms(phone, "Тестовое SMS сообщение"):
                    st.success("SMS отправлено успешно!")
                else:
                    st.error("Ошибка отправки SMS")
    
    with col3:
        if st.button("📅 Отправить напоминания"):
            notification_manager = NotificationManager()
            sent_count = notification_manager.send_daily_reminders()
            st.success(f"Отправлено напоминаний: {sent_count}")

def show_notification_log():
    """Показать лог уведомлений"""
    st.subheader("📋 Лог уведомлений")
    
    # Здесь можно добавить логику для отображения лога уведомлений
    # Пока что показываем заглушку
    st.info("Лог уведомлений будет реализован в следующих версиях")

# Глобальный экземпляр менеджера уведомлений
@st.cache_resource
def get_notification_manager():
    return NotificationManager()

# Функции-обертки для совместимости с notification_manager.py
def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """Отправить email уведомление"""
    manager = NotificationManager()
    return manager.send_email(to_email, subject, body)

def send_sms_notification(phone: str, message: str) -> bool:
    """Отправить SMS уведомление"""
    manager = NotificationManager()
    return manager.send_sms(phone, message)
