import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
            ---
            **Bike Sharing Demand 데이터셋**
            - [Kaggle Bike Sharing Demand](https://www.kaggle.com/c/bike-sharing-demand)

            **Population Trends 데이터셋**
            - 한국 통계청에서 제공한 연도별 지역 인구 변동 데이터
            - 분석 항목: 총인구수, 출생아수, 사망자수, 지역별 인구 증감, 예측 등
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 EDA Dashboard")
        
        uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded_file:
            st.info("Please upload population_trends.csv")
            return

        df = pd.read_csv(uploaded_file)

        # 전처리
        df.loc[df['지역'] == '세종'] = df.loc[df['지역'] == '세종'].replace('-', 0)
        df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
        df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
        df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')
        df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
        df = df.dropna(subset=['연도', '인구'])

        region_translations = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
            '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
            '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk',
            '경남': 'Gyeongnam', '제주': 'Jeju'
        }
        df['지역(영문)'] = df['지역'].map(region_translations)

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        # 기초 통계
        with tabs[0]:
            st.subheader("📋 Basic Statistics")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())

        # 연도별 추이 + 예측
        with tabs[1]:
            st.subheader("📈 Total Population Trend + Forecast")
            nat = df[df['지역'] == '전국'].copy()
            nat = nat.sort_values('연도')
            recent = nat[nat['연도'] >= nat['연도'].max() - 2]
            net_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            future_year = 2035
            future_pop = nat['인구'].iloc[-1] + net_change * (future_year - nat['연도'].max())

            plot_df = nat[['연도', '인구']].copy()
            plot_df.loc[len(plot_df)] = [future_year, future_pop]

            fig, ax = plt.subplots()
            sns.lineplot(x='연도', y='인구', data=plot_df, marker='o', ax=ax)
            ax.scatter(future_year, future_pop, color='red', label='Forecast')
            ax.set_title("Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        # 지역별 분석
        with tabs[2]:
            st.subheader("📍 Population by Region (Latest Year)")
            latest = df[df['연도'] == df['연도'].max()]
            latest = latest[latest['지역'] != '전국'].sort_values(by='인구', ascending=False)
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='인구', y='지역(영문)', data=latest, ax=ax)
            ax.set_title("Regional Population")
            st.pyplot(fig)

        # 변화량 분석
        with tabs[3]:
            st.subheader("📊 Top 100 Region-Year Population Changes")
            df = df[df['지역'] != '전국'].sort_values(['지역', '연도'])
            df['증감'] = df.groupby('지역')['인구'].diff()
            top100 = df.dropna(subset=['증감']).copy()
            top100 = top100.sort_values(by='증감', key=abs, ascending=False).head(100)

            def color_diff(val):
                color = '#cce5ff' if val > 0 else '#f8d7da'
                return f'background-color: {color}'

            top100['인구'] = top100['인구'].apply(lambda x: f'{int(x):,}')
            top100['증감'] = top100['증감'].astype(int)

            styled = top100[['연도', '지역(영문)', '인구', '증감']].style.applymap(color_diff, subset=['증감']).format({'증감': '{:,}'})
            st.dataframe(styled, use_container_width=True)

        # 시각화 - 누적 영역 그래프
        with tabs[4]:
            st.subheader("📊 Stacked Area Chart")
            area_df = df[df['지역'] != '전국'].pivot_table(index='연도', columns='지역(영문)', values='인구')
            area_df = area_df.fillna(0)
            fig, ax = plt.subplots(figsize=(12, 6))
            area_df.plot.area(ax=ax, cmap='tab20')
            ax.set_title("Population by Region")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()