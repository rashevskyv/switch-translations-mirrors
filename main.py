import requests
import os
import shutil
import zipfile
import time
from datetime import datetime
import json

def get_latest_release(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Помилка при запиті до GitHub API: {e}")
        return None

def download_assets(release_data, target_folder):
    if not release_data:
        print("Немає даних для завантаження.")
        return

    # Перевірка та створення папки
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)
    os.makedirs(target_folder)

    assets = release_data.get('assets', [])
    if not assets:
        print("Немає архівів для завантаження.")
        return

    for asset in assets:
        download_url = asset['browser_download_url']
        download_asset(download_url, target_folder)

def download_asset(url, target_folder):
    try:
        response = requests.get(url)
        response.raise_for_status()
        file_name = url.split('/')[-1]
        file_path = os.path.join(target_folder, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Файл '{file_name}' успішно завантажено.")
    except requests.RequestException as e:
        print(f"Помилка при завантаженні файлу {url.split('/')[-1]}: {e}")

def unzip_assets(target_folder):
    for item in os.listdir(target_folder):
        if item.endswith('.zip'):
            file_path = os.path.join(target_folder, item)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_folder)
            print(f"Файл '{item}' успішно розпаковано.")
            os.remove(file_path)  # Видалити архів після розпакування

            # Отримуємо назву папки з назви архіву
            parts = item.replace('.zip', '').split('_')
            folder_name = parts[1] + "_" + parts[2]
            if len(parts) >= 3:
                new_folder_name = parts[1].capitalize()  # Використовуємо першу частину як нову назву папки
                original_folder_path = os.path.join(target_folder, folder_name)
                new_folder_path = os.path.join(target_folder, new_folder_name)
                if os.path.exists(original_folder_path):
                    os.rename(original_folder_path, new_folder_path)
                    print(f"Папка '{folder_name}' перейменована на '{new_folder_name}'.")

def repackage_translations(translation_folder):
    for language in os.listdir(translation_folder):
        language_path = os.path.join(translation_folder, language)
        if os.path.isdir(language_path):
            for region in os.listdir(language_path):
                if region == 'licenses':  # Пропускаємо папку licenses
                    continue

                region_path = os.path.join(language_path, region)
                if os.path.isdir(region_path):
                    # Видаляємо префікс "replaces_" для імені архіву
                    archive_name = region.replace('replaces_', '')
                    archive_file_path = os.path.join(language_path, archive_name)

                    # Створюємо архів із вмістом папки
                    shutil.make_archive(archive_file_path, 'zip', region_path)
                    print(f"Архів '{archive_name}.zip' створено у папці '{language}'.")

                    # Видаляємо оригінальну папку
                    shutil.rmtree(region_path)
                    print(f"Папка '{region}' видалена.")
                    
def save_last_run_timestamp(file_path):
    timestamp = int(time.time())
    with open(file_path, 'w') as file:
        file.write(str(timestamp))
    print(f"Мітка часу останнього запуску ({timestamp}) збережена у файлі '{file_path}'.")

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
    
def create_config(translations_path, template_file_path):
    """
    Creates a config.ini file based on the updated template file and directories inside the translations folder.
    This version excludes the 'langs' folder.
    :param translations_path: Path to the translations folder containing language directories.
    :param template_file_path: Path to the template file.
    """
    try:
        # Read the template content
        with open(template_file_path, 'r', encoding='utf-8') as file:
            template = file.read()

        # List the directories in the given path, excluding 'langs' folder
        language_dirs = [d for d in os.listdir(translations_path) if os.path.isdir(os.path.join(translations_path, d)) and d != 'langs']
        
        # Split the template into two parts: static (first two elements) and dynamic (for each language)
        static_part, dynamic_part = template.split('[*{%language_name%}]', 1)

        config_content = static_part.strip() + "\n\n"

        # Generate config sections for each language directory
        for lang in language_dirs:
            config_section = "[*" + lang + "]" + dynamic_part.replace('{%language_name%}', lang).replace('{%lang%}', lang)
            config_content += config_section.strip() + "\n\n"

        # Save the config_content to a file in translations_path
        with open(os.path.join(translations_path, 'config.ini'), 'w', encoding='utf-8') as file:
            file.write(config_content)

        return "config.ini file created successfully."
    except Exception as e:
        return f"Error: {e}"
        
def create_json_in_folders(base_path):
    print("Початок виконання функції...")

    translations_path = os.path.join(base_path, 'translations')
    print(f"Перевіряємо шлях: {translations_path}")

    if not os.path.exists(translations_path):
        print("Папка перекладів не знайдена.")
        return
    else:
        print("Папка перекладів знайдена.")

    langs_path = os.path.join(translations_path, 'langs')
    if not os.path.exists(langs_path):
        print(f"Створюємо папку: {langs_path}")
        os.makedirs(langs_path)
    else:
        print(f"Папка вже існує: {langs_path}")

    # Словник для розшифровки лінгвістичних пар
    lang_decoding = {
        'de-EU': 'German for Europe region',
        'en-EU': 'English for Europe region',
        'en-US': 'English for America region',
        'es-EU': 'Spanish for Europe region',
        'es-US': 'Spanish for America region',
        'fr-EU': 'French for Europe region',
        'it-EU': 'Italian for Europe region',
        'ru-EU': 'Russian for Europe region'
    }

    for lang_folder in os.listdir(translations_path):
        lang_folder_path = os.path.join(translations_path, lang_folder)
        print(f"Обробляємо папку мови: {lang_folder_path}")

        if os.path.isdir(lang_folder_path) and lang_folder != 'langs':
            print(f"Створюємо JSON для мови: {lang_folder}")
            json_array = [{"lang":"`Choose what language will be replaced"},]

            for file in os.listdir(lang_folder_path):
                if file.endswith('.zip'):
                    file_url = f"https://github.com/rashevskyv/switch-translations-mirrors/raw/main/translations/{lang_folder}/{file}"
                    file_name_without_extension = file[:-4]  # Видаляємо розширення .zip
                    lang_description = lang_decoding.get(file_name_without_extension, file)  # Використовуємо назву файлу, якщо розшифровки немає
                    json_array.append({
                        'file-name': file, 
                        'file-url': file_url,
                        'lang': lang_description
                    })

            with open(os.path.join(langs_path, f'{lang_folder}.json'), 'w') as json_file:
                json.dump(json_array, json_file, indent=4)
            print(f"JSON файл створено: {lang_folder}.json")
        else:
            print(f"Пропускаємо папку: {lang_folder_path}")

    print("Завершення виконання функції.")

    
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

def main():
    user = 'NX-Family'
    repo = 'NX-Translation'
    current_dir = os.path.dirname(os.path.realpath(__file__))
    target_folder = os.path.join(current_dir, 'translations')
    release_data = get_latest_release(user, repo)
    translations_path = target_folder
    commit_user = 'rashevskyv'  # замініть на потрібного користувача
    commit_repo = 'switch-translations-mirrors'  # замініть на потрібний репозиторій

    release_date = get_latest_release_date(user, repo)
    commit_date = get_latest_commit_date(commit_user, commit_repo)
        
    download_assets(release_data, target_folder)
    unzip_assets(target_folder)

    repackage_translations(translations_path)

    create_config(translations_path, os.path.join(current_dir, 'config_template.ini'))
    create_json_in_folders(current_dir)

    archive_and_move(translations_path, current_dir)

    if release_date and commit_date:
        if commit_date < release_date:
            print(f"New release was detected on {release_date.strftime('%d.%m.%Y %H:%M:%S')}.")	
        else:
            print(f"No new releases detected")
    else:
        print("Не вдалося отримати одну або обидві дати.")

if __name__ == "__main__":
    main()