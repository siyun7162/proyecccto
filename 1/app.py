from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.font_manager as fm
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 시스템에 따라 적절한 폰트 선택
# plt.rcParams["font.family"] = "AppleGothic"     # macOS
plt.rcParams["font.family"] = "Malgun Gothic"  # Windows
#plt.rcParams["font.family"] = "NanumGothic"    # Linux
plt.rcParams["axes.unicode_minus"] = False       # 음수 깨짐 방지
# --------------------------------------------------
# 1. Streamlit 웹페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="부산항 KPI 대시보드",
    layout="wide"
)

st.title("부산항 시설별 KPI 대시보드")

# --------------------------------------------------
# 2. CSV 파일 위치 설정
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "marine.csv"


# CSV 파일이 실제로 있는지 확인합니다.
if not DATA_PATH.exists():

    st.error(
        f"CSV 파일을 찾을 수 없습니다: {DATA_PATH}"
    )

    st.stop()


# CSV 파일을 한 번만 읽습니다.
df = pd.read_csv(
    DATA_PATH,
    encoding="euc-kr"
)


# --------------------------------------------------
# 3. 데이터 정리
# --------------------------------------------------

# 시설명의 빈값을 없애고 문자열로 바꿉니다.
df["시설명"] = (
    df["시설명"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# 모든 시설을 먼저 북항으로 분류합니다.
df["권역"] = "북항"


# 시설명이 감천으로 시작하면 감천으로 변경합니다.
df.loc[
    df["시설명"].str.startswith("감천", na=False),
    "권역"
] = "감천"


# 시설명이 신항으로 시작하면 신항으로 변경합니다.
df.loc[
    df["시설명"].str.startswith("신항", na=False),
    "권역"
] = "신항"


# 연도와 월을 합쳐 연월을 만듭니다.
df["연월"] = (
    df["사용년월"].astype(str).str.strip()
    + "-"
    + df["사용월"].astype(str).str.strip().str.zfill(2)
)


# 처리실적을 숫자로 바꿉니다.
df["처리실적"] = pd.to_numeric(
    df["처리실적"],
    errors="coerce"
)


# 접안시간도 숫자로 바꿉니다.
df["접안시간"] = pd.to_numeric(
    df["접안시간"],
    errors="coerce"
)


# --------------------------------------------------
# 4. 권역별 데이터 복사
# --------------------------------------------------

# 감천 데이터만 복사합니다.
gamcheon_df = df.loc[
    df["권역"] == "감천"
].copy()


# 신항 데이터만 복사합니다.
new_port_df = df.loc[
    df["권역"] == "신항"
].copy()


# 북항 데이터만 복사합니다.
north_port_df = df.loc[
    df["권역"] == "북항"
].copy()


# --------------------------------------------------
# 5. 사용자가 조회할 권역 선택
# --------------------------------------------------

selected_region = st.radio(
    "조회할 권역을 선택하세요.",
    options=["감천", "신항", "북항"],
    horizontal=True
)


# 선택한 권역에 맞는 데이터만 가져옵니다.
if selected_region == "감천":

    selected_df = gamcheon_df.copy()

elif selected_region == "신항":

    selected_df = new_port_df.copy()

else:

    selected_df = north_port_df.copy()


# --------------------------------------------------
# 6. 선택한 권역의 기본 정보
# --------------------------------------------------

st.subheader(f"{selected_region} 기본 현황")


left_column, right_column = st.columns(2)


with left_column:

    st.metric(
        label="데이터 개수",
        value=f"{len(selected_df):,}개"
    )


with right_column:

    st.metric(
        label="시설 수",
        value=f"{selected_df['시설명'].nunique():,}개"
    )


# --------------------------------------------------
# 7. 선택 권역의 월간 총 처리실적
# --------------------------------------------------

st.subheader(
    f"{selected_region} 월간 총 처리실적"
)


# 핵심:
# 전체 df가 아니라 선택한 selected_df를 사용합니다.
MT = (
    selected_df.groupby(
        ["연월", "권역"],
        as_index=False
    )
    .agg(
        월간총처리실적=("처리실적", "sum")
    )
    .sort_values("연월")
)


# 월간 총 처리실적 표를 표시합니다.
st.dataframe(
    MT,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 8. 월간 총 처리실적 그래프
# --------------------------------------------------

from matplotlib.ticker import StrMethodFormatter

fig, ax = plt.subplots(figsize=(12, 5))

sns.lineplot(
    data=MT,
    x="연월",
    y="월간총처리실적",
    marker="o",
    linewidth=2,
    ax=ax
)

ax.set_title(
    f"{selected_region} Monthly Total Throughput (Tons)"
)

ax.set_xlabel("year_month")
ax.set_ylabel("month_total(T)")

# 1e6을 없애고 9,000,000처럼 표시합니다.
ax.yaxis.set_major_formatter(
    StrMethodFormatter("{x:,.0f}")
)

ax.tick_params(
    axis="x",
    rotation=45
)

ax.grid(
    axis="y",
    linestyle=":",
    alpha=0.5
)

plt.tight_layout()
st.pyplot(fig)

# --------------------------------------------------
# 9. 선택한 권역의 원본 데이터
# --------------------------------------------------

st.subheader(
    f"{selected_region} 시설별 원본 데이터"
)


st.dataframe(
    selected_df,
    use_container_width=True,
    hide_index=True
)

result = (
        df.groupby(["연월", "권역"], as_index=False)
        .agg(
            총접안시간=("접안시간", "sum"),
            총처리실적=("처리실적", "sum"),
        )
    )
result['시간당처리실적'] = (result['총처리실적'] / result['총접안시간']).round(2)

RWA = (result.groupby("권역", as_index=False).agg(전체접안시간=("총접안시간", "sum"),전체처리실적=("총처리실적", "sum")))

RWA['평균접안시간당처리실적'] = (RWA['전체처리실적'] / RWA['전체접안시간']).round(2)

comparison = result.merge(
    RWA[['권역','평균접안시간당처리실적']],
    on="권역",
    how="left",
    validate="many_to_one"
)

comparison['평균대비차이율'] = (
    (comparison['시간당처리실적'] - comparison['평균접안시간당처리실적'])
    / comparison['평균접안시간당처리실적'] * 100).round(2)

comparison.sort_values('권역')
# --------------------------------------------------
# KPI 2. 접안시간당 처리실적
# --------------------------------------------------

st.subheader(
    f"{selected_region} 접안시간당 처리실적"
)


# 접안시간당 처리실적을 계산할 수 있는 데이터만 선택합니다.
valid_df = selected_df.loc[
    selected_df["접안시간"].notna()
    & selected_df["처리실적"].notna()
    & (selected_df["접안시간"] > 0)
    & (selected_df["처리실적"] >= 0)
].copy()


# 사용할 수 있는 데이터가 없는 경우 계산을 중단합니다.
if valid_df.empty:

    st.warning(
        f"{selected_region}의 시간당 처리실적을 계산할 수 없습니다."
    )

else:

    # --------------------------------------------------
    # 1. 월별 총접안시간과 총처리실적 계산
    # --------------------------------------------------

    result = (
        valid_df.groupby(
            ["연월", "권역"],
            as_index=False
        )
        .agg(
            총접안시간=("접안시간", "sum"),
            총처리실적=("처리실적", "sum")
        )
        .sort_values("연월")
    )


    # --------------------------------------------------
    # 2. 월별 시간당 처리실적 계산
    # --------------------------------------------------

    result["시간당처리실적"] = (
        result["총처리실적"]
        / result["총접안시간"]
    )


    # --------------------------------------------------
    # 3. 선택 권역의 전체 평균 계산
    # --------------------------------------------------

    RWA = (
        result.groupby(
            "권역",
            as_index=False
        )
        .agg(
            전체접안시간=("총접안시간", "sum"),
            전체처리실적=("총처리실적", "sum")
        )
    )


    RWA["평균접안시간당처리실적"] = (
        RWA["전체처리실적"]
        / RWA["전체접안시간"]
    )


    # --------------------------------------------------
    # 4. 월별 데이터에 권역 평균 붙이기
    # --------------------------------------------------

    comparison = result.merge(
        RWA[
            [
                "권역",
                "평균접안시간당처리실적"
            ]
        ],
        on="권역",
        how="left",
        validate="many_to_one"
    )


    # --------------------------------------------------
    # 5. 평균 대비 차이율 계산
    # --------------------------------------------------

    comparison["평균대비차이율"] = (
        (
            comparison["시간당처리실적"]
            - comparison["평균접안시간당처리실적"]
        )
        / comparison["평균접안시간당처리실적"]
        * 100
    )


    # 평균보다 높은지 낮은지 구분합니다.
    comparison["평균비교"] = "평균 미만"

    comparison.loc[
        comparison["시간당처리실적"]
        >= comparison["평균접안시간당처리실적"],
        "평균비교"
    ] = "평균 이상"


    # --------------------------------------------------
    # 6. KPI 카드 표시
    # --------------------------------------------------

    average_productivity = RWA.loc[
        0,
        "평균접안시간당처리실적"
    ]


    above_average_months = (
        comparison["평균비교"] == "평균 이상"
    ).sum()


    below_average_months = (
        comparison["평균비교"] == "평균 미만"
    ).sum()


    column1, column2, column3 = st.columns(3)


    with column1:

        st.metric(
            label="평균 시간당 처리실적",
            value=f"{average_productivity:,.2f}"
        )


    with column2:

        st.metric(
            label="평균 이상 월",
            value=f"{above_average_months}개월"
        )


    with column3:

        st.metric(
            label="평균 미만 월",
            value=f"{below_average_months}개월"
        )


    # --------------------------------------------------
    # 7. 화면 출력용 표 만들기
    # --------------------------------------------------

    kpi2_table = comparison[
        [
            "연월",
            "권역",
            "총접안시간",
            "총처리실적",
            "시간당처리실적",
            "평균접안시간당처리실적",
            "평균대비차이율",
            "평균비교"
        ]
    ].copy()


    # 화면에 보여줄 숫자만 반올림합니다.
    kpi2_table["시간당처리실적"] = (
        kpi2_table["시간당처리실적"].round(2)
    )

    kpi2_table["평균접안시간당처리실적"] = (
        kpi2_table["평균접안시간당처리실적"].round(2)
    )

    kpi2_table["평균대비차이율"] = (
        kpi2_table["평균대비차이율"].round(2)
    )


    # --------------------------------------------------
    # 8. KPI 2 표 출력
    # --------------------------------------------------

    st.dataframe(
        kpi2_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "총접안시간": st.column_config.NumberColumn(
                "총 접안시간",
                format="%,.0f"
            ),
            "총처리실적": st.column_config.NumberColumn(
                "총 처리실적",
                format="%,.0f"
            ),
            "시간당처리실적": st.column_config.NumberColumn(
                "시간당 처리실적",
                format="%,.2f"
            ),
            "평균접안시간당처리실적": st.column_config.NumberColumn(
                "권역 평균",
                format="%,.2f"
            ),
            "평균대비차이율": st.column_config.NumberColumn(
                "평균 대비 차이율",
                format="%.2f%%"
            )
        }
    )

# --------------------------------------------------
# KPI 2. 평균 대비 차이율 그래프
# --------------------------------------------------

st.subheader(
    f"{selected_region} 월별 평균 대비 차이율"
)


# 연월 순서로 정렬합니다.
graph_data = comparison.sort_values(
    by="연월"
).copy()


# 그래프 틀을 만듭니다.
fig, ax = plt.subplots(
    figsize=(12, 5)
)


# 월별 평균 대비 차이율을 선으로 표시합니다.
sns.lineplot(
    data=graph_data,
    x="연월",
    y="평균대비차이율",
    marker="o",
    linewidth=2,
    ax=ax
)


# 0% 위치에 평균 기준 점선을 표시합니다.
ax.axhline(
    y=0,
    color="red",
    linestyle="--",
    linewidth=1.5,
    label="권역 평균"
)


# 그래프 제목을 설정합니다.
ax.set_title(
    f"{selected_region} Variance Rate of Monthly Hourly Performance Against Average"
)


# X축과 Y축 이름을 설정합니다.
ax.set_xlabel("year_month")
ax.set_ylabel("Percentage Deviation from Average(%)")


# 연월이 겹치지 않도록 글자를 기울입니다.
ax.tick_params(
    axis="x",
    rotation=45
)


# Y축 숫자 뒤에 %를 붙입니다.
ax.yaxis.set_major_formatter(
    lambda value, position: f"{value:.0f}%"
)


# 가로 격자를 표시합니다.
ax.grid(
    axis="y",
    linestyle=":",
    alpha=0.5
)


# 범례를 표시합니다.
ax.legend()


# 글자나 그래프가 잘리지 않게 정리합니다.
plt.tight_layout()


# Streamlit 화면에 그래프를 표시합니다.
st.pyplot(fig)


# 사용이 끝난 그래프를 메모리에서 정리합니다.
plt.close(fig)