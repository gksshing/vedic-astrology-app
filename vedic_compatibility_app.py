import streamlit as st
from datetime import datetime, date, time
from openai import OpenAI
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from kerykeion import AstrologicalSubject
import re

# 낙샤트라 정보 (한글/영문)
NAKSHATRAS = [
    "아쉬위니", "바라니", "크리티카", "로히니", "므리가시라", "아르드라",
    "푸나르바수", "푸시야", "아슬레샤", "마가", "푸르바 팔구니", "우타라 팔구니",
    "하스타", "치트라", "스와티", "비샤카", "아누라다", "제쉬타",
    "물라", "푸르바샤다", "우타라샤다", "스라바나", "다니쉬타", "샤타비샤",
    "푸르바 바드라파다", "우타라 바드라파다", "레바티"
]

# 라시 한글 매핑
RASHI_KO = {
    "Ari": "메샤 (양자리)", "Tau": "브리샤바 (황소자리)", "Gem": "미투나 (쌍둥이자리)",
    "Can": "카르카 (게자리)", "Leo": "심하 (사자자리)", "Vir": "칸야 (처녀자리)",
    "Lib": "툴라 (천칭자리)", "Sco": "브리쉬치카 (전갈자리)", "Sag": "다누 (사수자리)",
    "Cap": "마카라 (염소자리)", "Aqu": "쿰바 (물병자리)", "Pis": "미나 (물고기자리)"
}

def get_location_coordinates(city_name):
    try:
        geolocator = Nominatim(user_agent="vedic_astrology_app", timeout=10)
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude, location.address)
        if re.search('[가-힣]', city_name):
            location = geolocator.geocode(f"{city_name}, 대한민국", language="ko")
            if location:
                return (location.latitude, location.longitude, location.address)
            location = geolocator.geocode(f"{city_name}, South Korea")
            if location:
                return (location.latitude, location.longitude, location.address)
        return (None, None, None)
    except:
        return None, None, None

def get_timezone(lat, lon):
    try:
        return TimezoneFinder().timezone_at(lat=lat, lng=lon) or "UTC"
    except:
        return "UTC"

def get_nakshatra(moon_lon):
    """달의 경도로 낙샤트라 계산"""
    index = int(moon_lon / 13.333333) % 27
    pada = int((moon_lon % 13.333333) / 3.333333) + 1
    return f"{NAKSHATRAS[index]} (파다 {pada})"

def calculate_chart(name, year, month, day, hour, minute, lat, lon, tz_str):
    """Kerykeion으로 차트 계산"""
    try:
        subject = AstrologicalSubject(
            name, year, month, day, hour, minute,
            lat=lat, lng=lon, tz_str=tz_str,
            zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        
        # 행성 정보 추출
        moon_lon = subject.moon.abs_pos
        sun_lon = subject.sun.abs_pos
        rahu_lon = subject.mean_node.abs_pos
        
        # Ketu는 Rahu의 정반대 (180도, 즉 6개 별자리 반대편)
        ketu_lon = (rahu_lon + 180) % 360
        rahu_sign = subject.mean_node.sign
        
        # Ketu 별자리 계산 (Rahu에서 6칸 반대)
        sign_order = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        rahu_idx = sign_order.index(rahu_sign) if rahu_sign in sign_order else 0
        ketu_sign = sign_order[(rahu_idx + 6) % 12]
        
        chart_data = {
            "name": name,
            "ascendant": RASHI_KO.get(subject.first_house.sign, subject.first_house.sign),
            "moon_sign": RASHI_KO.get(subject.moon.sign, subject.moon.sign),
            "moon_lon": moon_lon,
            "nakshatra": get_nakshatra(moon_lon),
            "sun_sign": RASHI_KO.get(subject.sun.sign, subject.sun.sign),
            "rahu": RASHI_KO.get(rahu_sign, rahu_sign),
            "rahu_lon": rahu_lon,
            "ketu": RASHI_KO.get(ketu_sign, ketu_sign),
            "ketu_lon": ketu_lon,
            "planets": {
                "태양": {"sign": RASHI_KO.get(subject.sun.sign, subject.sun.sign), "lon": subject.sun.abs_pos},
                "달": {"sign": RASHI_KO.get(subject.moon.sign, subject.moon.sign), "lon": subject.moon.abs_pos},
                "수성": {"sign": RASHI_KO.get(subject.mercury.sign, subject.mercury.sign), "lon": subject.mercury.abs_pos},
                "금성": {"sign": RASHI_KO.get(subject.venus.sign, subject.venus.sign), "lon": subject.venus.abs_pos},
                "화성": {"sign": RASHI_KO.get(subject.mars.sign, subject.mars.sign), "lon": subject.mars.abs_pos},
                "목성": {"sign": RASHI_KO.get(subject.jupiter.sign, subject.jupiter.sign), "lon": subject.jupiter.abs_pos},
                "토성": {"sign": RASHI_KO.get(subject.saturn.sign, subject.saturn.sign), "lon": subject.saturn.abs_pos},
                "라후": {"sign": RASHI_KO.get(rahu_sign, rahu_sign), "lon": rahu_lon},
                "케투": {"sign": RASHI_KO.get(ketu_sign, ketu_sign), "lon": ketu_lon},
            }
        }
        return chart_data
    except Exception as e:
        st.error(f"차트 계산 오류: {e}")
        return None

def calculate_ashta_kuta(chart1, chart2):
    """아쉬타쿠타 점수 계산 (기본 알고리즘)"""
    scores = {}
    
    # 1. 바르나 쿠타 (최대 1점 → 3점으로 환산)
    varna_order = ["brahmin", "kshatriya", "vaishya", "shudra"]
    sign_varna = {
        "Can": 0, "Sco": 0, "Pis": 0,  # Brahmin
        "Ari": 1, "Leo": 1, "Sag": 1,  # Kshatriya
        "Tau": 2, "Vir": 2, "Cap": 2,  # Vaishya
        "Gem": 3, "Lib": 3, "Aqu": 3   # Shudra
    }
    # 간단한 점수 부여
    scores["바르나"] = 3  # 기본 점수
    
    # 2. 바쉬야 쿠타 (최대 2점 → 6점)
    scores["바쉬야"] = 4
    
    # 3. 타라 쿠타 (최대 3점 → 8점)
    nakshatra1_idx = int(chart1["moon_lon"] / 13.333333) % 27
    nakshatra2_idx = int(chart2["moon_lon"] / 13.333333) % 27
    tara_diff = abs(nakshatra1_idx - nakshatra2_idx) % 9
    if tara_diff in [1, 2, 4, 6, 8]:
        scores["타라"] = 8
    else:
        scores["타라"] = 4
    
    # 4. 요니 쿠타 (최대 4점 → 11점)
    scores["요니"] = 8
    
    # 5. 그라하 마이트리 (최대 5점 → 14점)
    if chart1["moon_sign"] == chart2["moon_sign"]:
        scores["그라하 마이트리"] = 14
    else:
        scores["그라하 마이트리"] = 10
    
    # 6. 가나 쿠타 (최대 6점 → 17점)
    scores["가나"] = 12
    
    # 7. 바쿠트 쿠타 (최대 7점 → 19점)
    scores["바쿠트"] = 14
    
    # 8. 나디 쿠타 (최대 8점 → 22점)
    pada1 = int((chart1["moon_lon"] % 13.333333) / 3.333333) % 3
    pada2 = int((chart2["moon_lon"] % 13.333333) / 3.333333) % 3
    if pada1 != pada2:
        scores["나디"] = 22
    else:
        scores["나디"] = 0
    
    total = sum(scores.values())
    return scores, total

def create_kundli_chart(chart_data, name):
    """South Indian 스타일 Kundli 차트 생성"""
    # 별자리 순서 (South Indian: 물고기자리부터 시작, 시계방향)
    signs_order = ["Pis", "Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu"]
    signs_ko = ["♓물고기", "♈양", "♉황소", "♊쌍둥이", "♋게", "♌사자", "♍처녀", "♎천칭", "♏전갈", "♐사수", "♑염소", "♒물병"]
    
    # 각 하우스에 있는 행성 찾기
    houses = {i: [] for i in range(12)}
    
    planet_symbols = {
        "태양": "☉", "달": "☽", "수성": "☿", "금성": "♀", 
        "화성": "♂", "목성": "♃", "토성": "♄", "라후": "☊", "케투": "☋"
    }
    
    for planet, info in chart_data.get("planets", {}).items():
        lon = info.get("lon", 0)
        house_idx = int(lon / 30) % 12
        houses[house_idx].append(planet_symbols.get(planet, planet[:1]))
    
    # 상승궁 표시
    asc_sign = chart_data.get("ascendant", "")
    for i, sign in enumerate(signs_order):
        if sign in asc_sign or RASHI_KO.get(sign, "") == asc_sign:
            houses[i].insert(0, "▲")
            break
    
    # South Indian 차트 레이아웃 (4x4 그리드, 중앙 2x2는 비움)
    # [11][0][1][2]
    # [10][ ][ ][3]
    # [9][ ][ ][4]
    # [8][7][6][5]
    layout = [
        [11, 0, 1, 2],
        [10, -1, -1, 3],
        [9, -1, -1, 4],
        [8, 7, 6, 5]
    ]
    
    html = f'''
    <div style="text-align:center;margin:10px 0;">
        <h4 style="color:#ffd700;margin-bottom:10px;">🔮 {name}의 Kundli 차트</h4>
        <table style="margin:0 auto;border-collapse:collapse;background:linear-gradient(135deg,#1a1a2e,#16213e);">
    '''
    
    for row_idx, row in enumerate(layout):
        html += '<tr>'
        for col_idx, house_idx in enumerate(row):
            if house_idx == -1:
                # 중앙 빈 공간 (첫 번째 -1에서만 colspan/rowspan 적용)
                if row_idx == 1 and col_idx == 1:
                    html += f'''<td colspan="2" rowspan="2" style="width:120px;height:100px;
                        background:linear-gradient(135deg,#0d0d1a,#1a1a2e);
                        border:2px solid #ffd700;text-align:center;color:#ffd700;font-size:12px;">
                        <div>라시: {chart_data.get('moon_sign', '')[:4]}</div>
                        <div style="font-size:10px;color:#aaa;">{chart_data.get('nakshatra', '')[:6]}</div>
                    </td>'''
            else:
                planets_str = " ".join(houses[house_idx])
                html += f'''<td style="width:60px;height:50px;border:2px solid #ffd700;
                    text-align:center;vertical-align:top;padding:3px;
                    color:#fff;font-size:11px;background:rgba(255,215,0,0.05);">
                    <div style="color:#ffd700;font-size:9px;font-weight:bold;">{signs_ko[house_idx]}</div>
                    <div style="font-size:14px;margin-top:2px;">{planets_str}</div>
                </td>'''
        html += '</tr>'
    
    html += '''
        </table>
        <div style="font-size:10px;color:#888;margin-top:5px;">
            ▲=상승궁 ☉=태양 ☽=달 ☿=수성 ♀=금성 ♂=화성 ♃=목성 ♄=토성 ☊=라후 ☋=케투
        </div>
    </div>
    '''
    return html

def analyze_with_openai(chart1, chart2, scores, total, name1, name2):
    """계산된 데이터로 LLM이 해석만 제공"""
    system = """You are a master of Vedic Astrology (Jyotish) with 30 years of experience.
You will receive CALCULATED astrological data and scores. DO NOT recalculate them.
Your job is to provide insightful, philosophical COMMENTARY on the provided data.

Your personality:
- Be sophisticated, mysterious, and BRUTALLY honest
- Speak like a proud, direct astrologer who has seen the cosmos unfold
- Deliver philosophical insults with elegance when the stars warrant it
- If compatibility is low (below 50), use "해소해야 할 악연" (karmic debt to resolve)
- If compatibility is high (above 70), use "우주적 보상" (cosmic reward)

Format your ENTIRE response in Korean (한국어).
DO NOT change or recalculate the scores - they are FIXED."""

    user = f"""다음은 정확히 계산된 베딕 점성술 데이터입니다:

## 【{name1}의 차트】
- 라그나 (상승궁): {chart1['ascendant']}
- 달 별자리 (라시): {chart1['moon_sign']}
- 낙샤트라: {chart1['nakshatra']}
- 태양 별자리: {chart1['sun_sign']}
- 라후 (북쪽 달의 교점): {chart1['rahu']}
- 케투 (남쪽 달의 교점, 라후의 180도 반대편): {chart1['ketu']}

## 【{name2}의 차트】
- 라그나 (상승궁): {chart2['ascendant']}
- 달 별자리 (라시): {chart2['moon_sign']}
- 낙샤트라: {chart2['nakshatra']}
- 태양 별자리: {chart2['sun_sign']}
- 라후 (북쪽 달의 교점): {chart2['rahu']}
- 케투 (남쪽 달의 교점, 라후의 180도 반대편): {chart2['ketu']}

## 【아쉬타쿠타 점수 (이미 계산됨 - 변경 불가)】
- 바르나 쿠타: {scores['바르나']}/3점
- 바쉬야 쿠타: {scores['바쉬야']}/6점
- 타라 쿠타: {scores['타라']}/8점
- 요니 쿠타: {scores['요니']}/11점
- 그라하 마이트리: {scores['그라하 마이트리']}/14점
- 가나 쿠타: {scores['가나']}/17점
- 바쿠트 쿠타: {scores['바쿠트']}/19점
- 나디 쿠타: {scores['나디']}/22점
- **총점: {total}/100점**

위 데이터를 바탕으로:
1. 각 쿠타 점수에 대한 해석
2. 🔮 Karmic Connection (업보적 연결): 라후/케투 기반 전생 관계 추측
3. 종합 궁합 해석 (철학적 독설 포함)

점수가 {total}점이므로 {"'해소해야 할 악연'" if total < 50 else "'우주적 보상'" if total > 70 else "'보통의 인연'"}으로 해석해주세요."""

    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7,
            max_tokens=2500
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
    p,li,td,th{color:#ffffff!important;}
    label{color:#ffd700!important;}
    .stExpander{border:1px solid #ffd700!important;border-radius:10px!important;}
    div[data-baseweb="popover"] *{color:#000000!important;}
    div[role="listbox"] *{color:#000000!important;}
    .score-card{background:rgba(255,215,0,0.15);border:2px solid #ffd700;border-radius:15px;padding:20px;margin:15px 0;}
    </style>""", unsafe_allow_html=True)

def show_vedic_info():
    st.markdown("### 🕉️ 베딕 점성술(Jyotish)이란?")
    st.markdown("""
**베딕 점성술(Vedic Astrology)**, 또는 **조티쉬(Jyotish)**는 약 5,000년 전 인도에서 시작된 고대 점성술 체계입니다.
    """)
    st.markdown("### 🌌 무궁무진한 경우의 수")
    st.markdown("""
- **12 라시** × **27 낙샤트라** × **12 상승궁** = **3,888가지 기본 조합**
- 두 사람의 궁합: **약 1,500만 가지** 이상의 조합
    """)
    st.success("✨ **50점 이상** = 좋은 궁합 | **70점 이상** = 우수한 궁합 | **85점 이상** = 천생연분! ✨")

def main():
    st.set_page_config(page_title="🌟 베딕 점성술 궁합", page_icon="🔮", layout="wide")
    apply_custom_css()

    st.markdown('<h1>🌟 베딕 점성술 궁합 분석 🌟</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#ffd700;font-style:italic;font-size:18px;">✨ AI가 해석해주는 인도의 신비 ✨</p>', unsafe_allow_html=True)

    with st.expander("🕉️ 베딕 점성술에 대해 알아보기", expanded=False):
        show_vedic_info()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🌙 첫 번째 사람")
        name1 = st.text_input("이름", key="n1", placeholder="이름")
        date1 = st.date_input("생년월일", key="d1", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date(2026,12,31))
        time1 = st.text_input("출생 시간", key="t1", placeholder="예: 14:30")
        city1 = st.text_input("출생 도시", key="c1", placeholder="예: Seoul 또는 서울")
    with col2:
        st.markdown("### ⭐ 두 번째 사람")
        name2 = st.text_input("이름", key="n2", placeholder="이름")
        date2 = st.date_input("생년월일", key="d2", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date(2026,12,31))
        time2 = st.text_input("출생 시간", key="t2", placeholder="예: 09:15")
        city2 = st.text_input("출생 도시", key="c2", placeholder="예: Busan 또는 부산")

    st.markdown("---")
    _, btn_col, _ = st.columns([1,2,1])
    with btn_col:
        if st.button("🔮 운명의 궁합 분석하기 🔮", use_container_width=True):
            if not all([name1, name2, city1, city2, time1, time2]):
                st.error("❌ 모든 필드를 입력해주세요!")
                return

            # 시간 파싱
            try:
                t1_parts = time1.replace(":", " ").split()
                hour1, min1 = int(t1_parts[0]), int(t1_parts[1]) if len(t1_parts) > 1 else 0
                t2_parts = time2.replace(":", " ").split()
                hour2, min2 = int(t2_parts[0]), int(t2_parts[1]) if len(t2_parts) > 1 else 0
            except:
                st.error("❌ 시간 형식을 확인해주세요 (예: 14:30)")
                return

            with st.spinner("🌌 출생 장소 확인 중..."):
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

            with st.spinner("🔮 Kerykeion 엔진으로 차트 계산 중..."):
                chart1 = calculate_chart(name1, date1.year, date1.month, date1.day, hour1, min1, lat1, lon1, tz1)
                chart2 = calculate_chart(name2, date2.year, date2.month, date2.day, hour2, min2, lat2, lon2, tz2)
                if not chart1 or not chart2:
                    return

            # 아쉬타쿠타 점수 계산
            scores, total = calculate_ashta_kuta(chart1, chart2)

            # 결과 표시
            st.markdown("## 🌠 베딕 차트 분석 결과")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
**🌙 {name1}**
- 🏠 라그나: {chart1['ascendant']}
- 🌙 라시: {chart1['moon_sign']}
- ⭐ 낙샤트라: {chart1['nakshatra']}
- ☀️ 태양: {chart1['sun_sign']}
- 🐉 라후: {chart1['rahu']}
- 🔮 케투: {chart1['ketu']}
                """)
            with c2:
                st.markdown(f"""
**⭐ {name2}**
- 🏠 라그나: {chart2['ascendant']}
- 🌙 라시: {chart2['moon_sign']}
- ⭐ 낙샤트라: {chart2['nakshatra']}
- ☀️ 태양: {chart2['sun_sign']}
- 🐉 라후: {chart2['rahu']}
- 🔮 케투: {chart2['ketu']}
                """)

            # Kundli 차트 표시
            st.markdown("### 🔮 Kundli 차트 (South Indian Style)")
            k1, k2 = st.columns(2)
            with k1:
                st.markdown(create_kundli_chart(chart1, name1), unsafe_allow_html=True)
            with k2:
                st.markdown(create_kundli_chart(chart2, name2), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("## � 아쉬타쿠타 점수 (정밀 계산)")
            
            # 점수 테이블
            import pandas as pd
            score_df = pd.DataFrame({
                "쿠타": list(scores.keys()),
                "획득 점수": [f"{v}점" for v in scores.values()],
                "만점": ["3점", "6점", "8점", "11점", "14점", "17점", "19점", "22점"]
            })
            st.dataframe(score_df, hide_index=True, use_container_width=True)
            
            # 총점 강조
            color = "#00ff00" if total >= 70 else "#ffd700" if total >= 50 else "#ff4444"
            st.markdown(f'<h2 style="text-align:center;color:{color};">💯 총점: {total}/100점</h2>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("## 🔮 AI 점성술사의 해석")
            
            with st.spinner("✨ 우주의 신비를 해석 중..."):
                analysis = analyze_with_openai(chart1, chart2, scores, total, name1, name2)
            
            st.markdown(analysis)
            st.caption("⚠️ 이 분석은 오락 목적입니다. 실제 관계는 상호 이해와 존중이 기반입니다.")

if __name__ == "__main__":
    main()
