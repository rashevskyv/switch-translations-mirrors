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
    
def archive_and_move(translations_path, current_dir, archive_name):
    archive_name = archive_name+'.zip'
    
    if os.path.exists(archive_name):
        os.remove(archive_name)

    # Check if translations folder exists
    if not os.path.exists(translations_path):
        print(f"Translations folder not found: {translations_path}")
        return

    # Archive name (with extension)
    archive_name = os.path.join(current_dir, archive_name)

    # Create archive and add translations folder
    print(f"Creating archive {archive_name}")
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as archive:
        # Add all files from translations folder
        for folder_name, subfolders, filenames in os.walk(translations_path):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                archive_path = os.path.relpath(file_path, translations_path)
                archive.write(file_path, archive_path)

    print(f"Archive {archive_name} created and placed in {current_dir}")

def create_language_jsons(api_data, base_path):
    translations_path = os.path.join(base_path, 'translations')
    translations_path = os.path.join(translations_path, 'translations_ultra')

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
        json_structure = []

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

def create_general_ini(api_data, ini_name, translations_path, current_dir, langs=False):
    """
    Створює загальний .ini файл у основній директорії для всіх конфігурацій.
    """
    # Формування шляху до шаблону
    template_path = os.path.join(current_dir, ini_name + '_template.ini')

    print("Reading template file...")
    with open(template_path, 'r') as file:
        template = file.read()

    # Розділення шаблону на частини, що стосуються основної конфігурації та мов
    print("Initializing general configuration content...")
    config_parts = template.split(';LANGUAGES')
    if len(config_parts) < 2:
        raise ValueError("Template file is missing the expected ';LANGUAGES' section")
    
    config_content_parts = config_parts[0].split(';CONFIG')
    if len(config_content_parts) < 2:
        raise ValueError("Template file is missing the expected ';CONFIG' section")
    
    config_content = config_content_parts[1].strip()

    # Створення директорії для перекладів, якщо вона не існує
    os.makedirs(translations_path, exist_ok=True)

    # Додавання мовних секцій, якщо параметр langs=True
    if langs:
        print("Adding language sections...")
        languages = api_data.get('languages', [])
        languages_sorted = sorted(languages, key=lambda x: x['id'])
        lang_template = config_parts[1] if len(config_parts) > 1 else ""

        for lang in languages_sorted:
            print(f"Processing language: {lang['name']}")
            language_section = lang_template.replace("{%name%}", lang['name'])
            language_section = language_section.replace("{%url%}", lang['download_url'])
            language_section = language_section.replace("{%id%}", str(lang['id']))
            config_content += language_section

    # Створення загального .ini файлу
    general_config_path = os.path.join(translations_path, ini_name + '.ini')
    print(f"Saving general {ini_name}.ini...")
    with open(general_config_path, 'w') as file:
        file.write(config_content)
    print(f"General {ini_name}.ini created: {general_config_path}")

def create_language_folders_and_inis(api_data, ini_name, translations_path, current_dir):
    """
    Створює папки для кожної мови та відповідні .ini файли.
    """
    template_path = os.path.join(current_dir, ini_name + '_template.ini')

    print("Reading template file for language configuration...")
    with open(template_path, 'r') as file:
        template = file.read()

    print("Extracting languages...")
    languages = api_data.get('languages', [])

    print("Sorting languages...")
    languages_sorted = sorted(languages, key=lambda x: x['id'])

    # Language template content
    if ';LANGUAGES' in template:
        lang_template = template.split(';LANGUAGES')[1].strip()
    else:
        print("Error: ';LANGUAGES' not found in template.")
        return

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

    for lang in languages_sorted:
        print(f"Processing language: {lang['name']}")
        lang_folder = os.path.join(translations_path, lang['name'])
        os.makedirs(lang_folder, exist_ok=True)

        lang_config = "-- Choose what language will be replaced\n\n"

        for replace in lang.get('replaces', []):
            decoding_key = f"replaces_{replace['region']['id']}-{replace['locale']['id']}"
            decoded_lang = lang_decoding.get(decoding_key, "")

            section_config = lang_template.replace("{%lang%}", decoded_lang)
            section_config = section_config.replace("{%download_url%}", lang.get('download_url', ''))
            section_config = section_config.replace("{%id%}", lang.get('id', ''))
            section_config = section_config.replace("{%path%}", replace.get('path', ''))

            lang_config += section_config + "\n"

        lang_config_path = os.path.join(lang_folder, ini_name + '.ini')
        with open(lang_config_path, 'w') as file:
            file.write(lang_config)
        print(f"Config.ini for {lang['name']} created: {lang_config_path}")

    print("Language configuration files creation completed.")

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
    translations_path = os.path.join(current_dir, 'translations')
    translations_uber_path = os.path.join(translations_path, 'translations_uber')
    translations_ultra_path = os.path.join(translations_path, 'translations_ultra')
    commit_user = 'rashevskyv'
    commit_repo = 'switch-translations-mirrors'

    release_date = get_latest_release_date(user, repo)
    commit_date = get_latest_commit_date(commit_user, commit_repo)
    print(f'release_date {release_date}, commit_date {commit_date}')

    if release_date and commit_date:
        if commit_date < release_date:
            print("New version available. Updating...")
            
            # Clean up the translations folder
            if os.path.exists(translations_path):
                print(f"Cleaning up the translations folder: {translations_path}")
                shutil.rmtree(translations_path)
            os.makedirs(translations_path)
            os.makedirs(translations_uber_path)
            os.makedirs(translations_ultra_path)
            print(f"Created clean translations folder: {translations_path}")
            
            download_file('https://raw.githubusercontent.com/NX-Family/NX-Translation/main/api.json', current_dir)
            api_data = read_json(os.path.join(current_dir, 'api.json'))
            create_general_ini(api_data, 'config', translations_uber_path, current_dir)
            create_language_folders_and_inis(api_data, 'config', translations_uber_path, current_dir)
            create_general_ini(api_data, 'package', translations_ultra_path, current_dir, True)
            create_language_jsons(api_data, current_dir)
            archive_and_move(translations_uber_path, current_dir, 'lang_packs')
            archive_and_move(translations_ultra_path, current_dir, 'lang_packs_ultra')
        else:
            print("Update not needed.")
    else:
        print("Failed to get date information. Update skipped.")

if __name__ == "__main__":
    main()