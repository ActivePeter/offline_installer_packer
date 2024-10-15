import os
import sys
import urllib.request
from pathlib import Path

# 配置项
GITHUB_REPO = 'ActivePeter/offline_installer_packer'  # 替换为你的 GitHub 仓库
APP_NAME = ''  # 替换为你的应用名称
DEB_PACKAGES = []  # 替换为你的 .deb 包列表


def download_deb_packages():
    DOWNLOAD_DIR=sys.argv[2]
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    base_url = f'https://github.com/{GITHUB_REPO}/releases/download/{APP_NAME}/'

    for package in DEB_PACKAGES:
        url = base_url + package
        local_path = os.path.join(DOWNLOAD_DIR, package)
        
        print(f'Downloading {url} to {local_path}')
        if os.path.exists(local_path):
            print(f'{local_path} already exists. Skipping download.')
            continue
        try:
            os.system(f"wget {url} -O {local_path}")
            # urllib.request.urlretrieve(url, local_path, cont)
            print(f'Successfully downloaded {package}')
        except Exception as e:
            print(f'Failed to download {package}: {e}')

    apt_offline_url="https://github.com/rickysarraf/apt-offline/releases/download/v1.8.5/apt-offline-1.8.5.tar.gz"
    if not os.path.exists(f"{DOWNLOAD_DIR}/apt-offline-1.8.5.tar.gz"):
        print(f'Downloading {apt_offline_url}')
        os.system(f"wget {apt_offline_url} -O {DOWNLOAD_DIR}/apt-offline-1.8.5.tar.gz")

def install_deb_packages():
    DOWNLOAD_DIR=sys.argv[2]
    # deb_files = [os.path.join(DOWNLOAD_DIR, package) for package in DEB_PACKAGES]
    # deb_files_str = ' '.join(deb_files)
    
    # print(f'Installing {deb_files_str}')
    # command = f'sudo dpkg -i {deb_files_str}'
    # result = os.system(command)
    
    # if result == 0:
    #     print('All packages installed successfully')
    # else:
    #     print(f'Installation failed: return code {result}')

def main():
    if len(sys.argv) !=3:
        print('Usage: python script.py <prepare|install> <package_dir>')
        sys.exit(1)

    action = sys.argv[1]

    if action == 'prepare':
        download_deb_packages()
    elif action == 'install':
        install_deb_packages()
    else:
        print('Invalid action. Use "prepare" or "install"')
        sys.exit(1)

if __name__ == '__main__':
    main()