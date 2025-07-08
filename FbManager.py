import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QListWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QGroupBox, QDialog, QComboBox, QScrollArea
)
import firebase_admin
from firebase_admin import credentials, firestore

import requests
from packaging import version

import subprocess
#---------------------------------------------------#
###------------------업데이트 체크------------------###

def get_latest_release_info():
    url = "https://api.github.com/repos/shine515/InspectionSystem/releases/latest"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            tag = data["tag_name"].lstrip("v")  # 'v1.2.3' → '1.2.3'
            for asset in data["assets"]:
                if asset["name"].endswith(".zip"):
                    return tag, asset["browser_download_url"]
        return None, None
    except Exception as e:
        print("[업데이트] 버전 조회 실패:", e)
        return None, None

def read_local_version():
    try:
        with open(os.path.join("version.txt"), "r", encoding="utf-8") as f:
            app = QApplication(sys.argv)
            lver = f.read().strip()[1:]
            print("로컬버전 조회: ", lver)
            return lver
    except Exception as e:
        print("로컬버전 조회실패", e)
        return "0.0.0"

def is_update_needed(current_version):
    latest_version, download_url = get_latest_release_info()
    if latest_version and version.parse(latest_version) > version.parse(current_version):
        window = ManagerProgram()
        window.show()
        sys.exit(app.exec_())
        return True, download_url, latest_version
            
    return False, None, None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller 실행 시 임시 폴더
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
#---------------------------------------------------#

###------------------DB(FireBase연결)------------------###
# Firebase 키 경로
key_path = resource_path("skyelectricFbKey.json")

# Firebase 초기화 및 연결 상태 확인
connection_status = ""
if not firebase_admin._apps:
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()
#-------------------------------------------------------#

class AddOrEditWindow(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("수용가 정보 입력")
        self.setGeometry(300, 150, 400, 400)
        self.setModal(True)
        self.initUI(data)

    def initUI(self, data): #수용가 추가UI
        layout = QVBoxLayout()
        #수용가 정보
        self.txt_code = QLineEdit()
        self.txt_name = QLineEdit()
        self.txt_addr = QLineEdit()
        self.txt_type = QLineEdit()
        self.txt_google = QLineEdit()
        self.txt_sheet = QLineEdit()
        self.txt_staff = QLineEdit()
        self.txt_Floder = QLineEdit()

        layout.addWidget(QLabel("수용가번호 (데이터코드)"))
        layout.addWidget(self.txt_code)
        layout.addWidget(QLabel("수용가이름"))
        layout.addWidget(self.txt_name)
        layout.addWidget(QLabel("구분"))
        layout.addWidget(self.txt_type)
        layout.addWidget(QLabel("주소"))
        layout.addWidget(self.txt_addr)
        layout.addWidget(QLabel("구글폼 링크"))
        layout.addWidget(self.txt_google)
        layout.addWidget(QLabel("응답시트링크"))
        layout.addWidget(self.txt_sheet)
        layout.addWidget(QLabel("담당직원"))
        layout.addWidget(self.txt_staff)
        layout.addWidget(QLabel("정리폴더"))
        layout.addWidget(self.txt_Floder)

        self.btn_save = QPushButton("저장")
        self.btn_save.clicked.connect(self.save_data)
        layout.addWidget(self.btn_save)

        self.setLayout(layout)

        if data:
            self.txt_code.setText(data.get("data_code", ""))
            self.txt_code.setReadOnly(True)
            self.txt_name.setText(data.get("name", ""))
            self.txt_addr.setText(data.get("address", ""))
            self.txt_google.setText(data.get("form_url", ""))
            self.txt_sheet.setText(data.get("sheet_url", ""))
            self.txt_staff.setText(data.get("employee", ""))
            self.txt_type.setText(data.get("category", ""))
            self.txt_Floder.setText(data.get("Folder", ""))
            
    def save_data(self): #서버에 업데이트
        name = self.txt_name.text().strip()
        code = self.txt_code.text().strip()
        if not name or not code:
            QMessageBox.warning(self, "입력 오류", "이름과 수용가번호는 필수입니다.")
            return

        data = {
            "data_code": code,
            "name": name,
            "address": self.txt_addr.text().strip(),
            "form_url": self.txt_google.text().strip(),
            "sheet_url": self.txt_sheet.text().strip(),
            "employee": self.txt_staff.text().strip(),
            "category": self.txt_type.text().strip(),
            "Folder": self.txt_Floder.text().strip()
        }

        db.collection("sites").document(code).set(data)
        QMessageBox.information(self, "성공", "저장되었습니다.")
        self.accept()

class ManagerProgram(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("수용가 관리자 프로그램")
        self.setGeometry(200, 100, 1000, 600)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # 연결 상태 표시
        self.status_label = QLabel(connection_status)
        main_layout.addWidget(self.status_label)

        content_layout = QHBoxLayout()

        # 왼쪽 수용가 리스트 그룹
        left_box = QVBoxLayout()

        # 검색 및 필터
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색 (이름 포함)")
        self.search_input.textChanged.connect(self.apply_filters)

        self.staff_filter = QComboBox()
        self.staff_filter.addItem("전체")
        self.staff_filter.currentIndexChanged.connect(self.apply_filters)

        self.type_filter = QComboBox()
        self.type_filter.addItem("전체")
        self.type_filter.currentIndexChanged.connect(self.apply_filters)

        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.staff_filter)
        filter_layout.addWidget(self.type_filter)

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(lambda current, prev: self.load_detail(current)) #커서에 맞춰 업데이트

        self.btn_add = QPushButton("+추가")
        self.btn_add.clicked.connect(self.open_add_window)

        left_box.addLayout(filter_layout)
        left_box.addWidget(self.btn_add)
        left_box.addWidget(self.list_widget)

        # 오른쪽 상세정보 그룹
        right_box = QVBoxLayout()
        detail_group = QGroupBox("수용가 상세정보")
        grid = QGridLayout()

        self.txt_code = QLineEdit(); self.txt_code.setReadOnly(True)
        self.txt_name = QLineEdit(); self.txt_name.setReadOnly(True)
        self.txt_addr = QLineEdit(); self.txt_addr.setReadOnly(True)
        self.txt_google = QLineEdit(); self.txt_google.setReadOnly(True)
        self.txt_sheet = QLineEdit(); self.txt_sheet.setReadOnly(True)
        self.txt_staff = QLineEdit(); self.txt_staff.setReadOnly(True)
        self.txt_type = QLineEdit(); self.txt_type.setReadOnly(True)
        self.txt_Floder = QLineEdit(); self.txt_Floder.setReadOnly(True)

        grid.addWidget(QLabel("데이터코드"), 0, 0); grid.addWidget(self.txt_code, 0, 1)
        grid.addWidget(QLabel("수용가이름"), 1, 0); grid.addWidget(self.txt_name, 1, 1)
        grid.addWidget(QLabel("주소"), 2, 0); grid.addWidget(self.txt_addr, 2, 1)
        grid.addWidget(QLabel("구글폼 링크"), 3, 0); grid.addWidget(self.txt_google, 3, 1)
        grid.addWidget(QLabel("응답시트링크"), 4, 0); grid.addWidget(self.txt_sheet, 4, 1)
        grid.addWidget(QLabel("담당직원"), 5, 0); grid.addWidget(self.txt_staff, 5, 1)
        grid.addWidget(QLabel("구분"), 6, 0); grid.addWidget(self.txt_type, 6, 1)
        grid.addWidget(QLabel("정리폴더"), 7, 0); grid.addWidget(self.txt_Floder, 7, 1)

        detail_group.setLayout(grid)

        btn_layout = QHBoxLayout()
        self.btn_update = QPushButton("수정")
        self.btn_delete = QPushButton("삭제")
        self.btn_update.clicked.connect(self.open_edit_window)
        self.btn_delete.clicked.connect(self.delete_site)
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_delete)

        right_box.addWidget(detail_group)
        right_box.addLayout(btn_layout)

        # 스크롤 가능 영역 설정
        scroll_area = QScrollArea()
        scroll_container = QWidget()
        scroll_layout = QHBoxLayout(scroll_container)
        scroll_layout.addLayout(left_box, 2)
        scroll_layout.addLayout(right_box, 3)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_container)

        content_layout.addWidget(scroll_area)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)
        self.load_site_list()

    def load_site_list(self):
        self.list_widget.clear()
        self.sites = {}
        self.staff_filter.blockSignals(True)
        self.staff_filter.clear()
        self.staff_filter.addItem("전체")
        self.type_filter.blockSignals(True)
        self.type_filter.clear()
        self.type_filter.addItem("전체")
        if not db:
            return
        employees = set()
        categories = set()
        for doc in db.collection("sites").stream():
            data = doc.to_dict()
            self.sites[data["name"]] = data
            employees.add(data.get("employee", ""))
            categories.add(data.get("category", ""))
        for emp in sorted(employees):
            self.staff_filter.addItem(emp)
        for cat in sorted(categories):
            self.type_filter.addItem(cat)
        self.staff_filter.blockSignals(False)
        self.type_filter.blockSignals(False)
        self.apply_filters()

    def apply_filters(self):
        keyword = self.search_input.text().strip().lower()
        selected_staff = self.staff_filter.currentText()
        selected_type = self.type_filter.currentText()

        self.list_widget.clear()
        for name, data in self.sites.items():
            if keyword and keyword not in name.lower():
                continue
            if selected_staff != "전체" and data.get("employee") != selected_staff:
                continue
            if selected_type != "전체" and data.get("category") != selected_type:
                continue
            self.list_widget.addItem(name)

    def load_detail(self, item):
        name = item.text()
        site = self.sites[name]
        self.txt_code.setText(site.get("data_code", ""))
        self.txt_name.setText(site.get("name", ""))
        self.txt_addr.setText(site.get("address", ""))
        self.txt_google.setText(site.get("form_url", ""))
        self.txt_sheet.setText(site.get("sheet_url", ""))
        self.txt_staff.setText(site.get("employee", ""))
        self.txt_type.setText(site.get("category", ""))
        self.txt_Floder.setText(site.get("Floder", ""))

    def open_add_window(self):
        dlg = AddOrEditWindow(parent=self)
        if dlg.exec_():
            self.load_site_list()

    def open_edit_window(self):
        name = self.txt_name.text().strip()
        if name and name in self.sites:
            dlg = AddOrEditWindow(parent=self, data=self.sites[name])
            if dlg.exec_():
                self.load_site_list()

    def delete_site(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "오류", "삭제할 수용가 이름을 입력하세요.")
            return
        db.collection("sites").document(name).delete()
        QMessageBox.information(self, "삭제", "삭제 완료")
        self.txt_code.clear()
        self.txt_name.clear()
        self.txt_addr.clear()
        self.txt_google.clear()
        self.txt_sheet.clear()
        self.txt_staff.clear()
        self.txt_type.clear()
        self.txt_Floder.clear()
        self.load_site_list()

if __name__ == "__main__":
    CURRENT_VERSION = read_local_version()
    app = QApplication(sys.argv)
    update_needed, zip_url, latest = is_update_needed(CURRENT_VERSION)

    if update_needed:
        reply = QMessageBox.question(
            None,
            "업데이트 확인",
            f"새 버전 {latest} 이(가) 있습니다.\n업데이트 하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            subprocess.Popen(["Updater.exe", zip_url])
            sys.exit()
    window = ManagerProgram()
    window.show()
    sys.exit(app.exec_())
