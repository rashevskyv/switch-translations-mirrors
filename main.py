import requests
import os
import shutil
import zipfile
import time
from datetime import datetime

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
                new_folder_name = parts[1]  # Використовуємо першу частину як нову назву папки
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
                region_path = os.path.join(language_path, region)
                if os.path.isdir(region_path):
                    # Видаляємо префікс "replaces_" для імені архіву
                    archive_name = region.replace('replaces_', '') + '.zip'
                    zip_file_path = os.path.join(language_path, archive_name)

                    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                        for root, dirs, files in os.walk(region_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                zipf.write(file_path, os.path.relpath(file_path, region_path))
                        print(f"Архів '{archive_name}' створено у папці '{language}'.")

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

def main():
	user = 'NX-Family'
	repo = 'NX-Translation'
	current_dir = os.path.dirname(os.path.realpath(__file__))
	target_folder = os.path.join(current_dir, 'translations')

	release_data = get_latest_release(user, repo)
	download_assets(release_data, target_folder)
	unzip_assets(target_folder)
    
	translation_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'translations')
	repackage_translations(translation_folder)
    
	timestamp_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'last_run_timestamp.txt')
	save_last_run_timestamp(timestamp_file_path)
    
	commit_user = 'rashevskyv'  # замініть на потрібного користувача
	commit_repo = 'switch-translations-mirrors'  # замініть на потрібний репозиторій

	release_date = get_latest_release_date(user, repo)
	commit_date = get_latest_commit_date(commit_user, commit_repo)
    
	if release_date and commit_date:
		if commit_date < release_date:
			print(f"{release_date} > {commit_date}")	
		else:
			print(f"{release_date} < {commit_date}")
	else:
		print("Не вдалося отримати одну або обидві дати.")

if __name__ == "__main__":
    main()