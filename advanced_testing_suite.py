#!/usr/bin/env python3
"""
Комплексная система автотестирования для Jardem Medical Center
Создано: Senior QA Engineer
"""

import unittest
import sqlite3
import os
import sys
from datetime import datetime, date, timedelta
import tempfile
import shutil

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_database, get_connection, create_client, create_doctor, 
    create_service, create_appointment, search_clients, get_all_doctors,
    get_all_services, get_appointments_by_date_range, authenticate_user,
    create_user, update_user_password, delete_user, log_audit_action
)
from validators import validate_phone, validate_email, validate_date

class TestJardemSystem(unittest.TestCase):
    """Комплексные тесты системы Jardem"""
    
    def setUp(self):
        """Настройка тестовой среды"""
        # Создаем временную базу данных
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Устанавливаем тестовую БД
        os.environ['TEST_DB_PATH'] = self.test_db.name
        
        # Инициализируем тестовую БД
        init_database()
        
        # Создаем тестовых пользователей
        self.create_test_users()
    
    def tearDown(self):
        """Очистка после тестов"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def create_test_users(self):
        """Создание тестовых пользователей"""
        test_users = [
            ('test_owner', 'password123', 'Test Owner', 'owner'),
            ('test_admin', 'password123', 'Test Admin', 'admin'),
            ('test_crm', 'password123', 'Test CRM', 'crm')
        ]
        
        for username, password, name, access_level in test_users:
            try:
                create_user(username, password, access_level)
            except:
                pass  # Пользователь уже существует
    
    # ==================== ТЕСТЫ АУТЕНТИФИКАЦИИ ====================
    
    def test_successful_login(self):
        """Тест успешного входа в систему"""
        result = authenticate_user('test_owner', 'password123')
        self.assertTrue(result, "Успешный вход должен возвращать True")
    
    def test_failed_login_wrong_password(self):
        """Тест неудачного входа с неверным паролем"""
        result = authenticate_user('test_owner', 'wrong_password')
        self.assertFalse(result, "Неверный пароль должен возвращать False")
    
    def test_failed_login_wrong_username(self):
        """Тест неудачного входа с неверным именем пользователя"""
        result = authenticate_user('nonexistent_user', 'password123')
        self.assertFalse(result, "Несуществующий пользователь должен возвращать False")
    
    def test_failed_login_empty_credentials(self):
        """Тест неудачного входа с пустыми данными"""
        result = authenticate_user('', '')
        self.assertFalse(result, "Пустые данные должны возвращать False")
    
    # ==================== ТЕСТЫ ВАЛИДАЦИИ ====================
    
    def test_phone_validation_valid_formats(self):
        """Тест валидации телефонов с валидными форматами"""
        valid_phones = [
            '7011234567',  # 7XXXXXXXXXX
            '87011234567', # 8XXXXXXXXXX
            '+77011234567' # +7XXXXXXXXXX
        ]
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                result = validate_phone(phone)
                self.assertTrue(result.startswith('7'), f"Телефон {phone} должен начинаться с 7")
    
    def test_phone_validation_invalid_formats(self):
        """Тест валидации телефонов с невалидными форматами"""
        invalid_phones = [
            '123456789',   # Слишком короткий
            '701123456789', # Слишком длинный
            'abc1234567',  # Содержит буквы
            '701-123-4567', # Содержит дефисы
            ''             # Пустой
        ]
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                with self.assertRaises(Exception, msg=f"Телефон {phone} должен вызывать исключение"):
                    validate_phone(phone)
    
    def test_email_validation(self):
        """Тест валидации email адресов"""
        # Валидные email
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'test+tag@example.org'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                result = validate_email(email)
                self.assertEqual(result, email, f"Email {email} должен быть валидным")
        
        # Невалидные email
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'test@',
            'test..test@example.com'
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                with self.assertRaises(Exception, msg=f"Email {email} должен вызывать исключение"):
                    validate_email(email)
    
    # ==================== ТЕСТЫ CRUD ОПЕРАЦИЙ ====================
    
    def test_create_client_success(self):
        """Тест успешного создания клиента"""
        client_id = create_client(
            'Иван', 'Иванов', date(1990, 1, 1), 
            '7011234567', 'ivan@example.com'
        )
        self.assertIsNotNone(client_id, "ID клиента должен быть создан")
        self.assertIsInstance(client_id, int, "ID должен быть числом")
    
    def test_create_client_duplicate_phone(self):
        """Тест создания клиента с дублирующимся телефоном"""
        # Создаем первого клиента
        create_client('Иван', 'Иванов', date(1990, 1, 1), '7011234567')
        
        # Пытаемся создать второго с тем же телефоном
        with self.assertRaises(Exception, msg="Дублирующийся телефон должен вызывать исключение"):
            create_client('Петр', 'Петров', date(1990, 1, 1), '7011234567')
    
    def test_create_client_missing_required_fields(self):
        """Тест создания клиента без обязательных полей"""
        with self.assertRaises(Exception, msg="Отсутствие обязательных полей должно вызывать исключение"):
            create_client('', '', None, '', '')
    
    def test_search_clients(self):
        """Тест поиска клиентов"""
        # Создаем тестового клиента
        create_client('Анна', 'Петрова', date(1985, 5, 15), '7012345678')
        
        # Поиск по имени
        results = search_clients('Анна')
        self.assertGreater(len(results), 0, "Поиск должен найти клиента")
        
        # Поиск по фамилии
        results = search_clients('Петрова')
        self.assertGreater(len(results), 0, "Поиск должен найти клиента")
        
        # Поиск по телефону
        results = search_clients('7012345678')
        self.assertGreater(len(results), 0, "Поиск должен найти клиента")
    
    def test_create_doctor_success(self):
        """Тест успешного создания врача"""
        doctor_id = create_doctor(
            'Доктор', 'Смит', 'Терапевт', 
            '7012345678', 'doctor@example.com'
        )
        self.assertIsNotNone(doctor_id, "ID врача должен быть создан")
        self.assertIsInstance(doctor_id, int, "ID должен быть числом")
    
    def test_create_service_success(self):
        """Тест успешного создания услуги"""
        service_id = create_service(
            'Консультация', 'Первичная консультация врача', 
            5000.0, 30
        )
        self.assertIsNotNone(service_id, "ID услуги должен быть создан")
        self.assertIsInstance(service_id, int, "ID должен быть числом")
    
    def test_create_appointment_success(self):
        """Тест успешного создания приема"""
        # Создаем необходимые данные
        client_id = create_client('Пациент', 'Тест', date(1990, 1, 1), '7011111111')
        doctor_id = create_doctor('Врач', 'Тест', 'Терапевт', '7011111112')
        service_id = create_service('Услуга', 'Тестовая услуга', 1000.0, 30)
        
        appointment_id = create_appointment(
            client_id, doctor_id, service_id, 
            date.today(), '10:00:00', 'Тестовый прием'
        )
        self.assertIsNotNone(appointment_id, "ID приема должен быть создан")
        self.assertIsInstance(appointment_id, int, "ID должен быть числом")
    
    def test_create_appointment_time_conflict(self):
        """Тест создания приема с конфликтом времени"""
        # Создаем необходимые данные
        client_id = create_client('Пациент1', 'Тест1', date(1990, 1, 1), '7011111111')
        client_id2 = create_client('Пациент2', 'Тест2', date(1990, 1, 1), '7011111112')
        doctor_id = create_doctor('Врач', 'Тест', 'Терапевт', '7011111113')
        service_id = create_service('Услуга', 'Тестовая услуга', 1000.0, 30)
        
        # Создаем первый прием
        create_appointment(client_id, doctor_id, service_id, date.today(), '10:00:00')
        
        # Пытаемся создать второй прием в то же время
        with self.assertRaises(Exception, msg="Конфликт времени должен вызывать исключение"):
            create_appointment(client_id2, doctor_id, service_id, date.today(), '10:00:00')
    
    # ==================== ТЕСТЫ АНАЛИТИКИ ====================
    
    def test_get_appointments_by_date_range(self):
        """Тест получения приемов по диапазону дат"""
        # Создаем тестовые данные
        client_id = create_client('Аналитика', 'Тест', date(1990, 1, 1), '7012222222')
        doctor_id = create_doctor('Аналитика', 'Врач', 'Терапевт', '7012222223')
        service_id = create_service('Аналитика', 'Тестовая услуга', 2000.0, 30)
        
        # Создаем приемы на разные даты
        create_appointment(client_id, doctor_id, service_id, date.today(), '09:00:00')
        create_appointment(client_id, doctor_id, service_id, date.today() + timedelta(days=1), '10:00:00')
        
        # Получаем приемы за сегодня
        appointments = get_appointments_by_date_range(date.today(), date.today())
        self.assertGreaterEqual(len(appointments), 1, "Должен быть хотя бы один прием за сегодня")
    
    # ==================== ТЕСТЫ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ ====================
    
    def test_create_user_success(self):
        """Тест успешного создания пользователя"""
        user_id = create_user('new_user', 'password123', 'crm')
        self.assertIsNotNone(user_id, "ID пользователя должен быть создан")
    
    def test_create_user_duplicate_username(self):
        """Тест создания пользователя с дублирующимся именем"""
        create_user('duplicate_user', 'password123', 'crm')
        
        with self.assertRaises(Exception, msg="Дублирующееся имя пользователя должно вызывать исключение"):
            create_user('duplicate_user', 'password123', 'crm')
    
    def test_update_user_password(self):
        """Тест обновления пароля пользователя"""
        create_user('password_test', 'old_password', 'crm')
        
        # Обновляем пароль
        result = update_user_password('password_test', 'new_password')
        self.assertTrue(result, "Обновление пароля должно быть успешным")
        
        # Проверяем, что новый пароль работает
        auth_result = authenticate_user('password_test', 'new_password')
        self.assertTrue(auth_result, "Новый пароль должен работать")
    
    def test_delete_user(self):
        """Тест удаления пользователя"""
        create_user('delete_test', 'password123', 'crm')
        
        # Удаляем пользователя
        result = delete_user('delete_test')
        self.assertTrue(result, "Удаление пользователя должно быть успешным")
        
        # Проверяем, что пользователь не может войти
        auth_result = authenticate_user('delete_test', 'password123')
        self.assertFalse(auth_result, "Удаленный пользователь не должен входить в систему")
    
    # ==================== ТЕСТЫ АУДИТА ====================
    
    def test_audit_logging(self):
        """Тест логирования аудита"""
        # Создаем пользователя для аудита
        user_id = create_user('audit_test', 'password123', 'crm')
        
        # Выполняем действие, которое должно логироваться
        log_audit_action(user_id, 'TEST_ACTION', 'test_table', 1, 'old_value', 'new_value')
        
        # Проверяем, что запись в аудите создана
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM audit_log WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertGreater(count, 0, "Должна быть создана запись в аудите")
    
    # ==================== ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ====================
    
    def test_database_performance(self):
        """Тест производительности базы данных"""
        import time
        
        # Создаем много записей
        start_time = time.time()
        
        for i in range(100):
            create_client(f'Тест{i}', f'Фамилия{i}', date(1990, 1, 1), f'701{i:07d}')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Проверяем, что создание 100 записей занимает менее 5 секунд
        self.assertLess(execution_time, 5.0, f"Создание 100 записей заняло {execution_time:.2f} секунд")
    
    # ==================== ТЕСТЫ БЕЗОПАСНОСТИ ====================
    
    def test_sql_injection_protection(self):
        """Тест защиты от SQL-инъекций"""
        malicious_input = "'; DROP TABLE clients; --"
        
        # Попытка SQL-инъекции должна вызывать исключение валидации
        with self.assertRaises(Exception, msg="SQL-инъекция должна блокироваться валидацией"):
            search_clients(malicious_input)
    
    def test_password_hashing(self):
        """Тест хеширования паролей"""
        import bcrypt
        
        # Создаем пользователя
        create_user('hash_test', 'plain_password', 'crm')
        
        # Проверяем, что пароль захеширован
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', ('hash_test',))
        password_hash = cursor.fetchone()[0]
        conn.close()
        
        # Пароль должен быть захеширован (не равен исходному)
        self.assertNotEqual(password_hash, 'plain_password', "Пароль должен быть захеширован")
        
        # Проверяем, что хеш работает с bcrypt
        self.assertTrue(bcrypt.checkpw('plain_password'.encode('utf-8'), password_hash.encode('utf-8')), 
                       "Хешированный пароль должен проверяться корректно")

class TestEdgeCases(unittest.TestCase):
    """Тесты граничных случаев"""
    
    def setUp(self):
        """Настройка тестовой среды"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        os.environ['TEST_DB_PATH'] = self.test_db.name
        init_database()
    
    def tearDown(self):
        """Очистка после тестов"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_empty_database_queries(self):
        """Тест запросов к пустой базе данных"""
        # Поиск в пустой базе
        results = search_clients('')
        self.assertEqual(len(results), 0, "Поиск в пустой базе должен возвращать пустой список")
        
        # Получение врачей из пустой базы
        doctors = get_all_doctors()
        self.assertEqual(len(doctors), 0, "Пустая база должна возвращать пустой список врачей")
    
    def test_boundary_dates(self):
        """Тест граничных дат"""
        # Очень старая дата
        old_date = date(1900, 1, 1)
        client_id = create_client('Старый', 'Пациент', old_date, '7010000000')
        self.assertIsNotNone(client_id, "Должна поддерживаться старая дата")
        
        # Будущая дата
        future_date = date(2030, 12, 31)
        client_id = create_client('Будущий', 'Пациент', future_date, '7010000001')
        self.assertIsNotNone(client_id, "Должна поддерживаться будущая дата")
    
    def test_unicode_characters(self):
        """Тест Unicode символов"""
        unicode_name = 'Анна-Мария José'
        client_id = create_client(unicode_name, 'Фамилия', date(1990, 1, 1), '7010000002')
        self.assertIsNotNone(client_id, "Должны поддерживаться Unicode символы")
    
    def test_very_long_strings(self):
        """Тест очень длинных строк"""
        long_name = 'A' * 1000  # 1000 символов
        client_id = create_client(long_name, 'Фамилия', date(1990, 1, 1), '7010000003')
        self.assertIsNotNone(client_id, "Должны поддерживаться длинные строки")

def run_comprehensive_tests():
    """Запуск всех тестов"""
    print("🧪 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ JARDEM")
    print("=" * 60)
    
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestJardemSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Провалено: {len(result.failures)}")
    print(f"💥 Ошибки: {len(result.errors)}")
    print(f"📈 Успешность: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ ПРОВАЛЕННЫЕ ТЕСТЫ:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ОШИБКИ:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result

if __name__ == "__main__":
    run_comprehensive_tests()
