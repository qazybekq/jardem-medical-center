#!/usr/bin/env python3
"""
Генератор безопасных паролей для системы управления медицинским центром
"""

import secrets
import string
import os

def generate_secure_password(length=16):
    """Генерирует безопасный пароль заданной длины"""
    # Используем буквы, цифры и специальные символы
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Генерируем пароль с использованием криптографически стойкого генератора
    password = ''.join(secrets.choice(characters) for _ in range(length))
    
    return password

def main():
    """Основная функция"""
    print("🔐 ГЕНЕРАТОР БЕЗОПАСНЫХ ПАРОЛЕЙ")
    print("=" * 50)
    
    # Генерируем пароли для разных ролей
    owner_password = generate_secure_password(20)
    admin_password = generate_secure_password(18)
    crm_password = generate_secure_password(16)
    
    print(f"👑 Пароль владельца (OWNER): {owner_password}")
    print(f"👨‍💼 Пароль администратора (ADMIN): {admin_password}")
    print(f"👥 Пароль CRM менеджера (CRM): {crm_password}")
    
    print("\n" + "=" * 50)
    print("📋 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ:")
    print("=" * 50)
    
    print("\n1. 🏠 Для локальной разработки:")
    print("   Добавь эти пароли в файл .streamlit/secrets.toml:")
    print(f"""
[secrets]
OWNER_PASSWORD = "{owner_password}"
ADMIN_PASSWORD = "{admin_password}"
CRM_PASSWORD = "{crm_password}"
""")
    
    print("\n2. 🌐 Для деплоя в Streamlit Cloud:")
    print("   Добавь эти пароли в раздел 'Secrets' приложения:")
    print(f"""
OWNER_PASSWORD = "{owner_password}"
ADMIN_PASSWORD = "{admin_password}"
CRM_PASSWORD = "{crm_password}"
""")
    
    print("\n3. ⚠️  ВАЖНО:")
    print("   - Сохрани эти пароли в безопасном месте")
    print("   - НЕ коммить их в Git репозиторий")
    print("   - Используй разные пароли для разных окружений")
    
    print("\n4. 🔄 Для смены паролей:")
    print("   - Запусти этот скрипт снова")
    print("   - Обнови секреты в Streamlit Cloud")
    print("   - Перезапусти приложение")
    
    # Создаем файл с паролями (НЕ коммитим в Git!)
    passwords_file = "generated_passwords.txt"
    with open(passwords_file, "w", encoding="utf-8") as f:
        f.write("🔐 СГЕНЕРИРОВАННЫЕ ПАРОЛИ\n")
        f.write("=" * 50 + "\n")
        f.write(f"Дата генерации: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"OWNER_PASSWORD = \"{owner_password}\"\n")
        f.write(f"ADMIN_PASSWORD = \"{admin_password}\"\n")
        f.write(f"CRM_PASSWORD = \"{crm_password}\"\n")
        f.write("\n" + "=" * 50 + "\n")
        f.write("⚠️  ВАЖНО: НЕ КОММИТЬ ЭТОТ ФАЙЛ В GIT!\n")
        f.write("=" * 50 + "\n")
    
    print(f"\n💾 Пароли сохранены в файл: {passwords_file}")
    print("   (Этот файл добавлен в .gitignore)")
    
    # Добавляем файл в .gitignore если его там нет
    gitignore_file = ".gitignore"
    if os.path.exists(gitignore_file):
        with open(gitignore_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "generated_passwords.txt" not in content:
            with open(gitignore_file, "a", encoding="utf-8") as f:
                f.write("\n# Generated passwords\n")
                f.write("generated_passwords.txt\n")
            print("✅ Файл добавлен в .gitignore")
    
    print("\n🎉 Генерация завершена!")
    print("Теперь ты можешь безопасно деплоить приложение!")

if __name__ == "__main__":
    main()