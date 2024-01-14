import requests
import os
import shutil
import zipfile
import time
from datetime import datetime
import json

def download_file(url, target_folder):
    # Перевірка та створення папки, якщо вона не існує
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print(f"Створено папку: {target_folder}")

    # Визначення імені файлу з URL
    file_name = url.split('/')[-1]
    file_path = os.path.join(target_folder, file_name)

    # Завантаження файлу
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Файл {file_name} успішно завантажено в {target_folder}")
    else:
        print(f"Помилка при завантаженні файлу: {response.status_code}")

def get_latest_release_date(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    response = requests.get(url)
    release_data = response.json()
    return datetime.strptime(release_data['published_at'], "%Y-%m-%dT%H:%M:%SZ")

def get_latest_commit_date(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/commits"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Помилка при запиті до GitHub API: HTTP {response.status_code}")
        return None

    commits_data = response.json()
    if commits_data:
        return datetime.strptime(commits_data[0]['commit']['committer']['date'], "%Y-%m-%dT%H:%M:%SZ")
    else:
        print("Немає доступних комітів.")
        return None
    
def archive_and_move(base_path, current_dir):
	config_file_path = os.path.join(base_path, 'config.ini')
	langs_path = os.path.join(base_path, 'langs')
	archive_name = 'lang_packs.zip'
    
	if os.path.exists(archive_name):
		os.remove(archive_name)

    # Перевірка наявності файлів та папок
	if not os.path.exists(config_file_path) or not os.path.exists(langs_path):
		print("config.ini або папка langs не знайдені.")
		return

    # Ім'я архіву (з розширенням)
	archive_name = os.path.join(current_dir, 'lang_packs.zip')

    # Створення архіву та додавання папки langs
	print(f"Створюємо архів {archive_name}")
	with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as archive:
		# Додавання папки langs
		for folder_name, subfolders, filenames in os.walk(langs_path):
			for filename in filenames:
					file_path = os.path.join(folder_name, filename)
					archive.write(file_path, os.path.relpath(file_path, base_path))

		# Додавання config.ini
		archive.write(config_file_path, os.path.relpath(config_file_path, base_path))

	print(f"Архів {archive_name} створено і розміщено в {current_dir}")
     
def create_config_from_json(api_data, template_path, config):
    print("Reading template file...")
    with open(template_path, 'r') as file:
        template = file.read()

    print("Extracting languages...")
    languages = api_data.get('languages', [])
    
    print("Sorting languages...")
    languages_sorted = sorted(languages, key=lambda x: x['id'])

    print("Initializing config content...")
    config_content = template.split("[*{%name%}]")[0]

    for lang in languages_sorted:
        print(f"Processing language: {lang['name']}")
        language_section = template.split("[*{%name%}]")[1]
        language_section = language_section.replace("{%name%}", lang['name'])
        language_section = language_section.replace("{%url%}", lang['download_url'])
        language_section = language_section.replace("{%id%}", lang['id'])

        config_content += "\n\n[*{0}]\n".format(lang['name']) + language_section

    config_ini_path = config

    # Перевірка та створення директорії, якщо потрібно
    config_dir = os.path.dirname(config_ini_path)
    if not os.path.exists(config_dir):
        print(f"Creating directory: {config_dir}")
        os.makedirs(config_dir)

    print("Saving config file...")
    with open(config_ini_path, 'w') as file:
        file.write(config_content)
    print("Config file created successfully at:", config_ini_path)

def create_language_jsons(api_data, base_path):
    translations_path = os.path.join(base_path, 'translations')

    langs_path = os.path.join(translations_path, 'langs')
    
    # Створення папки для мов, якщо вона не існує
    if not os.path.exists(langs_path):
        print(f"Створюємо папку для мов: {langs_path}")
        os.makedirs(langs_path)
    else:
        print(f"Папка для мов вже існує: {langs_path}")

    lang_decoding = {
        'replaces_CN-zh': 'Chinese for China region',
        'replaces_EU-de': 'German for Europe region',
        'replaces_EU-en': 'English for Europe region',
        'replaces_EU-es': 'Spanish for Europe region',
        'replaces_EU-fr': 'French for Europe region',
        'replaces_EU-it': 'Italian for Europe region',
        'replaces_EU-nl': 'Dutch for Europe region',
        'replaces_EU-pt': 'Portuguese for Europe region',
        'replaces_EU-ru': 'Russian for Europe region',
        'replaces_JP-ja': 'Japanese for Japan region',
        'replaces_KR-ko': 'Korean for Korea region',
        'replaces_TW-zh': 'Chinese for Taiwan region',
        'replaces_US-en': 'English for America region',
        'replaces_US-es': 'Spanish for America region',
        'replaces_US-fr': 'French for America region',
        'replaces_US-pt': 'Portuguese for America region'
    }

    print("Обробка даних мов...")
    for lang in api_data['languages']:
        json_structure = [{"lang": "`Choose what language will be replaced"}]

        for replace in lang['replaces']:
            decoding_key = f"replaces_{replace['region']['id']}-{replace['locale']['id']}"
            decoded_lang = lang_decoding.get(decoding_key, "")
            json_structure.append({
                "lang": decoded_lang,
                "dir": replace['path']
            })

        json_filename = f"{lang['name']}.json"
        json_file_path = os.path.join(langs_path, json_filename)

        # Запис у JSON файл
        with open(json_file_path, 'w') as json_file:
            json.dump(json_structure, json_file, indent=4)
            print(f"JSON файл створено: {json_filename}")

    print("Створення JSON файлів завершено.")

def read_json(file_path):
    try:
        with open(file_path, 'r') as file:
            print(f"Відкриваю файл: {file_path}")
            data = json.load(file)
            print("Файл успішно прочитано.")
            return data
    except FileNotFoundError:
        print(f"Помилка: файл не знайдено - {file_path}")
    except json.JSONDecodeError:
        print(f"Помилка: не вдалося декодувати JSON з файлу - {file_path}")
    except Exception as e:
        print(f"Виникла помилка при читанні файлу: {e}")

def main():
    user = 'NX-Family'
    repo = 'NX-Translation'
    current_dir = os.path.dirname(os.path.realpath(__file__))
    target_folder = os.path.join(current_dir, 'translations')
    translations_path = target_folder
    commit_user = 'rashevskyv'  # замініть на потрібного користувача
    commit_repo = 'switch-translations-mirrors'  # замініть на потрібний репозиторій

    release_date = get_latest_release_date(user, repo)
    commit_date = get_latest_commit_date(commit_user, commit_repo)

    # download_file('https://raw.githubusercontent.com/NX-Family/NX-Translation/main/api.json', current_dir)
    # api_data = read_json(os.path.join(current_dir, 'api.json'))
    # create_config_from_json(api_data, os.path.join(current_dir, 'config_template.ini'), os.path.join(translations_path, 'config.ini'))
    # create_language_jsons(api_data, current_dir)
    # archive_and_move(translations_path, current_dir)

    if release_date and commit_date:
        if commit_date < release_date:
            print(f"New release was detected on {release_date.strftime('%d.%m.%Y %H:%M:%S')}.")	

            download_file('https://raw.githubusercontent.com/NX-Family/NX-Translation/main/api.json', current_dir)
            api_data = read_json(os.path.join(current_dir, 'api.json'))
            create_config_from_json(api_data, os.path.join(current_dir, 'config_template.ini'), os.path.join(translations_path, 'config.ini'))
            create_language_jsons(api_data, current_dir)
            archive_and_move(translations_path, current_dir)

        else:
            print(f"No new releases detected")
    else:
        print("Не вдалося отримати одну або обидві дати.")

if __name__ == "__main__":
    main()