# 📱 ПЛАН ИНТЕГРАЦИИ WHATSAPP API

## 📋 **ОТВЕТ НА ВОПРОС О WHATSAPP API**

### ✅ **ДА, МОЖНО ИНТЕГРИРОВАТЬ WHATSAPP API!**

**Возможности интеграции:**
- ✅ Отправка автоматических уведомлений пациентам
- ✅ Массовые рассылки о скидках и акциях
- ✅ Поздравления с праздниками
- ✅ Напоминания о приемах
- ✅ Автоматические сообщения через scheduler

## 🔧 **ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ**

### **1. WhatsApp Business API (Meta Cloud API)**
```python
# Пример интеграции с WhatsApp Business API
import requests
import json
from datetime import datetime, timedelta
import schedule
import time

class WhatsAppNotifier:
    def __init__(self, access_token, phone_number_id):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def send_message(self, to_phone, message):
        """Отправка сообщения через WhatsApp API"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    
    def send_template_message(self, to_phone, template_name, parameters):
        """Отправка шаблонного сообщения"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "ru"},
                "components": [
                    {
                        "type": "body",
                        "parameters": parameters
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
```

### **2. Автоматические уведомления через Scheduler**
```python
import schedule
import time
from database import get_connection, search_clients

def send_appointment_reminders():
    """Отправка напоминаний о приемах"""
    # Получаем приемы на завтра
    tomorrow = datetime.now() + timedelta(days=1)
    appointments = get_appointments_by_date(tomorrow.date())
    
    for appointment in appointments:
        client_phone = appointment['phone']
        client_name = appointment['first_name']
        doctor_name = appointment['doctor_name']
        appointment_time = appointment['appointment_time']
        
        message = f"""
🏥 Напоминание о приеме
        
Здравствуйте, {client_name}!

Напоминаем, что завтра у вас запланирован прием:
👨‍⚕️ Врач: {doctor_name}
⏰ Время: {appointment_time}

Ждем вас в медицинском центре!
        """
        
        whatsapp.send_message(client_phone, message)

def send_birthday_greetings():
    """Отправка поздравлений с днем рождения"""
    today = datetime.now().date()
    
    # Получаем клиентов с днем рождения сегодня
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT first_name, phone FROM clients 
        WHERE DATE_FORMAT(birth_date, '%m-%d') = DATE_FORMAT(?, '%m-%d')
    """, (today,))
    
    birthday_clients = cursor.fetchall()
    
    for client in birthday_clients:
        message = f"""
🎉 С Днем Рождения!

Дорогой(ая) {client[0]}!

От всей души поздравляем вас с днем рождения! 
Желаем крепкого здоровья и благополучия!

С уважением,
Команда медицинского центра
        """
        
        whatsapp.send_message(client[1], message)

def send_promotional_messages():
    """Отправка рекламных сообщений"""
    # Получаем всех активных клиентов
    clients = search_clients("")
    
    promotional_message = """
🎯 Специальное предложение!

Дорогие пациенты!

В этом месяце действует скидка 20% на:
• Профилактический осмотр
• Консультацию специалиста
• Диагностические процедуры

Записывайтесь на прием и экономьте на здоровье!

📞 Телефон: +7 (XXX) XXX-XX-XX
🌐 Сайт: www.medical-center.com
    """
    
    for client in clients:
        if client[5]:  # Если есть телефон
            whatsapp.send_message(client[5], promotional_message)

# Настройка автоматических задач
schedule.every().day.at("09:00").do(send_appointment_reminders)
schedule.every().day.at("10:00").do(send_birthday_greetings)
schedule.every().monday.at("11:00").do(send_promotional_messages)

# Запуск планировщика
while True:
    schedule.run_pending()
    time.sleep(60)
```

## 📱 **ТИПЫ СООБЩЕНИЙ**

### **1. Напоминания о приемах**
- За 24 часа до приема
- За 2 часа до приема
- Персональные сообщения с именем врача и временем

### **2. Поздравления с праздниками**
- День рождения пациента
- Новый год, 8 марта, 23 февраля
- Медицинские праздники

### **3. Рекламные сообщения**
- Информация о скидках
- Новые услуги клиники
- Специальные предложения
- Акции и промо

### **4. Автоматические уведомления**
- Подтверждение записи
- Отмена приема
- Изменение времени приема
- Результаты анализов

## 🔧 **ИНТЕГРАЦИЯ В СИСТЕМУ**

### **1. Обновление notification_manager.py**
```python
def send_whatsapp_notification(phone, message, template_name=None):
    """Отправка WhatsApp уведомления"""
    try:
        whatsapp = WhatsAppNotifier(
            access_token=st.secrets["WHATSAPP_ACCESS_TOKEN"],
            phone_number_id=st.secrets["WHATSAPP_PHONE_NUMBER_ID"]
        )
        
        if template_name:
            result = whatsapp.send_template_message(phone, template_name, [message])
        else:
            result = whatsapp.send_message(phone, message)
        
        return result
    except Exception as e:
        st.error(f"Ошибка отправки WhatsApp: {e}")
        return None
```

### **2. Добавление в Streamlit Secrets**
```toml
# .streamlit/secrets.toml
WHATSAPP_ACCESS_TOKEN = "your_access_token_here"
WHATSAPP_PHONE_NUMBER_ID = "your_phone_number_id_here"
WHATSAPP_VERIFY_TOKEN = "your_verify_token_here"
```

## 💰 **СТОИМОСТЬ И ОГРАНИЧЕНИЯ**

### **WhatsApp Business API:**
- **Бесплатные сообщения**: 1000 в месяц
- **Платные сообщения**: ~$0.005 за сообщение
- **Шаблонные сообщения**: Требуют одобрения Meta
- **Скорость отправки**: До 1000 сообщений в секунду

### **Ограничения:**
- Только к клиентам, которые инициировали диалог
- Шаблонные сообщения для массовых рассылок
- Соблюдение политики WhatsApp

## 🚀 **ПЛАН ВНЕДРЕНИЯ**

### **Этап 1: Подготовка**
1. Регистрация в Meta for Developers
2. Создание WhatsApp Business аккаунта
3. Получение токенов доступа

### **Этап 2: Разработка**
1. Интеграция WhatsApp API в систему
2. Создание шаблонов сообщений
3. Настройка автоматических задач

### **Этап 3: Тестирование**
1. Тестирование на ограниченной группе клиентов
2. Проверка доставки сообщений
3. Настройка обработки ошибок

### **Этап 4: Запуск**
1. Постепенное увеличение объема рассылок
2. Мониторинг эффективности
3. Оптимизация сообщений

## 📊 **ПРЕИМУЩЕСТВА**

### **Для клиники:**
- ✅ Автоматизация коммуникации
- ✅ Снижение количества неявок
- ✅ Увеличение лояльности клиентов
- ✅ Эффективный маркетинг

### **Для пациентов:**
- ✅ Удобные напоминания
- ✅ Персональные поздравления
- ✅ Информация о скидках
- ✅ Быстрая связь с клиникой

---
**Вывод**: Интеграция WhatsApp API полностью возможна и рекомендуется для повышения эффективности работы медицинского центра!
