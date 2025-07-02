import firebase_admin
from firebase_admin import credentials, db

# 서비스 계정 키 경로
cred = credentials.Certificate("sky-electric-a036a-firebase-adminsdk-fbsvc-f8631e3db8.json")

# Firebase 앱 초기화
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://console.firebase.google.com/project/sky-electric-a036a/database/sky-electric-a036a-default-rtdb/data'  # 수정 필요
})

# DB 경로 지정
ref = db.reference('names')  # "names"는 루트 노드 이름
