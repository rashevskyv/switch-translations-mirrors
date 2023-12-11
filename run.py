import requests
import shutil
import zipfile
import tarfile
import os

def get_latest_ukrainian_release_tag(repo):
    """
    Get the tag name of the latest release containing 'ukrainian' in its assets from the specified GitHub repository.

    :param repo: Repository name in the format 'owner/repo'
    :return: Tag name of the latest Ukrainian release or None if not found
    """
    # GitHub API endpoint for releases
    api_url = f"https://api.github.com/repos/{repo}/releases"

    try:
        # Send a request to the GitHub API
        response = requests.get(api_url)
        response.raise_for_status()

        # Parse the JSON response
        releases = response.json()

        # Iterate over releases and their assets
        for release in releases:
            for asset in release.get('assets', []):
                if 'ukrainian' in asset['name'].lower():
                    return release['tag_name']

        return None
    except requests.RequestException as e:
        print(f"Error fetching releases: {e}")
        return None

def get_latest_ukrainian_release(repo):
    """
    Get the latest release containing 'ukrainian' in its assets from the specified GitHub repository.

    :param repo: Repository name in the format 'owner/repo'
    :return: Download URL of the latest Ukrainian release asset or None if not found
    """
    # GitHub API endpoint for releases
    api_url = f"https://api.github.com/repos/{repo}/releases"

    try:
        # Send a request to the GitHub API
        response = requests.get(api_url)
        response.raise_for_status()

        # Parse the JSON response
        releases = response.json()

        # Iterate over releases and their assets
        for release in releases:
            for asset in release.get('assets', []):
                if 'ukrainian' in asset['name'].lower():
                    return asset['browser_download_url']

        return None
    except requests.RequestException as e:
        print(f"Error fetching releases: {e}")
        return None

def download_and_extract(url, download_dir):
    """
    Download a file from the given URL and extract it in the directory where the script is located.

    :param url: URL of the file to download
    :param download_dir: Directory where the script is located
    """
    if not url:
        print("URL is None, cannot download.")
        return

    # Determine the file name from the URL
    file_name = url.split('/')[-1]

    # Full path for the file to be saved
    file_path = os.path.join(download_dir, file_name)

    # Download the file
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Save the file
    with open(file_path, 'wb') as f:
        f.write(response.content)

    # Check the file type and extract
    if file_name.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)
    elif file_name.endswith('.tar.gz'):
        with tarfile.open(file_path, 'r:gz') as tar_ref:
            tar_ref.extractall(download_dir)
    else:
        print("Unknown file format, cannot extract.")

    # Optionally, delete the downloaded file after extraction
    os.remove(file_path)

def  create_archives(base_dir, folders, output_dir):
    """
    Create archives from the specified folders within the base directory and store them in the output directory.

    :param base_dir: Base directory containing the folders
    :param folders: List of folder names to be archived
    :param output_dir: Directory where the archives will be stored
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path):
            archive_name = os.path.join(output_dir, folder)
            # Create an archive for the folder
            shutil.make_archive(archive_name, 'zip', base_dir, folder)
        else:
            print(f"Folder not found: {folder}")


# Determine the directory of the script
working_directory = os.path.dirname(os.path.realpath(__file__))
repo = "NX-Family/NX-Translation"
latest_ukrainian_release_tag = get_latest_ukrainian_release_tag(repo)
latest_ukrainian_release_url = get_latest_ukrainian_release(repo)
download_and_extract(latest_ukrainian_release_url, working_directory)
print(latest_ukrainian_release_url)
# Base directory containing the folders
base_directory = 'ukrainian_FW17.0.1'

# List of folders to be archived
folders_to_archive = ['replaces_ru-EU', 'replaces_en-US', 'replaces_en-EU']

# Create archives
create_archives(base_directory, folders_to_archive, working_directory)
