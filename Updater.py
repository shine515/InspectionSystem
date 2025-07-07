# updater.py
import os
import sys
import requests
import zipfile
import shutil
import subprocess
import tempfile

def download_zip(download_url, save_path):
    print("[업데이트] 최신 zip 파일 다운로드 중...")
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print("[업데이트] 다운로드 완료:", save_path)

def extract_and_replace(zip_path, target_dir):
    print("[업데이트] 압축 해제 중...")
    temp_extract_dir = tempfile.mkdtemp()

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    print("[업데이트] 기존 파일 교체 중...")
    for item in os.listdir(temp_extract_dir):
        s = os.path.join(temp_extract_dir, item)
        d = os.path.join(target_dir, item)

        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    shutil.rmtree(temp_extract_dir)
    print("[업데이트] 교체 완료")

def run_new_executable(exe_name="FbManager.exe"):
    print("[업데이트] 새 버전 실행 중...")
    subprocess.Popen([exe_name], cwd=os.getcwd())
    sys.exit()

def main(download_url):
    zip_file_path = os.path.join(tempfile.gettempdir(), "update.zip")
    app_dir = os.getcwd()

    download_zip(download_url, zip_file_path)
    extract_and_replace(zip_file_path, app_dir)
    run_new_executable()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[업데이트] 오류: 다운로드 URL이 필요합니다.")
        sys.exit(1)

    zip_url = sys.argv[1]
    main(zip_url)
