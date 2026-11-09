import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Smart Storage Manager")

st.header("Upload")
uploaded = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"])
if uploaded is not None and st.button("Upload"):
    try:
        response = requests.post(
            f"{BACKEND_URL}/upload",
            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
            timeout=30,
        )
        response.raise_for_status()
        st.success(f"Uploaded: {uploaded.name}")
    except requests.RequestException as error:
        st.error(f"Upload failed: {error}")

st.header("Inventory")
try:
    items = requests.get(f"{BACKEND_URL}/items", timeout=10).json()
    if items:
        st.table(items)
    else:
        st.info("No items yet.")
except requests.RequestException as error:
    st.error(f"Cannot reach backend: {error}")
