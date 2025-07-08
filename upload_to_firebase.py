import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup

# 경로 지정
EXCEL_PATH = r"H:\내 드라이브\WORK\점검기록표\수용가리스트.xlsm"
SERVICE_ACCOUNT_PATH = r"skyelectricFbKey.json"
FIRESTORE_COLLECTION = 'sites'
HTML_PAGE_PATH = r"C:/Users/Admin/Documents/카카오톡 받은 파일/Links.html"  # 단일 HTML 파일

# Firebase 초기화
cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

# 엑셀 읽기
df = pd.read_excel(EXCEL_PATH, sheet_name=0, engine='openpyxl')

# ===== HTML 파일에서 모든 수용가 이름과 구글폼 링크 매핑 =====
def build_form_link_map(html_path):
    link_map = {}
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            current_text = None
            # 모든 태그를 순회하며 수용가 이름과 링크 추출
            for tag in soup.find_all(['h3', 'a']):
                text = tag.get_text(strip=True)
                print(f"name: {tag.name}, text: {text} ")
                if tag.name == 'h3':
                    if "점검리스트" not in text:
                        current_text = text
                elif tag.name == 'a':
                    href = tag['href']
                    if "https://forms.gle/" in href:
                        link_map[text] = {
                            "url": href,
                            "Folder": current_text
                        }
    except Exception as e:
        print(f"[HTML 파싱 오류] {e}")
    return link_map

form_link_map = build_form_link_map(HTML_PAGE_PATH)

# ===== 데이터 처리 및 업로드 =====
for index, row in df.iterrows():
    try:
        name = str(row['수용가명칭']).strip()
        code = str(row['수용가번호']).strip()
        if pd.isna(name) or name == '':
            continue  # 수용가 이름 없으면 스킵

        form_info = form_link_map.get(name, {})
        form_url = form_info.get("url", "")
        Folder = form_info.get("Folder", "")

        doc_data = {
            'name': name,
            'data_code': code,
            'category': str(row['구분']).strip() if not pd.isna(row['구분']) else '',
            'address': str(row['설비위치']).strip() if not pd.isna(row['설비위치']) else '',
            'employee': str(row['담당자']).strip() if not pd.isna(row['담당자']) else '',
            'form_url': form_url,
            'sheet_url': '',
            'Folder': Folder
        }

        db.collection(FIRESTORE_COLLECTION).document(code).set(doc_data)
        print(f"[✅ 업로드 성공] {code}")
        print(f"[✅ 업로드 성공] {doc_data}")

    except Exception as e:
        print(f"[❌ 오류] {index + 2}행 ({code}): {e}")