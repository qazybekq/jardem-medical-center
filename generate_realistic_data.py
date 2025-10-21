#!/usr/bin/env python3
"""
Генерация реалистичных данных для медицинского центра
1000 записей с повторными клиентами за последние 6 месяцев
"""

import random
from datetime import datetime, date, time, timedelta
from database import (
    get_connection, create_client, create_appointment, 
    get_all_doctors, get_all_services, add_service_to_appointment,
    update_appointment_status
)

# Казахские имена и фамилии
FIRST_NAMES_MALE = [
    'Асхат', 'Данияр', 'Ерлан', 'Марат', 'Нурлан', 'Олжас', 'Рустем', 'Серик',
    'Талгат', 'Айдар', 'Бекзат', 'Ержан', 'Жанибек', 'Кайрат', 'Мурат', 'Санжар',
    'Тимур', 'Шынгыс', 'Алмас', 'Батыр', 'Галымжан', 'Дулат', 'Есен', 'Женис'
]

FIRST_NAMES_FEMALE = [
    'Айгуль', 'Айжан', 'Айша', 'Гульнара', 'Динара', 'Жанар', 'Жанна', 'Зарина',
    'Камила', 'Лаура', 'Мадина', 'Назира', 'Сауле', 'Толганай', 'Алия', 'Балжан',
    'Гульмира', 'Дарига', 'Елена', 'Жансая', 'Индира', 'Куралай', 'Ляззат', 'Меруерт'
]

LAST_NAMES = [
    'Нурланов', 'Ахметов', 'Калиев', 'Сериков', 'Тулеуов', 'Ибрагимов', 'Сейтжанов',
    'Куанов', 'Жумабаев', 'Оспанов', 'Касымов', 'Байбосынов', 'Алибеков', 'Мухамбетов',
    'Абдуллаев', 'Есенов', 'Бекенов', 'Токаев', 'Смагулов', 'Жакупов', 'Асанов',
    'Садыков', 'Турсунов', 'Мамбетов', 'Рахимов', 'Сабиров', 'Темиров', 'Умаров'
]

def generate_phone():
    """Генерация уникального казахстанского телефона"""
    return f"+7 {random.randint(700, 799)} {random.randint(100, 999)} {random.randint(1000, 9999)}"

def generate_email(first_name, last_name):
    """Генерация email"""
    domains = ['gmail.com', 'mail.ru', 'yandex.kz', 'inbox.ru', 'bk.ru']
    name = first_name.lower()
    surname = last_name.lower()
    patterns = [
        f"{name}.{surname}@{random.choice(domains)}",
        f"{name}{random.randint(1, 99)}@{random.choice(domains)}",
        f"{surname}.{name}@{random.choice(domains)}",
        f"{name}_{surname}@{random.choice(domains)}"
    ]
    return random.choice(patterns)

def generate_birth_date():
    """Генерация даты рождения (18-80 лет)"""
    years_ago = random.randint(18, 80)
    today = date.today()
    birth_year = today.year - years_ago
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)  # Безопасно для всех месяцев
    return date(birth_year, birth_month, birth_day)

def generate_appointment_datetime(start_date):
    """Генерация даты и времени приема"""
    # Генерируем дату в пределах последних 6 месяцев от start_date
    days_ago = random.randint(0, 180)
    appointment_date = start_date - timedelta(days=days_ago)
    
    # Только рабочие часы: 9:00 - 18:00, с шагом 15 минут
    hour = random.randint(9, 17)
    minute = random.choice([0, 15, 30, 45])
    appointment_time = time(hour, minute, 0)
    
    return appointment_date, appointment_time

def generate_status(appointment_date):
    """Генерация статуса приема в зависимости от даты"""
    today = date.today()
    
    if appointment_date > today:
        # Будущие приемы - только "записан"
        return 'записан'
    elif appointment_date == today:
        # Сегодняшние - могут быть разные
        return random.choices(
            ['записан', 'на приеме', 'прием завершен', 'не явился'],
            weights=[40, 30, 20, 10]
        )[0]
    else:
        # Прошлые приемы
        return random.choices(
            ['прием завершен', 'не явился'],
            weights=[85, 15]
        )[0]

def main():
    """Главная функция генерации данных"""
    print("🚀 Начинаем генерацию реалистичных данных...")
    print("=" * 60)
    
    # Получаем существующих врачей и услуги
    doctors = get_all_doctors()
    all_services = get_all_services()
    
    if not doctors or not all_services:
        print("❌ Ошибка: Нет врачей или услуг в базе данных!")
        return
    
    print(f"✅ Найдено {len(doctors)} врачей")
    print(f"✅ Найдено {len(all_services)} услуг")
    print()
    
    # Генерация клиентов (300 уникальных клиентов)
    print("👥 Генерация клиентов...")
    clients = []
    used_phones = set()
    
    # Получаем существующие телефоны из БД
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT phone FROM clients')
    existing_phones = {row[0] for row in cursor.fetchall()}
    conn.close()
    used_phones.update(existing_phones)
    
    created_count = 0
    attempts = 0
    max_attempts = 500
    
    while created_count < 300 and attempts < max_attempts:
        attempts += 1
        
        # Случайный пол для разнообразия
        gender = random.choice(['male', 'female'])
        
        if gender == 'male':
            first_name = random.choice(FIRST_NAMES_MALE)
        else:
            first_name = random.choice(FIRST_NAMES_FEMALE)
        
        last_name = random.choice(LAST_NAMES)
        if gender == 'female' and not last_name.endswith('а'):
            last_name += 'а'  # Женская форма фамилии
        
        birth_date = generate_birth_date()
        
        # Генерируем уникальный телефон
        phone = generate_phone()
        retries = 0
        while phone in used_phones and retries < 50:
            phone = generate_phone()
            retries += 1
        
        if phone in used_phones:
            continue
            
        used_phones.add(phone)
        
        email = generate_email(first_name, last_name) if random.random() > 0.2 else None
        
        client_id = create_client(first_name, last_name, birth_date, phone, email)
        
        if client_id:
            clients.append(client_id)
            created_count += 1
            if created_count % 50 == 0:
                print(f"  ✓ Создано {created_count} клиентов...")
    
    print(f"✅ Всего создано клиентов: {len(clients)}")
    print()
    
    # Генерация приемов (1000 записей)
    print("📅 Генерация приемов...")
    
    today = date.today()
    appointments_created = 0
    appointments_failed = 0
    
    # Некоторые клиенты будут повторными (30% клиентов приходят 2-5 раз)
    repeat_clients = random.sample(clients, int(len(clients) * 0.3))
    repeat_counts = {client_id: random.randint(2, 5) for client_id in repeat_clients}
    
    # Распределяем приемы
    target_appointments = 1000
    appointments_to_create = []
    
    # Повторные клиенты
    for client_id, count in repeat_counts.items():
        for _ in range(count):
            appointments_to_create.append(client_id)
    
    # Остальные - новые клиенты (по одному приему)
    remaining = target_appointments - len(appointments_to_create)
    single_visit_clients = [c for c in clients if c not in repeat_clients]
    appointments_to_create.extend(random.choices(single_visit_clients, k=remaining))
    
    # Перемешиваем
    random.shuffle(appointments_to_create)
    
    # Создаем приемы
    for i, client_id in enumerate(appointments_to_create):
        appointment_date, appointment_time = generate_appointment_datetime(today)
        
        # Выбираем случайного врача
        doctor = random.choice(doctors)
        doctor_id = doctor[0]
        
        # Выбираем услуги этого врача
        doctor_services = [s for s in all_services if s[5] == doctor[1] and s[6] == doctor[2]]
        
        if not doctor_services:
            # Если у врача нет услуг, берем любую
            service = random.choice(all_services)
        else:
            service = random.choice(doctor_services)
        
        service_id = service[0]
        service_price = service[3]
        
        # Генерируем заметки (иногда)
        notes = None
        if random.random() < 0.3:
            notes_options = [
                "Первичный прием",
                "Повторный прием",
                "Жалобы на боли",
                "Профилактический осмотр",
                "Консультация по результатам анализов",
                "Направление от терапевта"
            ]
            notes = random.choice(notes_options)
        
        # Создаем прием (теперь service_id обрабатывается внутри create_appointment)
        try:
            appointment_id = create_appointment(
                client_id, doctor_id, service_id,
                appointment_date, appointment_time, notes,
                skip_date_validation=True  # Разрешаем исторические даты для тестовых данных
            )
            
            if not appointment_id:
                # Логируем первые 5 неудачных попыток для отладки
                if appointments_failed < 5:
                    print(f"  ⚠️ Прием #{i+1} не создан: client={client_id}, doctor={doctor_id}, service={service_id}, date={appointment_date}, time={appointment_time}")
        except Exception as e:
            print(f"  ⚠️ Ошибка создания приема #{i+1}: {e}")
            appointment_id = None
        
        if appointment_id:
            appointments_created += 1
            
            # Устанавливаем статус
            status = generate_status(appointment_date)
            
            # Если прием завершен, добавляем время начала и окончания
            if status == 'прием завершен':
                start_time = datetime.combine(appointment_date, appointment_time)
                duration = random.randint(15, 60)  # 15-60 минут
                end_time = start_time + timedelta(minutes=duration)
                
                update_appointment_status(
                    appointment_id, status,
                    start_time.isoformat(),
                    end_time.isoformat()
                )
            elif status in ['на приеме', 'не явился']:
                update_appointment_status(appointment_id, status)
            
            # Иногда добавляем дополнительные услуги (15% приемов)
            if random.random() < 0.15:
                additional_services = random.sample(
                    [s for s in all_services if s[0] != service_id],
                    random.randint(1, 2)
                )
                for add_service in additional_services:
                    add_service_to_appointment(
                        appointment_id,
                        add_service[0],
                        add_service[3]
                    )
            
            if (i + 1) % 100 == 0:
                print(f"  ✓ Создано {i + 1} приемов...")
        else:
            appointments_failed += 1
    
    print(f"✅ Всего создано приемов: {appointments_created}")
    if appointments_failed > 0:
        print(f"⚠️ Ошибок при создании: {appointments_failed}")
    
    print()
    print("=" * 60)
    print("🎉 Генерация данных завершена!")
    print()
    print("📊 Итоговая статистика:")
    print(f"  • Клиентов: {len(clients)}")
    print(f"  • Приемов: {appointments_created}")
    print(f"  • Повторных клиентов: {len(repeat_clients)}")
    print(f"  • Период: последние 6 месяцев от {today}")
    print()
    print("✅ Данные готовы для тестирования!")

if __name__ == "__main__":
    main()

