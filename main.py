import streamlit as st
import pandas as pd
import time
from PIL import Image
import requests
from io import BytesIO

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
##############################################################################

# 사용자 쿼리에 따른 검색어 설정
query_keyword_mapping = {
    "카페": ["커피", "스타벅스", "커피숍", "다방"],
    "커피숍": ["커피", "스타벅스", "다방"],
    "음료": ["커피", "스타벅스", "커피숍", "다방"],

    #################
    "식당" : ["요식", "음식", "외식", "식사", "배달"],
    "음식" : ["요식", "식당", "외식", "식사", "배달"],
    "외식" : ["요식", "음식", "식당", "식사", "배달"],
    "식사" : ["요식", "음식", "외식", "식당", "배달"],
    "요식" : ["요식", "음식", "외식", "식사", "배달"],
    "배달" : ["요식", "음식", "외식", "식사", "식당"],

    #################
    "문화" : ["영화", "여가", "쇼핑"],
    "여가" : ["영화", "문화", "쇼핑"],
    
    "쇼핑" : ["백화점", ""],
    #################
    "구독": ["멤버십", "스트리밍"],
    "멤버십": ["구독", "스트리밍"],
    "스트리밍": ["멤버십", "구독"],
    ##################
    "포인트" : ["적립"],
    "적립" : ["포인트"],
    ##################
    "버스" : ["지하철", "교통", "대중교통", "기차", "택시", "대중 교통"],
    "지하철" : ["버스", "교통", "대중교통", "기차", "택시", "대중 교통"],
    "교통" : ["지하철", "버스", "대중교통", "기차", "택시", "대중 교통"],
    "기차" : ["지하철", "교통", "대중교통", "버스", "택시", "KTX", "대중 교통"],
    "ktx" : ["지하철", "교통", "대중교통", "버스", "택시", "KTX", "대중 교통"],
    "택시" : ["지하철", "교통", "대중교통", "버스", "기차", "대중 교통"],

    "주유소" : ["주유", "기름", "충전"],
    "주유" : ["주유소", "기름", "충전"],
    "기름" : ["주유", "주유소", "충전"],
    "충전" : ["주유", "기름", "주유소"],

}

##############################################################################
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

#########################################################################################


# 초기 세션 상태 설정
if 'page' not in st.session_state:
    st.session_state['page'] = 'dashboard'

# 사이드바에 페이지 선택 버튼 추가
st.sidebar.button("소개", on_click=lambda: st.session_state.update({'page': 'intro'}))
st.sidebar.button("대시보드", on_click=lambda: st.session_state.update({'page': 'dashboard'}))


# 현재 페이지에 따른 내용 표시
if st.session_state['page'] == 'dashboard':
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
    temp_filtered_df = pd.concat(filtered_dfs, ignore_index=True)

    # 연회비 조건에 맞는 데이터 필터링
    fee_filtered_df = temp_filtered_df[
        (temp_filtered_df['total_fee_1'].between(min_fee, max_fee, inclusive="right")) |
        (temp_filtered_df['total_fee_2'].between(min_fee, max_fee, inclusive="right")) |
        (temp_filtered_df['total_fee_3'].between(min_fee, max_fee, inclusive="right"))
    ]


    # 유사도 검색
    # 혜택 텍스트 데이터 준비
    benefits = []
    for i in range(1, 6):
        benefits.extend(lottecard_df[f"benefit_title_{i}"].dropna().unique())
        benefits.extend(lottecard_df[f"benefit_detail_{i}_1"].dropna().unique())
        benefits.extend(lottecard_df[f"benefit_detail_{i}_2"].dropna().unique())

    # 사용자 입력 받기
    user_query = st.sidebar.text_input("혜택에서 찾고 싶은 단어를 입력하세요")

    # 혜택 관련 검색 수행
    search_queries = [user_query]
    if user_query not in benefits:
        # 쿼리 확장 로직 적용
        expanded_queries = query_keyword_mapping.get(user_query, [user_query])
        search_queries.extend(expanded_queries)

    # 해당 검색어가 포함된 혜택을 가진 카드 필터링
    additional_filtered_dfs = []
    for query in search_queries:
        for i in range(1, 6):
            additional_filtered_dfs.append(fee_filtered_df[fee_filtered_df[f"benefit_title_{i}"].astype(str).str.contains(query, na=False)])
            additional_filtered_dfs.append(fee_filtered_df[fee_filtered_df[f"benefit_detail_{i}_1"].astype(str).str.contains(query, na=False)])
            additional_filtered_dfs.append(fee_filtered_df[fee_filtered_df[f"benefit_detail_{i}_2"].astype(str).str.contains(query, na=False)])

    # 최종 필터링된 데이터 결합
    filtered_df = pd.concat(additional_filtered_dfs).drop_duplicates().reset_index(drop=True)

    ####################################################################################
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

elif st.session_state['page'] == 'intro':
        info_html = """<h1>🧑‍💻프로젝트 주제</h1>
                    <p><strong>경쟁사 카드 제품 분석을 위한 통합 대시보드 개발 (prototype)</strong></p>
                    """
        info_html += "<hr/>"    

        info_html += """<h2>🔎선택 회사&amp;팀</h2>
                    <p><strong>BC카드 - 카드 상품 개발팀</strong></p>
                    """
        info_html += "<hr/>"

        info_html += """ <h3>🕵️‍♂️활용도/의미</h3>
                    <p>BC카드는 오랜 시간 동안 <strong>BC카드 결제망을 임대</strong>하며, 회원사의 카드 결제를 위탁 처리를 주 사업으로 진행해왔다. 하지만 최근 시장 변화로 인해 여러 회원사들이 <strong>독자 결제망을 구축하면서 BC카드의 주요 사업 영역에 변화가 필요</strong>하게 되었다.</p>
                    <p><strong>2021년 7월</strong>, BC카드는 이러한 시장 변화에 대응하여 <strong>자체 카드 발급을 시작</strong>했다.</p>
                    <p>이 프로젝트의 주 목적은 ❗자체 신용 카드의 후발 주자로 출발하는 <strong>BC카드의 카드 상품 개발 팀</strong>이 더 효율적이고 <strong>경쟁력 있는 카드를 개발</strong>하는데 도움을❗ 주고자 한다.</p>
                    <p>따라서 이 프로젝트는 <strong>경쟁사의 카드 제품 정보를 유형 별로 파악하고 분석</strong>할 수 있도록 지원하는 통합 대시보드를 개발하는 것이다. 이를 통해 BC카드는 더욱 강력하고 경쟁력 있는 카드 제품을 시장에 선보일 수 있을 것으로 예상된다.</p>
                    """ 
        info_html += "<hr/>"

        info_html += "<h3>🧑‍💻데이터 분석 과정</h3>"

        info_html += """<ol>
                        <li>데이터 수집을 진행하면서 페이지 구성이 달라 수집이 안되는 카드 페이지는 따로 저장한다.</li>
                        <li>수집이 안된 카드를 대상으로 다시 데이터를 수집한다.</li>
                        <li>두 개의 데이터를 합친다</li>
                        <li>‘날짜’ 데이터는 숫자(날짜)만 남긴다.</li>
                        <li>컬럼 순서를 ‘신한카드’를 기준으로 다른 카드 사도 정렬한다.</li>
                        <li>‘연회비’
                            <ol>
                                <li>타입을 숫자로 변환한다.</li>
                                <li>null 값과 0원 혹은 무료를 구분한다.</li>
                            </ol>
                        </li>
                    </ol>
                    """
        info_html += "<hr/>"

        sinhan_url ='https://www.shinhancard.com/pconts/html/card/credit/MOBFM281/MOBFM281R11.html?crustMenuId=ms581'
        lotte_url = 'https://www.lottecard.co.kr/app/LPCDADA_V100.lc'
        info_html += f"""<div style="display: flex; justify-content: space-around; align-items: center;">
                            <a href="{sinhan_url}" target="_blank" style="text-decoration: none;">
                                <button style="background-color: #F3CED5; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: block; font-size: 16px; margin-top: 10px; cursor: pointer; border-radius: 5px;">
                                    신한카드-신용카드 수집 링크 보러 가기
                                </button>
                            </a>
                            <a href="{lotte_url}" target="_blank" style="text-decoration: none;">
                                <button style="background-color: #F3CED5; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: block; font-size: 16px; margin-top: 10px; cursor: pointer; border-radius: 5px;">
                                    롯데카드-신용카드 수집 링크 보러 가기
                                </button>
                            </a>
                        </div>
                        <div style="display: flex; justify-content: space-around; align-items: center;">
                            <button style="background-color: #F3CED5; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: block; font-size: 16px; margin-top: 10px; cursor: pointer; border-radius: 5px;">
                                   추후 upload 예정..
                            </button>
                        </div>
                        """

        st.markdown(info_html, unsafe_allow_html=True)