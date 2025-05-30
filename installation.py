import subprocess

# Список библиотек, которые нужно установить
libraries_to_install = ['requests', 'pycryptodome', 'pywin32']
for library in libraries_to_install:
    try:
        subprocess.check_call(['pip', 'install', library])
        print(f'{library} успешно установлена.')
    except subprocess.CalledProcessError:
        print(f'Ошибка при установке {library}.')

print('Установка библиотек завершена.')