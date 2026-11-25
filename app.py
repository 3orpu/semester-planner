import streamlit as st

st.title("📅 학기 일정 생성기")

st.write("강의계획서를 업로드하면")
st.write("시험, 과제, 발표 일정을 정리해 드립니다.")

uploaded_file = st.file_uploader(
    "강의계획서 PDF를 업로드하세요",
    type=["pdf"]
)

if uploaded_file is not None:
    st.success("PDF 업로드 성공!")
    st.write("파일 이름:", uploaded_file.name)
    