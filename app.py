
import streamlit as st
import pymupdf
import pandas as pd
import re
import calendar
from datetime import date, timedelta

st.set_page_config(
    page_title="Semester Planner",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Semester Planner")
st.write("여러 강의계획서의 일정을 한 번에 관리해요.")


# -------------------------
# 1. 일정 추출 함수
# -------------------------

def extract_events(text, year, course_name):

    events = []

    keywords = {
        "시험": ["시험", "중간고사", "기말고사", "퀴즈", "고사"],
        "과제": ["과제", "제출", "레포트", "보고서", "마감"],
        "발표": ["발표", "프레젠테이션", "presentation"]
    }

    date_patterns = [
        r"(\d{4})[./년-]\s*(\d{1,2})[./월-]\s*(\d{1,2})일?",
        r"(\d{1,2})월\s*(\d{1,2})일",
        r"(\d{1,2})\s*/\s*(\d{1,2})"
    ]

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        event_type = None

        for kind, words in keywords.items():
            if any(word in line for word in words):
                event_type = kind
                break

        if event_type is None:
            continue

        event_date = None

        for i, pattern in enumerate(date_patterns):

            match = re.search(pattern, line)

            if match:

                try:
                    if i == 0:
                        y = int(match.group(1))
                        m = int(match.group(2))
                        d = int(match.group(3))
                    else:
                        y = int(year)
                        m = int(match.group(1))
                        d = int(match.group(2))

                    event_date = date(y, m, d)
                    break

                except ValueError:
                    continue

        if event_date is not None:

            events.append({
                "과목": course_name,
                "날짜": event_date,
                "종류": event_type,
                "일정": line
            })

    return events


# -------------------------
# 2. 여러 PDF 업로드
# -------------------------

uploaded_files = st.file_uploader(
    "강의계획서 PDF를 여러 개 선택하세요",
    type=["pdf"],
    accept_multiple_files=True
)

selected_year = st.number_input(
    "일정 연도",
    min_value=2020,
    max_value=2035,
    value=date.today().year
)

all_events = []

if uploaded_files:

    st.subheader("📚 과목별 강의계획서")

    for file_index, uploaded_file in enumerate(uploaded_files):

        with st.expander(
            f"📄 {uploaded_file.name}",
            expanded=True
        ):

            course_name = st.text_input(
                "과목명",
                value=uploaded_file.name.replace(".pdf", ""),
                key=f"course_{file_index}_{uploaded_file.name}"
            )

            pdf = pymupdf.open(
                stream=uploaded_file.getvalue(),
                filetype="pdf"
            )

            full_text = ""

            for page in pdf:
                full_text += page.get_text() + "\n"

            st.success("PDF 텍스트 추출 완료")

            with st.expander("추출한 PDF 원문 보기"):
                st.text_area(
                    "PDF 내용",
                    full_text,
                    height=200,
                    key=f"text_{file_index}"
                )

            course_events = extract_events(
                full_text,
                int(selected_year),
                course_name
            )

            all_events.extend(course_events)

            st.write(
                f"자동으로 찾은 일정: {len(course_events)}개"
            )


# -------------------------
# 3. 직접 추가한 일정 저장
# -------------------------

if "manual_events" not in st.session_state:
    st.session_state.manual_events = []


st.subheader("➕ 일정 직접 추가")

with st.form("add_event_form"):

    new_course = st.text_input(
        "과목명",
        placeholder="예: 공학생물학"
    )

    new_date = st.date_input(
        "날짜",
        value=date.today()
    )

    new_type = st.selectbox(
        "일정 종류",
        ["시험", "과제", "발표", "기타"]
    )

    new_description = st.text_input(
        "일정 내용",
        placeholder="예: 중간고사"
    )

    submitted = st.form_submit_button(
        "일정 추가"
    )

    if submitted:

        if new_description.strip():

            st.session_state.manual_events.append({
                "과목": new_course,
                "날짜": new_date,
                "종류": new_type,
                "일정": new_description.strip()
            })

            st.success("일정을 추가했어요!")
            st.rerun()

        else:
            st.warning("일정 내용을 입력해주세요.")


# -------------------------
# 4. 전체 일정표
# -------------------------

all_events.extend(
    st.session_state.manual_events
)

st.subheader("🗓️ 전체 일정표")

if all_events:

    df = pd.DataFrame(all_events)

    df = df.sort_values("날짜")

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="schedule_editor"
    )

    edited_df["날짜"] = pd.to_datetime(
        edited_df["날짜"]
    ).dt.date

    # -------------------------
    # 5. 일정 충돌 확인
    # -------------------------

    st.subheader("⚠️ 같은 날짜 일정")

    duplicated = edited_df[
        edited_df.duplicated(
            subset=["날짜"],
            keep=False
        )
    ]

    if not duplicated.empty:

        st.warning(
            "같은 날짜에 일정이 여러 개 있어요!"
        )

        st.dataframe(
            duplicated.sort_values("날짜"),
            use_container_width=True
        )

    else:
        st.success("같은 날짜에 일정이 겹치지 않아요.")

    # -------------------------
    # 6. CSV 다운로드
    # -------------------------

    csv_data = edited_df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "📥 일정표 CSV 다운로드",
        data=csv_data,
        file_name="semester_schedule.csv",
        mime="text/csv"
    )

    # -------------------------
    # 7. ICS 캘린더 다운로드
    # -------------------------

    def escape_ics(text):

        text = str(text)
        text = text.replace("\\", "\\\\")
        text = text.replace(";", "\\;")
        text = text.replace(",", "\\,")
        text = text.replace("\n", "\\n")

        return text

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Semester Planner//KO",
        "CALSCALE:GREGORIAN"
    ]

    for index, row in edited_df.iterrows():

        event_date = row["날짜"]

        start_date = event_date.strftime("%Y%m%d")

        end_date = (
            event_date + timedelta(days=1)
        ).strftime("%Y%m%d")

        event_title = escape_ics(
            f"[{row['과목']}] {row['일정']}"
        )

        event_kind = escape_ics(
            row["종류"]
        )

        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:semester-planner-{index}-{start_date}@local",
            f"DTSTAMP:{pd.Timestamp.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;VALUE=DATE:{start_date}",
            f"DTEND;VALUE=DATE:{end_date}",
            f"SUMMARY:{event_title}",
            f"DESCRIPTION:{event_kind}",
            "END:VEVENT"
        ])

    ics_lines.append("END:VCALENDAR")

    st.download_button(
        "📆 캘린더 앱용 일정 파일 (.ics)",
        data="\r\n".join(ics_lines),
        file_name="semester_schedule.ics",
        mime="text/calendar"
    )

    # -------------------------
    # 8. 월별 캘린더
    # -------------------------

    st.subheader("📅 월별 캘린더")

    calendar_year = st.number_input(
        "캘린더 연도",
        min_value=2020,
        max_value=2035,
        value=date.today().year,
        key="calendar_year"
    )

    calendar_month = st.selectbox(
        "월 선택",
        list(range(1, 13)),
        index=date.today().month - 1,
        key="calendar_month"
    )

    weekdays = ["월", "화", "수", "목", "금", "토", "일"]

    weekday_columns = st.columns(7)

    for col, weekday in zip(weekday_columns, weekdays):
        col.markdown(f"**{weekday}**")

    month_calendar = calendar.monthcalendar(
        int(calendar_year),
        int(calendar_month)
    )

    for week in month_calendar:

        day_columns = st.columns(7)

        for col, day in zip(day_columns, week):

            if day == 0:
                col.write(" ")

            else:

                current_date = date(
                    int(calendar_year),
                    int(calendar_month),
                    day
                )

                day_events = edited_df[
                    edited_df["날짜"] == current_date
                ]

                count = len(day_events)

                label = str(day)

                if count > 0:
                    label += f" 📌{count}"

                if col.button(
                    label,
                    key=f"day_{calendar_year}_{calendar_month}_{day}"
                ):

                    st.session_state.selected_date = current_date

    selected_date = st.session_state.get(
        "selected_date",
        date.today()
    )

    st.write(f"선택한 날짜: {selected_date}")

    selected_events = edited_df[
        edited_df["날짜"] == selected_date
    ]

    if not selected_events.empty:

        st.dataframe(
            selected_events,
            use_container_width=True
        )

    else:
        st.info("이 날짜에는 일정이 없어요.")

    # -------------------------
    # 9. D-day
    # -------------------------

    st.subheader("⏳ 다가오는 일정")

    today = date.today()

    upcoming = edited_df[
        edited_df["날짜"] >= today
    ].copy()

    upcoming = upcoming.sort_values(
        "날짜"
    ).head(5)

    if not upcoming.empty:

        upcoming["D-day"] = upcoming["날짜"].apply(
            lambda d: (d - today).days
        )

        st.dataframe(
            upcoming[
                ["과목", "날짜", "종류", "일정", "D-day"]
            ],
            use_container_width=True
        )

    else:
        st.info("다가오는 일정이 없어요.")


    # -------------------------
    # 10. 일정 몰림 분석
    # -------------------------

    st.subheader("🚨 일정 몰림 분석")

    # 날짜를 기준으로 주차 계산
    analysis_df = edited_df.copy()

    analysis_df["날짜"] = pd.to_datetime(
        analysis_df["날짜"]
    )

    # 월요일 기준으로 해당 주의 시작 날짜 계산
    analysis_df["주 시작일"] = (
        analysis_df["날짜"]
        - pd.to_timedelta(
            analysis_df["날짜"].dt.weekday,
            unit="D"
        )
    )

    # 주별 일정 개수 계산
    weekly_summary = (
        analysis_df
        .groupby("주 시작일")
        .agg(
            일정_개수=("일정", "count"),
            시험_개수=("종류", lambda x: (x == "시험").sum()),
            과제_개수=("종류", lambda x: (x == "과제").sum()),
            발표_개수=("종류", lambda x: (x == "발표").sum())
        )
        .reset_index()
    )

    # 일정이 많은 주간 찾기
    busy_weeks = weekly_summary[
        (weekly_summary["일정_개수"] >= 3)
        | (weekly_summary["시험_개수"] >= 2)
    ]

    if not busy_weeks.empty:

        st.warning(
            "일정이 몰리는 주간이 있어요! "
            "미리 공부와 과제 시간을 계획해보세요."
        )

        st.markdown("### 📌 일정이 많은 주간")

        st.dataframe(
            busy_weeks,
            use_container_width=True
        )

        # 해당 주간의 구체적인 일정 표시
        for _, week in busy_weeks.iterrows():

            week_start = week["주 시작일"]

            week_end = week_start + pd.Timedelta(days=6)

            st.markdown(
                f"#### {week_start.strftime('%Y-%m-%d')} ~ "
                f"{week_end.strftime('%Y-%m-%d')}"
            )

            details = analysis_df[
                (analysis_df["날짜"] >= week_start)
                & (analysis_df["날짜"] <= week_end)
            ]

            st.dataframe(
                details[
                    ["과목", "날짜", "종류", "일정"]
                ],
                use_container_width=True
            )

    else:

        st.success(
            "일정이 많이 몰리는 주간이 발견되지 않았어요."
        )

else:

    st.info(
        "PDF를 업로드하거나 직접 일정을 추가해주세요."
    )
