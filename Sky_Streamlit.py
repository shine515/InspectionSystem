import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import toml
import os

# Firebase 연결
# Firebase 초기화 및 연결 상태 확인
connection_status = ""
try:
    # toml 파일에서 서비스 계정 키 로드
    config = st.secrets["firebase"]["private_key"]
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(config)
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()
    connection_status = "✅ Firebase 연결 성공"
except Exception as e:
    db = None
    connection_status = f"❌ Firebase 연결 실패: {e}"


st.set_page_config(page_title="직원별 수용가 링크", layout="wide")
st.title("👨‍💼 직원별 담당 수용가")

# 직원 목록 가져오기
employee_docs = db.collection("employees").stream()
employee_names = []
for doc in employee_docs:
    data = doc.to_dict()
    employee_names.append(data.get("name", "이름없음"))

if not employee_names:
    st.warning("직원이 등록되어 있지 않습니다.")
else:
    # 탭 생성
    tabs = st.tabs(employee_names)

    for i, emp_name in enumerate(employee_names):
        with tabs[i]:
            st.subheader(f"담당자: {emp_name}")

            # 해당 직원이 담당한 수용가들 조회
            query = db.collection("sites").where("employee", "==", emp_name).stream()
            found = False
            for doc in query:
                site = doc.to_dict()
                site_name = site.get("name", "이름없음")
                form_url = site.get("form_url", "")

                st.markdown(f"📌 **{site_name}**")
                with st.expander(f"📌 {site_name}", expanded=True):
                    if form_url:
                        st.markdown(f"🔗 [Google Form 바로가기]({form_url})", unsafe_allow_html=True)
                    else:
                        st.markdown("❌ 구글폼 링크 없음")

                st.markdown("---")
                found = True

            if not found:
                st.info("담당 수용가가 없습니다.")
