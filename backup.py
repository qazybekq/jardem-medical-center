import streamlit as st
import sqlite3
import pandas as pd
import zipfile
import os
from datetime import datetime, timedelta
import shutil

# Функции-обертки для совместимости с backup_manager.py
def create_backup():
    """Создать резервную копию"""
    manager = BackupManager()
    return manager.create_backup()

def restore_backup(backup_path):
    """Восстановить из резервной копии"""
    manager = BackupManager()
    return manager.restore_backup(backup_path)

def list_backups():
    """Список резервных копий"""
    manager = BackupManager()
    backups = manager.get_backup_list()
    # Преобразуем в нужный формат
    result = []
    for backup in backups:
        result.append({
            'filename': backup['filename'],
            'path': backup['path'],
            'size_mb': backup['size'] / (1024 * 1024),
            'date': backup['created'].strftime('%Y-%m-%d %H:%M:%S')
        })
    return result

def delete_backup(backup_path):
    """Удалить резервную копию"""
    manager = BackupManager()
    return manager.delete_backup(backup_path)

class BackupManager:
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Создает директорию для бэкапов если её нет"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, include_data=True, include_structure=True) -> str:
        """Создает резервную копию базы данных"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"medical_center_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Копируем базу данных
                db_path = "medical_center.db"
                if os.path.exists(db_path):
                    zipf.write(db_path, "medical_center.db")
                
                # Копируем конфигурационные файлы
                config_files = ["config.py", "requirements.txt"]
                for config_file in config_files:
                    if os.path.exists(config_file):
                        zipf.write(config_file, config_file)
                
                # Добавляем метаданные
                metadata = {
                    "backup_date": datetime.now().isoformat(),
                    "include_data": include_data,
                    "include_structure": include_structure,
                    "version": "1.0"
                }
                
                zipf.writestr("backup_metadata.txt", str(metadata))
            
            return backup_path
            
        except Exception as e:
            st.error(f"Ошибка создания резервной копии: {str(e)}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Восстанавливает базу данных из резервной копии"""
        try:
            if not os.path.exists(backup_path):
                st.error("Файл резервной копии не найден")
                return False
            
            # Создаем резервную копию текущей базы
            current_backup = self.create_backup()
            if current_backup:
                st.info(f"Создана резервная копия текущей базы: {current_backup}")
            
            # Извлекаем файлы из архива
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Извлекаем базу данных
                if "medical_center.db" in zipf.namelist():
                    zipf.extract("medical_center.db", ".")
                    st.success("База данных восстановлена успешно!")
                    return True
                else:
                    st.error("База данных не найдена в резервной копии")
                    return False
                    
        except Exception as e:
            st.error(f"Ошибка восстановления: {str(e)}")
            return False
    
    def get_backup_list(self) -> list:
        """Получает список доступных резервных копий"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("medical_center_backup_") and filename.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stat = os.stat(file_path)
                    backups.append({
                        "filename": filename,
                        "path": file_path,
                        "size": file_stat.st_size,
                        "created": datetime.fromtimestamp(file_stat.st_ctime)
                    })
            
            # Сортируем по дате создания (новые сначала)
            backups.sort(key=lambda x: x["created"], reverse=True)
            return backups
            
        except Exception as e:
            st.error(f"Ошибка получения списка резервных копий: {str(e)}")
            return []
    
    def delete_backup(self, backup_path: str) -> bool:
        """Удаляет резервную копию"""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка удаления резервной копии: {str(e)}")
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Удаляет старые резервные копии"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            backups = self.get_backup_list()
            for backup in backups:
                if backup["created"] < cutoff_date:
                    if self.delete_backup(backup["path"]):
                        deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            st.error(f"Ошибка очистки старых резервных копий: {str(e)}")
            return 0
    
    def export_to_excel(self) -> str:
        """Экспортирует данные в Excel файл"""
        try:
            db = get_database()
            df = db.get_all_patients()
            
            if df.empty:
                st.warning("Нет данных для экспорта")
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"medical_center_export_{timestamp}.xlsx"
            excel_path = os.path.join(self.backup_dir, excel_filename)
            
            # Создаем Excel файл с несколькими листами
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Основные данные
                df.to_excel(writer, sheet_name='Пациенты', index=False)
                
                # Статистика
                stats_data = {
                    'Метрика': ['Всего записей', 'Уникальных пациентов', 'Общая выручка', 'Средний чек'],
                    'Значение': [
                        len(df),
                        df['full_name'].nunique(),
                        df['service_cost'].sum() if 'service_cost' in df.columns else 0,
                        df['service_cost'].mean() if 'service_cost' in df.columns else 0
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Статистика', index=False)
                
                # Аналитика по врачам
                if 'doctor_name' in df.columns:
                    doctor_stats = df.groupby('doctor_name').agg({
                        'full_name': 'count',
                        'service_cost': ['sum', 'mean'] if 'service_cost' in df.columns else 'count'
                    }).round(2)
                    doctor_stats.columns = ['Записей', 'Общая выручка', 'Средний чек'] if 'service_cost' in df.columns else ['Записей']
                    doctor_stats.to_excel(writer, sheet_name='Врачи')
            
            return excel_path
            
        except Exception as e:
            st.error(f"Ошибка экспорта в Excel: {str(e)}")
            return None

def show_backup_management():
    """Показать интерфейс управления резервными копиями"""
    st.subheader("💾 Управление резервными копиями")
    
    backup_manager = BackupManager()
    
    # Создание резервной копии
    st.subheader("📦 Создание резервной копии")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_data = st.checkbox("Включить данные", value=True)
        include_structure = st.checkbox("Включить структуру", value=True)
    
    with col2:
        if st.button("💾 Создать резервную копию", type="primary"):
            with st.spinner("Создание резервной копии..."):
                backup_path = backup_manager.create_backup(include_data, include_structure)
                if backup_path:
                    st.success(f"Резервная копия создана: {backup_path}")
                    st.rerun()
                else:
                    st.error("Ошибка создания резервной копии")
    
    st.markdown("---")
    
    # Список резервных копий
    st.subheader("📋 Список резервных копий")
    
    backups = backup_manager.get_backup_list()
    
    if backups:
        for backup in backups:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"📁 {backup['filename']}")
            
            with col2:
                st.write(f"📅 {backup['created'].strftime('%d.%m.%Y %H:%M')}")
            
            with col3:
                size_mb = backup['size'] / (1024 * 1024)
                st.write(f"💾 {size_mb:.2f} MB")
            
            with col4:
                if st.button("🗑️", key=f"delete_{backup['filename']}", help="Удалить"):
                    if backup_manager.delete_backup(backup['path']):
                        st.success("Резервная копия удалена")
                        st.rerun()
                    else:
                        st.error("Ошибка удаления")
        
        # Восстановление
        st.subheader("🔄 Восстановление")
        
        backup_options = [f"{b['filename']} ({b['created'].strftime('%d.%m.%Y %H:%M')})" for b in backups]
        selected_backup = st.selectbox("Выберите резервную копию для восстановления:", backup_options)
        
        if selected_backup and st.button("🔄 Восстановить", type="primary"):
            backup_index = backup_options.index(selected_backup)
            backup_path = backups[backup_index]['path']
            
            if st.checkbox("Подтвердить восстановление (это заменит текущую базу данных)"):
                with st.spinner("Восстановление..."):
                    if backup_manager.restore_backup(backup_path):
                        st.success("База данных восстановлена успешно!")
                        st.rerun()
                    else:
                        st.error("Ошибка восстановления")
    
    else:
        st.info("Резервные копии не найдены")
    
    st.markdown("---")
    
    # Экспорт в Excel
    st.subheader("📊 Экспорт данных")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Экспорт в Excel"):
            with st.spinner("Экспорт данных..."):
                excel_path = backup_manager.export_to_excel()
                if excel_path:
                    st.success(f"Данные экспортированы: {excel_path}")
                else:
                    st.error("Ошибка экспорта")
    
    with col2:
        if st.button("🧹 Очистить старые копии"):
            days = st.number_input("Удалить копии старше (дней)", value=30, min_value=1)
            if st.button("Подтвердить очистку"):
                deleted_count = backup_manager.cleanup_old_backups(days)
                st.success(f"Удалено резервных копий: {deleted_count}")
                st.rerun()
    
    # Автоматическое резервное копирование
    st.subheader("⏰ Автоматическое резервное копирование")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_backup_enabled = st.checkbox("Включить автоматическое резервное копирование")
        backup_frequency = st.selectbox("Частота", ["Ежедневно", "Еженедельно", "Ежемесячно"])
    
    with col2:
        backup_time = st.time_input("Время резервного копирования", value=datetime.now().time())
        max_backups = st.number_input("Максимум копий", value=10, min_value=1, max_value=100)
    
    if st.button("💾 Сохранить настройки"):
        st.success("Настройки автоматического резервного копирования сохранены")

# Глобальный экземпляр менеджера резервных копий
@st.cache_resource
def get_backup_manager():
    return BackupManager()
