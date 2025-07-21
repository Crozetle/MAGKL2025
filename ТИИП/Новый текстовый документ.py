import os

# Папка, содержащая файлы
folder_path = 'Вопросы'

# Строка, которую нужно добавить
line_to_add = '[[Анализ данных]]\n'

# Проходим по каждому файлу в папке
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # Пропускаем, если это не файл
    if not os.path.isfile(file_path):
        continue

    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Добавляем строку, если её ещё нет
    if '[[Анализ данных]]' not in content:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(line_to_add)

print("Готово: строка добавлена ко всем файлам.")
