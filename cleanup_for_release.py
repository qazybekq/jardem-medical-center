#!/usr/bin/env python3
"""
Скрипт очистки проекта для релиза
Удаляет временные файлы, отчеты разработки и другие ненужные файлы
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Очистка проекта для релиза"""
    print("🧹 ОЧИСТКА ПРОЕКТА ДЛЯ РЕЛИЗА")
    print("=" * 50)
    
    # Файлы для удаления
    files_to_remove = [
        # Отчеты разработки
        "BA_UX_CRUD_REPORT.md",
        "BUG_FIX_DUPLICATE_ELEMENTS.md", 
        "BUG_FIX_UI_AND_DATES.md",
        "BUG_FIX_UnboundLocalError.md",
        "BUSINESS_ANALYSIS_UX_AUDIT.md",
        "BUTTON_SIZE_FIX_v2.7.3.md",
        "CHANGELOG_v2.3.md",
        "CHANGELOG_v2.4.2.md",
        "CHANGELOG_v2.4.3.md",
        "CHANGELOG_v2.4.4_FINAL.md",
        "CHANGELOG_v2.7.2.md",
        "CHANGELOG_v2.7.md",
        "DATA_GENERATION_REPORT.md",
        "DELETE_FEATURE.md",
        "DEVELOPER_FINAL_FIXES.md",
        "DEVELOPER_FIXES_COLOR_CODING.md",
        "DEVELOPER_FIXES_REPORT.md",
        "DEVELOPER_FIXES_v2.4.1.md",
        "DEVELOPMENT_PLAN_CRUD_v3.0.md",
        "DEVELOPMENT_REPORT_STAGE1_v3.0.md",
        "EXCEL_IMPORT_GUIDE.md",
        "FINAL_COMPLETE_v2.4.2.md",
        "FINAL_CRUD_COMPLETE_v3.2.0.md",
        "FINAL_DEVELOPER_REPORT_v2.6.md",
        "FINAL_HANDOFF_TO_QA.md",
        "FINAL_PROJECT_SUMMARY.md",
        "FINAL_QA_REPORT.md",
        "FINAL_REPORT_COLOR_CODING_v2.4.md",
        "FINAL_REPORT_v2.4.1.md",
        "FINAL_REPORT_v2.4.3.md",
        "FINAL_REPORT_v2.4.4.md",
        "FINAL_STATUS_COMPLETE.md",
        "FINAL_STATUS.md",
        "OPTIMIZATION_REPORT.md",
        "PAYMENT_FIX_v2.7.1.md",
        "QA_CLICKABLE_CELLS_v2.4.3.md",
        "QA_COLOR_CODING_REPORT.md",
        "QA_COMPACT_CELLS_v2.4.5.md",
        "QA_COMPREHENSIVE_REPORT.md",
        "QA_FINAL_COLOR_v2.4.2.md",
        "QA_NEW_FEATURES_REPORT.md",
        "QA_PERFECT_CELLS_v2.4.4_FINAL.md",
        "QA_REPORT_COLORED_CELLS_v2.4.1.md",
        "QA_UNIFORM_CELLS_v2.4.4.md",
        "QUICK_FIXES_SUMMARY.md",
        "QUICK_START_SECURITY.md",
        "RESTORATION_REPORT.md",
        "SECURITY_FIXES_REPORT.md",
        "STAGE1_COMPLETE_v3.0.0.md",
        "STAGE2_COMPLETE_v3.1.0.md",
        "UX_IMPROVEMENT_REPORT.md",
        
        # Временные файлы
        "comprehensive_testing.py",
        "test_changes_v2.7.2.py",
        "generate_realistic_data.py",
        "create_excel_templates.py",
        "import_from_excel.py",
        "migrate_v2_7.py",
        "backup.py",
        "generate_secure_passwords.py",
        "generated_passwords.txt",
        
        # Старые файлы
        "env.example",
    ]
    
    # Директории для удаления
    dirs_to_remove = [
        "__pycache__",
        "tests",
        "backups",
    ]
    
    removed_files = 0
    removed_dirs = 0
    
    # Удаляем файлы
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Удален файл: {file}")
                removed_files += 1
            except Exception as e:
                print(f"❌ Ошибка удаления {file}: {e}")
        else:
            print(f"⚠️ Файл не найден: {file}")
    
    # Удаляем директории
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ Удалена директория: {dir_name}")
                removed_dirs += 1
            except Exception as e:
                print(f"❌ Ошибка удаления {dir_name}: {e}")
        else:
            print(f"⚠️ Директория не найдена: {dir_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТ ОЧИСТКИ:")
    print(f"✅ Удалено файлов: {removed_files}")
    print(f"✅ Удалено директорий: {removed_dirs}")
    print("🎉 ПРОЕКТ ОЧИЩЕН ДЛЯ РЕЛИЗА!")

def create_release_structure():
    """Создание структуры для релиза"""
    print("\n📁 СОЗДАНИЕ СТРУКТУРЫ РЕЛИЗА")
    print("=" * 50)
    
    # Создаем директорию для релиза
    release_dir = "release_v3.2.0"
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)
        print(f"✅ Создана директория: {release_dir}")
    
    # Копируем основные файлы
    essential_files = [
        "app.py",
        "auth.py", 
        "database.py",
        "crm_system.py",
        "analytics_dashboard.py",
        "directories.py",
        "user_management.py",
        "audit_viewer.py",
        "backup_manager.py",
        "notification_manager.py",
        "notifications.py",
        "import_manager.py",
        "validators.py",
        "requirements.txt",
        "README.md",
        "USAGE_GUIDE.md",
        "DEPLOYMENT_GUIDE.md",
        "QUICK_DEPLOY.md",
        "TESTING_REPORT_FINAL.md",
        "deploy.sh",
        ".streamlit/config.toml",
        ".streamlit/secrets.toml",
        ".gitignore"
    ]
    
    copied_files = 0
    
    for file in essential_files:
        if os.path.exists(file):
            try:
                # Создаем поддиректории если нужно
                dest_path = os.path.join(release_dir, file)
                dest_dir = os.path.dirname(dest_path)
                if dest_dir and not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                shutil.copy2(file, dest_path)
                print(f"✅ Скопирован: {file}")
                copied_files += 1
            except Exception as e:
                print(f"❌ Ошибка копирования {file}: {e}")
        else:
            print(f"⚠️ Файл не найден: {file}")
    
    # Копируем excel_templates если существует
    if os.path.exists("excel_templates"):
        try:
            shutil.copytree("excel_templates", os.path.join(release_dir, "excel_templates"))
            print("✅ Скопирована директория: excel_templates")
        except Exception as e:
            print(f"❌ Ошибка копирования excel_templates: {e}")
    
    print(f"\n📊 СКОПИРОВАНО ФАЙЛОВ: {copied_files}")
    print(f"📁 РЕЛИЗ ГОТОВ В ДИРЕКТОРИИ: {release_dir}")

if __name__ == "__main__":
    cleanup_project()
    create_release_structure()
    print("\n🎉 ПРОЕКТ ГОТОВ К РЕЛИЗУ!")
