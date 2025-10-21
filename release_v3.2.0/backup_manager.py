#!/usr/bin/env python3
"""
Управление резервным копированием базы данных
"""

import streamlit as st
import os
from datetime import datetime
from backup import create_backup, restore_backup, list_backups, delete_backup

def main():
    """Главная функция управления резервными копиями"""
    st.title("💾 Резервное копирование")
    
    tab1, tab2, tab3 = st.tabs(["📦 Создать копию", "🔄 Восстановить", "📋 Управление копиями"])
    
    with tab1:
        show_create_backup()
    
    with tab2:
        show_restore_backup()
    
    with tab3:
        show_manage_backups()

def show_create_backup():
    """Создание резервной копии"""
    st.subheader("📦 Создание резервной копии")
    
    st.info("""
    💡 **Резервная копия включает:**
    - Всю базу данных (клиенты, врачи, услуги, приемы)
    - Журнал аудита
    - Настройки системы
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        backup_description = st.text_input(
            "Описание копии (необязательно):",
            placeholder="Например: Резервная копия перед обновлением",
            key="backup_description"
        )
    
    with col2:
        if st.button("🚀 Создать резервную копию", use_container_width=True):
            with st.spinner("Создание резервной копии..."):
                try:
                    backup_path = create_backup()
                    if backup_path:
                        st.success(f"✅ Резервная копия создана успешно!")
                        st.code(backup_path)
                        
                        # Показываем размер файла
                        if os.path.exists(backup_path):
                            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
                            st.info(f"📊 Размер файла: {size_mb:.2f} МБ")
                    else:
                        st.error("❌ Ошибка при создании резервной копии")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
    
    st.markdown("---")
    
    # Информация о последней копии
    backups = list_backups()
    if backups:
        latest = backups[0]
        st.subheader("📍 Последняя резервная копия")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Дата создания:**")
            st.write(latest['date'])
        
        with col2:
            st.write("**Размер:**")
            st.write(f"{latest['size_mb']:.2f} МБ")
        
        with col3:
            st.write("**Файл:**")
            st.write(latest['filename'])

def show_restore_backup():
    """Восстановление из резервной копии"""
    st.subheader("🔄 Восстановление из резервной копии")
    
    st.warning("""
    ⚠️ **ВНИМАНИЕ:**
    - Восстановление заменит ВСЕ текущие данные
    - Создайте резервную копию текущих данных перед восстановлением
    - Процесс необратим!
    """)
    
    backups = list_backups()
    
    if not backups:
        st.info("📭 Нет доступных резервных копий")
        return
    
    # Выбор копии для восстановления
    selected_backup = st.selectbox(
        "Выберите резервную копию:",
        options=backups,
        format_func=lambda x: f"{x['date']} ({x['size_mb']:.2f} МБ) - {x['filename']}",
        key="restore_backup_select"
    )
    
    if selected_backup:
        col1, col2 = st.columns(2)
        
        with col1:
            # Подтверждение
            confirm = st.checkbox(
                "Я понимаю, что текущие данные будут заменены",
                key="restore_confirm"
            )
        
        with col2:
            if confirm:
                if st.button("🔄 Восстановить", type="primary", use_container_width=True):
                    with st.spinner("Восстановление данных..."):
                        try:
                            success = restore_backup(selected_backup['path'])
                            if success:
                                st.success("✅ Данные успешно восстановлены!")
                                st.info("💡 Перезапустите приложение для применения изменений")
                            else:
                                st.error("❌ Ошибка при восстановлении данных")
                        except Exception as e:
                            st.error(f"❌ Ошибка: {e}")

def show_manage_backups():
    """Управление резервными копиями"""
    st.subheader("📋 Управление резервными копиями")
    
    backups = list_backups()
    
    if not backups:
        st.info("📭 Нет доступных резервных копий")
        return
    
    st.write(f"**Всего копий:** {len(backups)}")
    
    total_size = sum(b['size_mb'] for b in backups)
    st.write(f"**Общий размер:** {total_size:.2f} МБ")
    
    st.markdown("---")
    
    # Таблица копий
    for i, backup in enumerate(backups):
        with st.expander(f"📦 {backup['date']} - {backup['filename']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Дата создания:**")
                st.write(backup['date'])
            
            with col2:
                st.write("**Размер:**")
                st.write(f"{backup['size_mb']:.2f} МБ")
            
            with col3:
                st.write("**Путь:**")
                st.code(backup['path'], language=None)
            
            # Кнопка удаления
            if st.button(f"🗑️ Удалить эту копию", key=f"delete_backup_{i}"):
                with st.spinner("Удаление..."):
                    try:
                        if delete_backup(backup['path']):
                            st.success("✅ Резервная копия удалена")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка при удалении")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")
    
    st.markdown("---")
    
    # Автоматическое копирование (будущая функция)
    st.subheader("🤖 Автоматическое копирование")
    st.info("⏳ Функция автоматического копирования будет добавлена в следующей версии")
    
    # Настройки
    # st.checkbox("Включить автоматическое копирование", disabled=True)
    # st.number_input("Создавать копию каждые N дней:", min_value=1, max_value=30, value=7, disabled=True)
    # st.number_input("Хранить последние N копий:", min_value=1, max_value=100, value=10, disabled=True)

if __name__ == "__main__":
    main()

