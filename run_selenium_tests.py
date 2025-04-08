import sys
import pytest
import os
import time
import platform

if __name__ == '__main__':
    print("\n===== ЗАПУСК SELENIUM-ТЕСТОВ =====")
    print(f"Python версия: {platform.python_version()}")
    print(f"Операционная система: {platform.system()} {platform.release()}")
    print("Убедитесь, что Chrome установлен в вашей системе.")
    
    # Вывести дополнительную информацию о текущей директории
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Текущая директория: {current_dir}")
    
    # Создаем директорию для скриншотов, если она не существует
    screenshots_dir = os.path.join(current_dir, 'tests', 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)
    print(f"Скриншоты будут сохранены в: {screenshots_dir}")
    
    # Ждем 1 секунду перед запуском тестов
    print("\nПодготовка к запуску тестов...")
    time.sleep(1)
    
    # Запускаем тесты с подробным выводом
    print("\nЗапуск тестов...")
    result = pytest.main(['tests/test_selenium.py', '-v'])
    
    if result == 0:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"Скриншоты доступны в: {screenshots_dir}")
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ.")
    
    # Возвращаем код результата
    sys.exit(result) 