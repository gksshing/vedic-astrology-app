import streamlit as st
from datetime import datetime, date, time
from openai import OpenAI
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

NAKSHATRAS = [
    "아쉬위니 (Ashwini)", "바라니 (Bharani)", "크리티카 (Krittika)",
    "로히니 (Rohini)", "므리가시라 (Mrigashira)", "아르드라 (Ardra)",
    "푸나르바수 (Punarvasu)", "푸시야 (Pushya)", "아슬레샤 (Ashlesha)",
    "마가 (Magha)", "푸르바 팔구니 (Purva Phalguni)", "우타라 팔구니 (Uttara Phalguni)",
    "하스타 (Hasta)", "치트라 (Chitra)", "스와티 (Swati)",
    "비샤카 (Vishakha)", "아누라다 (Anuradha)", "제쉬타 (Jyeshtha)",
    "물라 (Mula)", "푸르바샤다 (Purvashadha)", "우타라샤다 (Uttarashadha)",
    "스라바나 (Shravana)", "다니쉬타 (Dhanishta)", "샤타비샤 (Shatabhisha)",
    "푸르바 바드라파다 (Purva Bhadrapada)", "우타라 바드라파다 (Uttara Bhadrapada)", "레바티 (Revati)"
]

RASHIS = [
    "메샤 (양자리)", "브리샤바 (황소자리)", "미투나 (쌍둥이자리)",
    "카르카 (게자리)", "심하 (사자자리)", "칸야 (처녀자리)",
    "툴라 (천칭자리)", "브리쉬치카 (전갈자리)", "다누 (사수자리)",
    "마카라 (염소자리)", "쿰바 (물병자리)", "미나 (물고기자리)"
]

def get_location_coordinates(city_name):
    try:
        geolocator = Nominatim(user_agent="vedic_astrology_app")
        location = geolocator.geocode(city_name)
        return (location.latitude, location.longitude, location.address) if location else (None, None, None)
    except: return None, None, None

def get_timezone(lat, lon):
    try: return TimezoneFinder().timezone_at(lat=lat, lng=lon) or "UTC"
    except: return "UTC"

def analyze_compatibility_with_openai(p1_data, p2_data):
    system = """You are a master of Vedic Astrology (Jyotish) with 30 years of experience.
You have deep knowledge of:
- Sidereal zodiac calculations (Lahiri Ayanamsa)
- 12 Rashis (zodiac signs) and their characteristics
- 27 Nakshatras (lunar mansions) with their padas
- Planetary positions and house placements
- Ashta Kuta compatibility system

Based on the birth data provided, you will:
1. Calculate the Vedic birth chart parameters (Lagna, Moon Sign, Nakshatra, Sun Sign)
2. Analyze the Ashta Kuta compatibility between two people
3. Provide scores for all 8 Kutas converted to 100-point scale

Be sophisticated, mysterious, and brutally honest.
If the stars say it's a disaster, call it a celestial catastrophe.
Format your ENTIRE response in Korean (한국어)."""

    user = f"""다음 두 사람의 출생 정보를 바탕으로 베딕 점성술 분석을 해주세요:

【첫 번째 사람: {p1_data['name']}】
- 생년월일: {p1_data['birth_date']}
- 출생 시간: {p1_data['birth_time']}
- 출생 장소: {p1_data['city']} (위도: {p1_data['lat']:.4f}, 경도: {p1_data['lon']:.4f})
- 시간대: {p1_data['timezone']}

【두 번째 사람: {p2_data['name']}】
- 생년월일: {p2_data['birth_date']}
- 출생 시간: {p2_data['birth_time']}
- 출생 장소: {p2_data['city']} (위도: {p2_data['lat']:.4f}, 경도: {p2_data['lon']:.4f})
- 시간대: {p2_data['timezone']}

다음을 수행해주세요:
1. 각 사람의 베딕 차트 파라미터 계산 (Lahiri Ayanamsa 사용):
   - 라그나 (상승궁/Ascendant)
   - 달 별자리 (라시/Moon Sign)
   - 낙샤트라 (Nakshatra) 및 파다
   - 태양 별자리 (Sun Sign)

2. 아쉬타쿠타 궁합 분석 (100점 만점 스케일):
   - 바르나 쿠타 (~3점): 영적 호환성
   - 바쉬야 쿠타 (~6점): 상호 매력
   - 타라 쿠타 (~8점): 운명과 건강
   - 요니 쿠타 (~11점): 친밀함
   - 그라하 마이트리 (~14점): 정신적 호환성
   - 가나 쿠타 (~17점): 기질
   - 바쿠트 쿠타 (~19점): 감정적 조화
   - 나디 쿠타 (~22점): 건강과 자녀
   - 총점: X/100점

3. 종합 궁합 해석 (신비롭고 심오하게)

궁합이 나쁘면 "천체적 재앙"이라고 솔직하게 표현해주세요."""

    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.8,
            max_tokens=3000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ API 오류: {e}"

def apply_custom_css():
    st.markdown("""<style>
    .stApp{background:linear-gradient(135deg,#0d0d1a,#1a1a2e,#16213e);}
    h1{color:#ffd700!important;text-align:center;text-shadow:0 0 20px rgba(255,215,0,0.5);}
    h2,h3,h4{color:#ffd700!important;}
    .stButton>button{background:linear-gradient(135deg,#ffd700,#ff8c00)!important;color:#1a1a2e!important;border:none!important;border-radius:25px!important;padding:15px 40px!important;font-weight:bold!important;box-shadow:0 0 20px rgba(255,215,0,0.4)!important;}
    .info-card{background:rgba(255,215,0,0.1);border-left:4px solid #ffd700;padding:15px;margin:10px 0;border-radius:0 10px 10px 0;}
    .result-box{background:linear-gradient(135deg,rgba(26,26,46,0.9),rgba(22,33,62,0.9));border:2px solid #ffd700;border-radius:15px;padding:25px;margin:20px 0;box-shadow:0 0 30px rgba(255,215,0,0.2);}
    p,li,td,th{color:#ffffff!important;}
    label{color:#ffd700!important;}
    .stExpander{border:1px solid #ffd700!important;border-radius:10px!important;}
    div[data-baseweb="popover"] *{color:#000000!important;}
    div[data-baseweb="calendar"] *{color:#000000!important;}
    div[data-baseweb="select"] ul li{color:#000000!important;}
    div[role="listbox"] *{color:#000000!important;}
    [data-baseweb="menu"] *{color:#000000!important;}
    </style>""", unsafe_allow_html=True)

def show_vedic_info():
    st.markdown("### 🕉️ 베딕 점성술(Jyotish)이란?")
    st.markdown("""
**베딕 점성술(Vedic Astrology)**, 또는 **조티쉬(Jyotish)**는 약 5,000년 전 인도에서 시작된 고대 점성술 체계입니다. 
"조티쉬"는 산스크리트어로 **"빛의 과학"** 또는 **"천체의 지혜"**를 의미합니다.
    """)
    
    st.markdown("### 🌌 무궁무진한 경우의 수")
    st.markdown("""
베딕 점성술의 가장 큰 강점은 그 **엄청난 조합의 다양성**입니다:
- **12 라시(별자리)** × **27 낙샤트라(달의 별자리)** × **12 상승궁** = **3,888가지 기본 조합**
- 여기에 7개 행성의 위치, 12개 하우스 배치, 행성 간 각도(Aspects)까지 고려하면...
- 🔢 **수십억 가지 이상의 고유한 차트 조합**이 가능합니다!
- 두 사람의 궁합 분석 시: **3,888² = 약 1,500만 가지** 이상의 기본 조합

→ *이것이 베딕 점성술이 각 개인의 독특한 운명을 정밀하게 읽어낼 수 있는 이유입니다.*
    """)
    
    st.markdown("### 🌙 서양 점성술과의 차이점")
    st.markdown("""
- **항성 황도대(Sidereal Zodiac)**: 실제 별자리 위치 기반 (서양은 계절 기반)
- **달 중심**: 태양보다 달의 위치를 더 중요시함
- **27 낙샤트라**: 서양의 12별자리보다 2배 이상 세밀한 분류
- **다샤 시스템**: 행성 주기에 따른 시간대별 운명 예측
    """)
    
    st.markdown("### 💑 아쉬타쿠타(Ashta Kuta) 궁합 시스템")
    st.markdown("인도에서 전통적으로 결혼 전 두 사람의 궁합을 분석하는데 사용됩니다. 8가지(Ashta) 요소(Kuta)를 분석하여 평가합니다:")
    
    import pandas as pd
    kuta_data = pd.DataFrame({
        "쿠타": ["바르나(Varna)", "바쉬야(Vashya)", "타라(Tara)", "요니(Yoni)", 
                "그라하 마이트리", "가나(Gana)", "바쿠트(Bhakut)", "나디(Nadi)", "📊 총점"],
        "의미": ["영적 발전 호환성", "상호 매력과 지배력", "운명과 건강", "친밀함과 조화",
                "정신적 호환성", "기질과 성격", "감정적 조화", "건강과 자녀 운", ""],
        "100점 환산": ["~3점", "~6점", "~8점", "~11점", "~14점", "~17점", "~19점", "~22점", "💯 100점"]
    })
    st.dataframe(kuta_data, hide_index=True, use_container_width=True)
    
    st.success("✨ **50점 이상** = 좋은 궁합 | **70점 이상** = 우수한 궁합 | **85점 이상** = 천생연분! ✨")

def main():
    st.set_page_config(page_title="🌟 베딕 점성술 궁합", page_icon="🔮", layout="wide")
    apply_custom_css()

    st.markdown('<h1>🌟 베딕 점성술 궁합 분석 🌟</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#ffd700;font-style:italic;font-size:18px;">✨ 별들이 속삭이는 당신의 운명적 궁합을 발견하세요 ✨</p>', unsafe_allow_html=True)

    with st.expander("🕉️ 베딕 점성술에 대해 알아보기", expanded=False):
        show_vedic_info()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🌙 첫 번째 사람")
        name1 = st.text_input("이름", key="n1", placeholder="이름")
        date1 = st.date_input("생년월일", key="d1", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date(2026,12,31))
        time1 = st.text_input("출생 시간", key="t1", placeholder="예: 14:30 또는 오후 2시 30분")
        city1 = st.text_input("출생 도시", key="c1", placeholder="예: Seoul 또는 서울")
    with col2:
        st.markdown("### ⭐ 두 번째 사람")
        name2 = st.text_input("이름", key="n2", placeholder="이름")
        date2 = st.date_input("생년월일", key="d2", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date(2026,12,31))
        time2 = st.text_input("출생 시간", key="t2", placeholder="예: 09:15 또는 오전 9시 15분")
        city2 = st.text_input("출생 도시", key="c2", placeholder="예: Busan 또는 부산")

    st.markdown("---")
    _, btn_col, _ = st.columns([1,2,1])
    with btn_col:
        if st.button("🔮 운명의 궁합 분석하기 🔮", use_container_width=True):
            if not all([name1, name2, city1, city2]):
                st.error("❌ 모든 필드를 입력해주세요!")
                return

            with st.spinner("🌌 출생 장소 정보를 확인중..."):
                lat1, lon1, addr1 = get_location_coordinates(city1)
                lat2, lon2, addr2 = get_location_coordinates(city2)

                if not lat1:
                    st.error(f"❌ '{city1}' 위치를 찾을 수 없습니다.")
                    return
                if not lat2:
                    st.error(f"❌ '{city2}' 위치를 찾을 수 없습니다.")
                    return

                tz1 = get_timezone(lat1, lon1)
                tz2 = get_timezone(lat2, lon2)

            st.markdown("## 🌠 입력된 출생 정보")
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"""
**🌙 {name1}**

📅 생년월일: {date1}

⏰ 출생 시간: {time1}

📍 출생 장소: {addr1 or city1}

🌍 시간대: {tz1}
                """)
            with c2:
                st.info(f"""
**⭐ {name2}**

📅 생년월일: {date2}

⏰ 출생 시간: {time2}

📍 출생 장소: {addr2 or city2}

🌍 시간대: {tz2}
                """)

            st.markdown("---")
            st.markdown("## 🔮 아쉬타쿠타 궁합 분석")

            with st.spinner("✨ 베딕 차트를 계산하고 우주의 신비를 해석중... (약 30초 소요)"):
                p1_data = {"name": name1, "birth_date": str(date1), "birth_time": str(time1),
                          "city": city1, "lat": lat1, "lon": lon1, "timezone": tz1}
                p2_data = {"name": name2, "birth_date": str(date2), "birth_time": str(time2),
                          "city": city2, "lat": lat2, "lon": lon2, "timezone": tz2}
                analysis = analyze_compatibility_with_openai(p1_data, p2_data)

            st.markdown(f"### 💫 {name1} & {name2}의 운명적 궁합 💫")
            st.markdown(analysis)

            st.caption("⚠️ 이 분석은 오락 목적입니다. 실제 관계는 상호 이해와 존중이 기반입니다.")

if __name__ == "__main__":
    main()
