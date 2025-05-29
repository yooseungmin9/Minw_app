import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
import json
from datetime import datetime, timedelta

# 서비스 키 (공공데이터포털에서 발급)
SERVICE_KEY = "L5PyqDviKAL0jSdGt5iPksot8IwBbYS7R27iyt6kKB0q6A+A2TS6Cn/cJ5CCsBWFPB/M+pgxnZwQiAhp9+TQ0A=="

# 기상청 API 엔드포인트
BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"

st.set_page_config(
    page_title="실시간 날씨 정보",
    page_icon="🌤️",
    layout="wide"
)

st.title("승민이의 실시간 날씨 정보")
st.markdown("---")

# 사이드바 - 지역 선택 기능
st.sidebar.header("🌍 지역 선택")

# 지역별 격자 좌표 정의 (기상청 API용)
regions = {
    '서울': {
        'lat': 37.5665, 'lon': 126.9780,
        'nx': 60, 'ny': 127
    },
    '대구': {
        'lat': 35.8714, 'lon': 128.6014,
        'nx': 89, 'ny': 90
    },
    '부산': {
        'lat': 35.1796, 'lon': 129.0756,
        'nx': 98, 'ny': 76
    },
    '인천': {
        'lat': 37.4563, 'lon': 126.7052,
        'nx': 55, 'ny': 124
    },
    '광주': {
        'lat': 35.1595, 'lon': 126.8526,
        'nx': 58, 'ny': 74
    },
    '대전': {
        'lat': 36.3504, 'lon': 127.3845,
        'nx': 67, 'ny': 100
    },
    '울산': {
        'lat': 35.5384, 'lon': 129.3114,
        'nx': 102, 'ny': 84
    },
    '경기': {
        'lat': 37.4138, 'lon': 127.5183,
        'nx': 60, 'ny': 120
    },
    '강원': {
        'lat': 37.8228, 'lon': 128.1555,
        'nx': 73, 'ny': 134
    },
    '충북': {
        'lat': 36.6357, 'lon': 127.4917,
        'nx': 69, 'ny': 107
    },
    '충남': {
        'lat': 36.5184, 'lon': 126.8000,
        'nx': 68, 'ny': 100
    },
    '전북': {
        'lat': 35.7175, 'lon': 127.1530,
        'nx': 63, 'ny': 89
    },
    '전남': {
        'lat': 34.8679, 'lon': 126.9910,
        'nx': 51, 'ny': 67
    },
    '경북': {
        'lat': 36.4919, 'lon': 128.8889,
        'nx': 87, 'ny': 106
    },
    '경남': {
        'lat': 35.4606, 'lon': 128.2132,
        'nx': 91, 'ny': 77
    },
    '제주': {
        'lat': 33.4996, 'lon': 126.5312,
        'nx': 52, 'ny': 38
    },
    '세종': {
        'lat': 36.4800, 'lon': 127.2890,
        'nx': 66, 'ny': 103
    }
}

# 기본값을 대구로 설정
default_region = '대구'
selected_region = st.sidebar.selectbox(
    "지역을 선택하세요:",
    options=list(regions.keys()),
    index=list(regions.keys()).index(default_region)
)

# 현재 선택된 지역 정보 표시
st.sidebar.info(f"📍 현재 선택: **{selected_region}**")

# 함수들 정의
@st.cache_data(ttl=600)  # 10분 캐시
def get_current_weather(nx, ny, service_key):
    """현재 날씨 정보 조회 (초단기실황)"""
    
    now = datetime.now()
    # 매시간 40분에 업데이트되므로 조정
    if now.minute < 40:
        now = now - timedelta(hours=1)
    
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")
    
    url = f"{BASE_URL}/getUltraSrtNcst"
    params = {
        'serviceKey': service_key,
        'pageNo': '1',
        'numOfRows': '1000',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': nx,
        'ny': ny
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['response']['header']['resultCode'] == '00':
            items = data['response']['body']['items']['item']
            
            # 데이터 파싱
            weather_info = {}
            for item in items:
                category = item['category']
                value = item['obsrValue']
                weather_info[category] = value
            
            return weather_info
        else:
            st.error(f"API 오류: {data['response']['header']['resultMsg']}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"날씨 데이터를 가져오는데 실패했습니다: {e}")
        return None

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_forecast_data(nx, ny, service_key):
    """단기예보 정보 조회 (3일)"""
    
    now = datetime.now()
    
    # 예보 발표 시간에 맞춰 base_time 설정
    if now.hour < 2:
        base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        base_time = "2300"
    elif now.hour < 5:
        base_date = now.strftime("%Y%m%d")
        base_time = "0200"
    elif now.hour < 8:
        base_date = now.strftime("%Y%m%d")
        base_time = "0500"
    elif now.hour < 11:
        base_date = now.strftime("%Y%m%d")
        base_time = "0800"
    elif now.hour < 14:
        base_date = now.strftime("%Y%m%d")
        base_time = "1100"
    elif now.hour < 17:
        base_date = now.strftime("%Y%m%d")
        base_time = "1400"
    elif now.hour < 20:
        base_date = now.strftime("%Y%m%d")
        base_time = "1700"
    elif now.hour < 23:
        base_date = now.strftime("%Y%m%d")
        base_time = "2000"
    else:
        base_date = now.strftime("%Y%m%d")
        base_time = "2300"
    
    url = f"{BASE_URL}/getVilageFcst"
    params = {
        'serviceKey': service_key,
        'pageNo': '1',
        'numOfRows': '1000',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': nx,
        'ny': ny
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['response']['header']['resultCode'] == '00':
            items = data['response']['body']['items']['item']
            
            # 날짜별로 데이터 정리
            forecast_data = {}
            for item in items:
                date = item['fcstDate']
                time = item['fcstTime']
                category = item['category']
                value = item['fcstValue']
                
                if date not in forecast_data:
                    forecast_data[date] = {}
                if time not in forecast_data[date]:
                    forecast_data[date][time] = {}
                
                forecast_data[date][time][category] = value
            
            return forecast_data
        else:
            st.error(f"API 오류: {data['response']['header']['resultMsg']}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"예보 데이터를 가져오는데 실패했습니다: {e}")
        return None

def parse_kma_data(weather_items):
    """기상청 API 응답 데이터를 파싱"""
    weather_dict = {}
    
    for item in weather_items:
        category = item['category']
        value = item['obsrValue'] if 'obsrValue' in item else item['fcstValue']
        weather_dict[category] = value
    
    return weather_dict

def get_weather_description(sky_code, pty_code):
    """하늘상태와 강수형태 코드를 날씨 설명으로 변환"""
    # 강수형태 (PTY)
    if pty_code == '1':
        return "비", "🌧️"
    elif pty_code == '2':
        return "비/눈", "🌨️"
    elif pty_code == '3':
        return "눈", "❄️"
    elif pty_code == '4':
        return "소나기", "🌦️"
    
    # 하늘상태 (SKY)
    if sky_code == '1':
        return "맑음", "☀️"
    elif sky_code == '3':
        return "구름많음", "⛅"
    elif sky_code == '4':
        return "흐림", "☁️"
    
    return "정보없음", "🌤️"

def get_weather_color(temp):
    """온도에 따른 마커 색상 결정"""
    temp = float(temp) if temp != 'N/A' else 0
    if temp >= 30:
        return 'red'
    elif temp >= 20:
        return 'orange'
    elif temp >= 10:
        return 'green'
    elif temp >= 0:
        return 'blue'
    else:
        return 'purple'

def create_weather_map(region_info, weather_data, weather_desc, weather_icon):
    """기상청 데이터로 날씨 지도 생성"""
    
    # 지도 생성
    m = folium.Map(
        location=[region_info['lat'], region_info['lon']], 
        zoom_start=10
    )
    
    # 온도에 따른 색상 결정
    temp = float(weather_data.get('T1H', 0))
    color = get_weather_color(temp)
    
    popup_html = f"""
    <div style="font-family: Arial; width: 200px;">
        <h4>{selected_region}</h4>
        <p><b>온도:</b> {weather_data.get('T1H', 'N/A')}°C</p>
        <p><b>습도:</b> {weather_data.get('REH', 'N/A')}%</p>
        <p><b>풍속:</b> {weather_data.get('WSD', 'N/A')} m/s</p>
        <p><b>날씨:</b> {weather_desc}</p>
        <p><b>강수량:</b> {weather_data.get('RN1', '0')} mm</p>
    </div>
    """
    
    folium.Marker(
        location=[region_info['lat'], region_info['lon']],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"{weather_icon} {temp}°C",
        icon=folium.Icon(color=color, icon='cloud')
    ).add_to(m)
    
    # 지도 표시
    folium_static(m, width=700, height=500)

def show_kma_forecast(region_info, service_key):
    """기상청 예보 데이터 표시"""
    forecast_items = get_forecast_data(region_info['nx'], region_info['ny'], service_key)
    
    if forecast_items:
        st.subheader("📅 단기예보 (3일)")
        
        # 일별 예보 카드 표시
        cols = st.columns(3)
        for i, (date, times) in enumerate(list(forecast_items.items())[:3]):
            with cols[i]:
                # 대표 시간대 데이터 (12시)
                representative_time = '1200' if '1200' in times else list(times.keys())[0]
                day_data = times[representative_time]
                
                temp = day_data.get('TMP', 'N/A')
                sky_code = day_data.get('SKY', '1')
                pty_code = day_data.get('PTY', '0')
                
                desc, icon = get_weather_description(sky_code, pty_code)
                
                # 날짜 포맷팅
                formatted_date = f"{date[4:6]}/{date[6:8]}"
                
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; border: 1px solid #ddd; border-radius: 10px;">
                    <h4>{formatted_date}</h4>
                    <div style="font-size: 2em;">{icon}</div>
                    <p><b>{temp}°C</b></p>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)

# 메인 애플리케이션
def main():
    # 지역 정보 가져오기
    region_info = regions[selected_region]
    
    # 업데이트 버튼
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 날씨 업데이트"):
            st.cache_data.clear()
            st.rerun()
    
    # 현재 날씨 데이터
    current_weather = get_current_weather(region_info['nx'], region_info['ny'], SERVICE_KEY)
    
    if current_weather:
        # 주요 정보 추출
        temp = current_weather.get('T1H', 'N/A')
        humidity = current_weather.get('REH', 'N/A')
        wind_speed = current_weather.get('WSD', 'N/A')
        rainfall = current_weather.get('RN1', '0')
        
        # 메트릭 표시
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🌡️ 현재 온도",
                value=f"{temp}°C" if temp != 'N/A' else "정보없음"
            )
        
        with col2:
            st.metric(
                label="💧 습도",
                value=f"{humidity}%" if humidity != 'N/A' else "정보없음"
            )
        
        with col3:
            st.metric(
                label="💨 풍속",
                value=f"{wind_speed} m/s" if wind_speed != 'N/A' else "정보없음"
            )
        
        # 현재 날씨 상태 (기본값 설정)
        weather_desc = "맑음"
        weather_icon = "☀️"
        
        st.subheader(f"{weather_icon} {selected_region} 날씨")
        st.write(f"**현재 상태:** {weather_desc}")
        
        # 추가 정보
        if rainfall != '0' and rainfall != 'N/A':
            st.info(f"☔ 1시간 강수량: {rainfall}mm")
        
        # 지도 생성
        st.subheader(f"📍 {selected_region} 날씨 지도")
        create_weather_map(region_info, current_weather, weather_desc, weather_icon)
        
        # 예보 정보
        show_kma_forecast(region_info, SERVICE_KEY)
        
    else:
        st.error("현재 날씨 정보를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")
        st.info("기상청 API는 간헐적으로 지연이 발생할 수 있습니다.")

if __name__ == "__main__":
    main()
