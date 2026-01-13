import streamlit as st
from datetime import datetime, date, time
from openai import OpenAI
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

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

RASHI_MAPPING = {"Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3, "Leo": 4, "Virgo": 5,
                "Libra": 6, "Scorpio": 7, "Sagittarius": 8, "Capricorn": 9, "Aquarius": 10, "Pisces": 11}

def get_location_coordinates(city_name):
    try:
        geolocator = Nominatim(user_agent="vedic_astrology_app")
        location = geolocator.geocode(city_name)
        return (location.latitude, location.longitude) if location else (None, None)
    except: return None, None

def get_timezone(lat, lon):
    try: return TimezoneFinder().timezone_at(lat=lat, lng=lon) or "UTC"
    except: return "UTC"

def calculate_nakshatra(moon_longitude):
    return NAKSHATRAS[int(moon_longitude / 13.333333) % 27]

def calculate_vedic_chart(birth_date, birth_time, lat, lon):
    try:
        tz = pytz.timezone(get_timezone(lat, lon))
        dt = tz.localize(datetime.combine(birth_date, birth_time))
        utc_offset = dt.utcoffset().total_seconds() / 3600
        offset_str = f"{'+' if utc_offset >= 0 else '-'}{abs(int(utc_offset)):02d}:{int((abs(utc_offset) % 1) * 60):02d}"
        chart = Chart(Datetime(birth_date.strftime("%Y/%m/%d"), birth_time.strftime("%H:%M"), offset_str), GeoPos(lat, lon))
        asc, moon, sun = chart.get(const.ASC), chart.get(const.MOON), chart.get(const.SUN)
        planets = {p: {'sign': chart.get(p).sign, 'longitude': chart.get(p).lon} 
                   for p in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]}
        return {"ascendant": RASHIS[RASHI_MAPPING.get(asc.sign, 0)], "moon_sign": RASHIS[RASHI_MAPPING.get(moon.sign, 0)],
                "moon_longitude": moon.lon, "nakshatra": calculate_nakshatra(moon.lon),
                "sun_sign": RASHIS[RASHI_MAPPING.get(sun.sign, 0)], "planets": planets, "timezone": str(tz)}
    except Exception as e: st.error(f"차트 계산 오류: {e}"); return None

def create_south_indian_chart(chart_data, name):
    houses = [""] * 12
    if chart_data and 'planets' in chart_data:
        symbols = {'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄'}
        for p, info in chart_data['planets'].items():
            houses[RASHI_MAPPING.get(info['sign'], 0)] += symbols.get(p, p[:2]) + " "
    if chart_data:
        for i, r in enumerate(RASHIS):
            if chart_data['ascendant'] == r: houses[i] = "★ASC★<br>" + houses[i]; break
    signs = ["물고기","양","황소","쌍둥이","물병","","","게","염소","","","사자","사수","전갈","천칭","처녀"]
    idx = [[11,0,1,2],[10,-1,-1,3],[9,-1,-1,4],[8,7,6,5]]
    html = f'<div style="text-align:center;"><h4 style="color:#ffd700;">🌙 {name}의 베딕 차트</h4><table style="margin:0 auto;border-collapse:collapse;background:linear-gradient(135deg,#1a1a2e,#16213e);">'
    for row in idx:
        html += '<tr>'
        for c in row:
            if c == -1: continue
            cs = ' colspan="2" rowspan="2"' if c == -1 else ''
            content = f'<b>{["물고기","양","황소","쌍둥이","게","사자","처녀","천칭","전갈","사수","염소","물병"][c]}</b><br>{houses[c]}' if c >= 0 else ''
            html += f'<td style="width:70px;height:50px;border:2px solid #ffd700;text-align:center;color:#e0e0e0;font-size:10px;"{cs}>{content}</td>'
        html += '</tr>'
    return html + '</table></div>'

def analyze_compatibility_with_openai(p1, p2, n1, n2):
    system = """You are a master of Vedic Astrology with 30 years of experience. Analyze the 'Ashta Kuta' compatibility between these two sets of birth data. Be sophisticated, mysterious, and brutally honest. If the stars say it's a disaster, call it a celestial catastrophe. Format your entire response in Korean. IMPORTANT: Convert the traditional 36-point scale to 100-point scale for easier understanding."""
    user = f"""다음 두 사람의 베딕 점성술 데이터를 바탕으로 아쉬타쿠타 궁합을 분석해주세요:
【{n1}】라그나: {p1['ascendant']}, 라시: {p1['moon_sign']}, 낙샤트라: {p1['nakshatra']}, 태양: {p1['sun_sign']}
【{n2}】라그나: {p2['ascendant']}, 라시: {p2['moon_sign']}, 낙샤트라: {p2['nakshatra']}, 태양: {p2['sun_sign']}
8가지 쿠타를 분석하고, 각 쿠타 점수와 총점을 100점 만점 스케일로 환산하여 제공해주세요. (원래 36점 만점 → 100점 만점으로 변환)"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        return client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system},{"role":"user","content":user}], temperature=0.8, max_tokens=2000).choices[0].message.content
    except Exception as e: return f"❌ API 오류: {e}"

def apply_custom_css():
    st.markdown("""<style>
    .stApp{background:linear-gradient(135deg,#0d0d1a,#1a1a2e,#16213e);}
    h1{color:#ffd700!important;text-align:center;text-shadow:0 0 20px rgba(255,215,0,0.5);}
    h2,h3{color:#e6c200!important;}
    .stButton>button{background:linear-gradient(135deg,#ffd700,#ff8c00)!important;color:#1a1a2e!important;border:none!important;border-radius:25px!important;padding:15px 40px!important;font-weight:bold!important;box-shadow:0 0 20px rgba(255,215,0,0.4)!important;}
    .info-card{background:rgba(255,215,0,0.1);border-left:4px solid #ffd700;padding:15px;margin:10px 0;border-radius:0 10px 10px 0;}
    .result-box{background:linear-gradient(135deg,rgba(26,26,46,0.9),rgba(22,33,62,0.9));border:2px solid #ffd700;border-radius:15px;padding:25px;margin:20px 0;box-shadow:0 0 30px rgba(255,215,0,0.2);}
    .vedic-info{background:rgba(139,69,19,0.2);border:1px solid #daa520;border-radius:15px;padding:20px;margin:20px 0;}
    </style>""", unsafe_allow_html=True)

def show_vedic_info():
    st.markdown("""<div class="vedic-info">
    <h3 style="color:#ffd700;text-align:center;">🕉️ 베딕 점성술(Jyotish)이란?</h3>
    <p style="color:#e0e0e0;line-height:1.8;"><b>베딕 점성술(Vedic Astrology)</b>, 또는 <b>조티쉬(Jyotish)</b>는 약 5,000년 전 인도에서 시작된 고대 점성술 체계입니다. "조티쉬"는 산스크리트어로 "빛의 과학" 또는 "천체의 지혜"를 의미합니다.</p>

    <h4 style="color:#ffd700;">🌌 무궁무진한 경우의 수</h4>
    <p style="color:#e0e0e0;">베딕 점성술의 가장 큰 강점은 그 <b>엄청난 조합의 다양성</b>입니다:</p>
    <ul style="color:#e0e0e0;">
    <li><b>12 라시(별자리)</b> × <b>27 낙샤트라(달의 별자리)</b> × <b>12 상승궁</b> = <b>3,888가지 기본 조합</b></li>
    <li>여기에 7개 행성의 위치, 12개 하우스 배치, 행성 간 각도(Aspects)까지 고려하면...</li>
    <li>🔢 <b>수십억 가지 이상의 고유한 차트 조합</b>이 가능합니다!</li>
    <li>두 사람의 궁합 분석 시: <b>3,888² = 약 1,500만 가지</b> 이상의 기본 조합</li>
    </ul>
    <p style="color:#b8860b;font-style:italic;">→ 이것이 베딕 점성술이 각 개인의 독특한 운명을 정밀하게 읽어낼 수 있는 이유입니다.</p>

    <h4 style="color:#ffd700;">🌙 서양 점성술과의 차이점</h4>
    <ul style="color:#e0e0e0;">
    <li><b>항성 황도대(Sidereal Zodiac)</b>: 실제 별자리 위치 기반 (서양은 계절 기반)</li>
    <li><b>달 중심</b>: 태양보다 달의 위치를 더 중요시함</li>
    <li><b>27 낙샤트라</b>: 서양의 12별자리보다 2배 이상 세밀한 분류</li>
    <li><b>다샤 시스템</b>: 행성 주기에 따른 시간대별 운명 예측</li>
    </ul>

    <h4 style="color:#ffd700;">💑 아쉬타쿠타(Ashta Kuta) 궁합 시스템</h4>
    <p style="color:#e0e0e0;">인도에서 전통적으로 결혼 전 두 사람의 궁합을 분석하는데 사용됩니다. 8가지(Ashta) 요소(Kuta)를 분석하여 평가합니다:</p>
    <table style="width:100%;color:#e0e0e0;border-collapse:collapse;margin:10px 0;">
    <tr style="background:rgba(255,215,0,0.2);"><th style="padding:8px;border:1px solid #daa520;">쿠타</th><th style="padding:8px;border:1px solid #daa520;">의미</th><th style="padding:8px;border:1px solid #daa520;">100점 환산</th></tr>
    <tr><td style="padding:8px;border:1px solid #555;">바르나(Varna)</td><td style="padding:8px;border:1px solid #555;">영적 발전 호환성</td><td style="padding:8px;border:1px solid #555;text-align:center;">~3점</td></tr>
    <tr><td style="padding:8px;border:1px solid #555;">바쉬야(Vashya)</td><td style="padding:8px;border:1px solid #555;">상호 매력과 지배력</td><td style="padding:8px;border:1px solid #555;text-align:center;">~6점</td></tr>
    <tr><td style="padding:8px;border:1px solid #555;">타라(Tara)</td><td style="padding:8px;border:1px solid #555;">운명과 건강</td><td style="padding:8px;border:1px solid #555;text-align:center;">~8점</td></tr>
    <tr><td style="padding:8px;border:1px solid #555;">요니(Yoni)</td><td style="padding:8px;border:1px solid #555;">친밀함과 조화</td><td style="padding:8px;border:1px solid #555;text-align:center;">~11점</td></tr>
    <tr><td style="padding:8px;border:1px solid #555;">그라하 마이트리(Graha Maitri)</td><td style="padding:8px;border:1px solid #555;">정신적 호환성</td><td style="padding:8px;border:1px solid #555;text-align:center;">~14점</td></tr>
    <tr><td style="padding:8px;border:1px solid #555;">가나(Gana)</td><td style="padding:8px;border:1px solid #555;">기질과 성격</td><td style="padding:8px;border:1px solid #555;text-align:center;">~17점</td></tr>
    <tr><td style="padding:8px;border:1px solid #555;">바쿠트(Bhakut)</td><td style="padding:8px;border:1px solid #555;">감정적 조화</td><td style="padding:8px;border:1px solid #555;text-align:center;">~19점</td></tr>
    <tr><td style="padding:8px;border:1px solid #555;">나디(Nadi)</td><td style="padding:8px;border:1px solid #555;">건강과 자녀 운</td><td style="padding:8px;border:1px solid #555;text-align:center;">~22점</td></tr>
    <tr style="background:rgba(255,215,0,0.1);"><td colspan="2" style="padding:8px;border:1px solid #daa520;font-weight:bold;">총점</td><td style="padding:8px;border:1px solid #daa520;text-align:center;font-weight:bold;">100점</td></tr>
    </table>
    <p style="color:#b8860b;font-style:italic;text-align:center;margin-top:15px;">✨ 50점 이상 = 좋은 궁합 | 70점 이상 = 우수한 궁합 | 85점 이상 = 천생연분! ✨</p>
    </div>""", unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="🌟 베딕 점성술 궁합", page_icon="🔮", layout="wide")
    apply_custom_css()

    st.markdown('<h1>🌟 베딕 점성술 궁합 분석 🌟</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#b8860b;font-style:italic;">✨ 별들이 속삭이는 당신의 운명적 궁합을 발견하세요 ✨</p>', unsafe_allow_html=True)

    with st.expander("🕉️ 베딕 점성술에 대해 알아보기", expanded=False):
        show_vedic_info()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🌙 첫 번째 사람")
        name1 = st.text_input("이름", key="n1", placeholder="이름")
        date1 = st.date_input("생년월일", key="d1", value=date(1990,1,1))
        time1 = st.time_input("출생 시간", key="t1", value=time(12,0))
        city1 = st.text_input("출생 도시", key="c1", placeholder="예: Seoul")
    with col2:
        st.markdown("### ⭐ 두 번째 사람")
        name2 = st.text_input("이름", key="n2", placeholder="이름")
        date2 = st.date_input("생년월일", key="d2", value=date(1990,1,1))
        time2 = st.time_input("출생 시간", key="t2", value=time(12,0))
        city2 = st.text_input("출생 도시", key="c2", placeholder="예: Busan")

    st.markdown("---")
    _, btn_col, _ = st.columns([1,2,1])
    with btn_col:
        if st.button("🔮 운명의 궁합 분석하기 🔮", use_container_width=True):
            if not all([name1, name2, city1, city2]): st.error("❌ 모든 필드를 입력해주세요!"); return
            with st.spinner("🌌 별들의 위치를 계산중..."):
                lat1, lon1 = get_location_coordinates(city1)
                lat2, lon2 = get_location_coordinates(city2)
                if not lat1: st.error(f"❌ '{city1}' 위치를 찾을 수 없습니다."); return
                if not lat2: st.error(f"❌ '{city2}' 위치를 찾을 수 없습니다."); return
                chart1, chart2 = calculate_vedic_chart(date1, time1, lat1, lon1), calculate_vedic_chart(date2, time2, lat2, lon2)
                if not chart1 or not chart2: return

            st.markdown("## 🌠 베딕 차트 분석 결과")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f'<div class="info-card"><h4 style="color:#ffd700;">🌙 {name1}</h4><p>🏠 라그나: {chart1["ascendant"]}</p><p>🌙 라시: {chart1["moon_sign"]}</p><p>⭐ 낙샤트라: {chart1["nakshatra"]}</p><p>☀️ 태양: {chart1["sun_sign"]}</p></div>', unsafe_allow_html=True)
                st.markdown(create_south_indian_chart(chart1, name1), unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="info-card"><h4 style="color:#ffd700;">⭐ {name2}</h4><p>🏠 라그나: {chart2["ascendant"]}</p><p>🌙 라시: {chart2["moon_sign"]}</p><p>⭐ 낙샤트라: {chart2["nakshatra"]}</p><p>☀️ 태양: {chart2["sun_sign"]}</p></div>', unsafe_allow_html=True)
                st.markdown(create_south_indian_chart(chart2, name2), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("## 🔮 아쉬타쿠타 궁합 분석")
            with st.spinner("✨ 우주의 신비가 해석중..."):
                analysis = analyze_compatibility_with_openai(chart1, chart2, name1, name2)
            st.markdown(f'<div class="result-box"><h3 style="color:#ffd700;text-align:center;">💫 {name1} & {name2}의 운명적 궁합 💫</h3><hr style="border-color:#ffd700;opacity:0.3;"><div style="color:#e0e0e0;line-height:1.8;">{analysis.replace(chr(10),"<br>")}</div></div>', unsafe_allow_html=True)
            st.markdown('<p style="text-align:center;color:#666;font-size:12px;">⚠️ 이 분석은 오락 목적입니다. 실제 관계는 상호 이해와 존중이 기반입니다.</p>', unsafe_allow_html=True)

if __name__ == "__main__": main()
