import streamlit as st
import pandas as pd
import time
from PIL import Image
import requests
from io import BytesIO
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 이미지 URL에서 이미지 크기 확인
def get_image_size(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img.size  # (width, height)

###############################################3

# 연회비 문자열을 숫자로 변환하는 함수
def lotte_fee_to_int(fee_str):
    if pd.isna(fee_str):
        return None
    return int(fee_str.replace('원', '').replace(',', ''))

def sinhan_fee_to_int(fee_str):
    if pd.isna(fee_str):
        return None
    if fee_str in ['없음', '무료']:
        return 0
    fee_str = fee_str.replace('원', '').replace(',', '')
    if '만' in fee_str:
        parts = fee_str.split('만')
        man = int(parts[0]) * 10000
        if len(parts) > 1 and '천' in parts[1]:
            cheon = int(parts[1].split('천')[0]) * 1000
            return man + cheon
        return man
    if '천' in fee_str:
        return int(fee_str.replace('천', '')) * 1000
    return int(fee_str)


# 데이터 로딩
lottecard_df = pd.read_csv('./Dataset/lottecard_result.csv')
sinhancard_df = pd.read_csv('./Dataset/sinhancard_result.csv')

# 롯데카드 전처리
# 1. date 날짜 형식 변경
lottecard_df['date'] = pd.to_datetime(lottecard_df['date'].str.strip(), format='%Y년 %m월 %d일').dt.strftime('%Y.%m.%d')


# 연회비 변환 함수를 각 카드사 데이터에 적용
# 연회비 변환 함수 적용하여 기존 열 업데이트
lottecard_df['total_fee_1'] = lottecard_df['total_fee_1'].apply(lotte_fee_to_int)
lottecard_df['total_fee_2'] = lottecard_df['total_fee_2'].apply(lotte_fee_to_int)
lottecard_df['total_fee_3'] = lottecard_df['total_fee_3'].apply(lotte_fee_to_int)

sinhancard_df['total_fee_1'] = sinhancard_df['total_fee_1'].apply(sinhan_fee_to_int)
sinhancard_df['total_fee_2'] = sinhancard_df['total_fee_2'].apply(sinhan_fee_to_int)
sinhancard_df['total_fee_3'] = sinhancard_df['total_fee_3'].apply(sinhan_fee_to_int)



# 왼쪽 사이드바 옵션
st.sidebar.header("필터 옵션")
selected_companies = st.sidebar.multiselect(
    "카드사 선택",
    ["롯데카드", "신한카드"],
    default=["롯데카드", "신한카드"]
)
# 연회비 범위 슬라이더
fee_range = st.sidebar.slider(
    "연회비 범위 선택",
    0, 100000, (15000, 30000) , step = 100 # step은 선택 단위 
)
min_fee, max_fee = fee_range



# 선택된 카드사에 따른 데이터 필터링
filtered_dfs = []
if "롯데카드" in selected_companies:
    filtered_dfs.append(lottecard_df)
if "신한카드" in selected_companies:
    filtered_dfs.append(sinhancard_df)

# 필터링된 데이터프레임 결합
filtered_df = pd.concat(filtered_dfs, ignore_index=True)

# 연회비 조건에 맞는 데이터 필터링
filtered_df = filtered_df[
    (filtered_df['total_fee_1'].between(min_fee, max_fee)) |
    (filtered_df['total_fee_2'].between(min_fee, max_fee)) |
    (filtered_df['total_fee_3'].between(min_fee, max_fee))
]

####################################################################################
# 유사도 검색 - tfidf
# 혜택 텍스트 데이터 준비
benefits = []
for i in range(1, 6):
    benefits.extend(lottecard_df[f"benefit_title_{i}"].dropna().unique())
    benefits.extend(lottecard_df[f"benefit_detail_{i}_1"].dropna().unique())
    benefits.extend(lottecard_df[f"benefit_detail_{i}_2"].dropna().unique())

# TF-IDF 벡터라이저 초기화 및 변환 수행
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(benefits)

# 사용자 입력 받기
user_query = st.sidebar.text_input("혜택에서 찾고 싶은 단어를 입력하세요")


# 사용자 쿼리에 대한 유사도 검색
if user_query:
    query_vector = vectorizer.transform([user_query])
    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix)

    def calculate_max_similarity(row):
        max_similarity = 0
        for i in range(1, 6):
            for key in [f"benefit_title_{i}", f"benefit_detail_{i}_1", f"benefit_detail_{i}_2"]:
                benefit = row.get(key, "")
                if benefit and benefit in benefits:
                    index = benefits.index(benefit)
                    max_similarity = max(max_similarity, cosine_similarities[0, index])
        return max_similarity

    # 각 행의 최대 유사도 점수 추가
    filtered_df['max_similarity'] = filtered_df.apply(calculate_max_similarity, axis=1)

    # 유사도가 높은 순으로 정렬 후, 0 인 값 삭제
    filtered_df = filtered_df[filtered_df['max_similarity'] > 0].sort_values(by='max_similarity', ascending=False)



###################################################################################
# 페이지당 표시할 카드 수 설정
cards_per_page = 5
num_pages = len(filtered_df) // cards_per_page + (1 if len(filtered_df) % cards_per_page else 0)

# 세션 상태에 페이지 번호 저장
if 'page_num' not in st.session_state:
    st.session_state['page_num'] = 1

# 현재 페이지 번호
page_num = st.session_state['page_num']

# 선택된 페이지에 해당하는 카드만 표시
start_idx = (page_num - 1) * cards_per_page
end_idx = start_idx + cards_per_page
paged_df = filtered_df.iloc[start_idx:end_idx]


# 필터링된 결과 처리 및 표시
for index, row in paged_df.iterrows():
    card_html = "<div style='display: flex; align-items: flex-start; margin-bottom: 20px;'>"

    # 이미지와 버튼을 포함하는 왼쪽 부분
    card_html += "<div style='margin-right: 20px;'>"
    card_html += f"<h3>{row['company']}</h3>"

    if pd.notna(row['img']):  # 이미지 URL이 있는 경우에만 표시
        width, height = get_image_size(row['img'])
        if width >= height:
            card_html += f"<img src='{row['img']}' style='width: 200px; display: block;'>"
        else:
            card_html += f"<img src='{row['img']}' style='width: 140px; display: block;'>"
    card_html += f"<br>"
    card_html += f"<p><strong>{row['title']}</strong></p>"
    card_html += f"<p><strong>출시 일자 :  </strong> {row['date']}    </p>"
    if pd.notna(row['url']):  # 링크 URL이 있는 경우에만 버튼 표시
        card_html += f"""<a href="{row['url']}" target="_blank" style="text-decoration: none;">
            <button style="background-color: #F3CED5; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: block; font-size: 16px; margin-top: 10px; cursor: pointer; border-radius: 5px;">
                카드 보러 가기
            </button>
        </a>"""

    card_html += "</div>"
        
    # 텍스트 정보 부분
    card_html += "<div>"


    # 연회비 정보
    card_html += "<p><strong>- 연회비 -</strong></p><ul>"
    for i in range(1, 4):
        fee_brand_key = f"fee_brand_{i}"
        total_fee_key = f"total_fee_{i}"
        if pd.notna(row[fee_brand_key]) and pd.notna(row[total_fee_key]):
            card_html += f"<li>{row[fee_brand_key]} : {int(row[total_fee_key]):,} 원</li>"
    card_html += "</ul> <br>"

    # 혜택 정보
    card_html += "<p><strong>- 혜택 -</strong></p><ul>"
    for i in range(1, 6):
        benefit_key = f"benefit_title_{i}"
        benefit_detail_1_key = f"benefit_detail_{i}_1"
        benefit_detail_2_key = f"benefit_detail_{i}_2"

        # 혜택 타이틀과 상세 정보 모두 확인
        if pd.notna(row[benefit_key]):
            card_html += f"<li>{row[benefit_key]}"
            if pd.notna(row[benefit_detail_1_key]):
                card_html += f" <ul><li>{row[benefit_detail_1_key]}</li></ul>"

            if pd.notna(row[benefit_detail_2_key]):
                card_html += f"<ul><li>{row[benefit_detail_2_key]}</li></ul>"

            card_html += "</li>"

    card_html += "</ul></div></div>"

    card_html += "<hr>"
    # HTML로 카드 정보 표시
    st.markdown(card_html, unsafe_allow_html=True)


# 페이지 네비게이션
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if page_num > 1:
        if st.button('이전 페이지'):
            st.session_state['page_num'] -= 1
            st.experimental_rerun()

with col2:
    st.write(f"페이지 {page_num} / {num_pages}")

with col3:
    if page_num < num_pages:
        if st.button('다음 페이지'):
            st.session_state['page_num'] += 1
            st.experimental_rerun()
