import requests
import streamlit as st


API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="CV AI Scientist", layout="wide")
st.title("CV AI Scientist")

with st.form("create_run"):
    query = st.text_area("研究问题", value="工业缺陷检测中小缺陷区域定位不稳定的问题")
    domain = st.selectbox("领域", ["industrial", "remote_sensing", "medical", "general_cv"])
    task_type = st.selectbox(
        "任务类型",
        ["anomaly_detection", "detection", "segmentation", "classification", "change_detection"],
    )
    dataset_path = st.text_input("数据集路径", value="data/raw")
    submitted = st.form_submit_button("创建研究任务")

if submitted:
    response = requests.post(
        f"{API_BASE}/runs",
        json={
            "query": query,
            "domain": domain,
            "task_type": task_type,
            "dataset_path": dataset_path,
        },
        timeout=30,
    )
    response.raise_for_status()
    st.success("任务已创建")
    st.json(response.json())
