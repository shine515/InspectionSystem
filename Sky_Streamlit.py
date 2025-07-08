#Sky_Streamlit.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from collections import defaultdict
from streamlit_option_menu import option_menu

# Firebase 연결
# Firebase 초기화 및 연결 상태 확인
connection_status = ""
try:
    
    # ✅ Firebase secrets 가져오기
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

    # ✅ Firebase 초기화
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)

    # ✅ Firestore 인스턴스 생성
    db = firestore.client()
    connection_status = f"✅ 서버 연결 성공"
except Exception as e:
    db = None
    connection_status = f"❌ 서버 연결 실패: {e}"

def read_site(Emp_name):
    #st.subheader(f"담당자: {Emp_name}")

    # 해당 직원이 담당한 수용가들 조회
    query = db.collection("sites").where("employee", "==", Emp_name).stream()
    
    grouped = defaultdict(list)
    found = False
        
    for doc in query:
        site = doc.to_dict()
        item = {"Folder": f"{site.get('Folder', '')}",'name': f"{site.get('name', '이름없음')}", 'form_url': f"{site.get('form_url', '')}"}
        grouped[item["Folder"]].append(item)
        found = True
        
    for folder, items in grouped.items():
        grouped[folder] = sorted(items, key=lambda x: x["name"])
        
    if not found:
        st.info("담당 수용가가 없습니다.")
        return found
    else:
        return dict(sorted(grouped.items()))

def print_folder(site):
    if not site:
        return None
    
    for folder, items in site.items():
        with st.expander(f"📂{folder}", expanded=False):
            print_url(items)

def print_url(items):
    for data in items:
        site_name = data["name"]
        form_url = data["form_url"]
        if not form_url:
            st.markdown(f"<p style='font-size:24px;'>🔗[{site_name}]</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size:24px;'>🔗<a href='{form_url}' target='_blank'>[{site_name}]</a></p>", unsafe_allow_html=True)
        #st.markdown("---")
    
def read_employee():
    emp=[]
    employee_docs = db.collection("employees").stream()
    for doc in employee_docs:
        data = doc.to_dict()
        emp.append(data.get("name", "이름없음"))
    return sorted(emp)
    
st.set_page_config(page_title="직원별 수용가 링크", layout="wide")
#st.warning(connection_status)  # 화면 상단에 표시
# 직원 목록 가져오기

employee_names = read_employee()


if not employee_names:
    st.warning("직원이 등록되어 있지 않습니다.")
else:
    choice = None

def print_page():
    #직원별 각각의 탭 생성
    empTabs = st.query_params.get("empTabs","직원별 담당 수용가")
    st.title(f"{empTabs}")
    if empTabs =="직원별 담당 수용가":
        #new
        with st.sidebar:
            choice = option_menu("직원 목록", employee_names,
                                menu_icon="app-indicator", default_index=0,)  
        ###
        sites = read_site(choice)
        print_folder(sites)
        if st.button(f"{choice}"):
            st.query_params["empTabs"] = choice
    else:
        sites = read_site(empTabs)
        folders = {}
        for folder, items in sites.items():
            folders[folder]=items
        #new
        with st.sidebar:
            choice = option_menu(None, list(folders.keys()),
                                icons=['house', 'kanban', 'bi bi-robot'],
                                menu_icon="app-indicator", default_index=0,)  
        
        print_url(folders[choice])
        ###
        
def main():
    print_page()
    
if __name__ == '__main__':
    main()
                
                

