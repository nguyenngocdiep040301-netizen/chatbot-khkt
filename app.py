import streamlit as st
from openai import OpenAI
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Cố vấn Hướng nghiệp AI", page_icon="🎓", layout="centered")

# 2. KHỞI TẠO API OPENROUTER
API_KEY = st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

st.title("🎓 Cố vấn Định hướng Nghề nghiệp AI")
st.caption("Dự án KHKT - Tích hợp Mô hình Holland & Dữ liệu Chuyên gia")

# 3. QUẢN LÝ TIN NHẮN (SESSION STATE)
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Xin chào! Tớ là Cố vấn Hướng nghiệp AI. Cậu tên là gì và hiện đang học lớp mấy rồi?"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 4. XỬ LÝ NHẬP LIỆU & GỌI API
if prompt := st.chat_input("Nhập tin nhắn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            response = client.chat.completions.create(
                model="google/gemma-2-9b-it:free",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Lỗi kết nối API: {e}. Vui lòng thử lại sau!")
