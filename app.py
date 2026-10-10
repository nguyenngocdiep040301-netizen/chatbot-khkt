import os
import streamlit as st
import docx2txt
from groq import Groq

# --- 1. CẤU HÌNH TRANG & LẤY API KEY BẢO MẬT ---
st.set_page_config(page_title="Cố vấn Hướng nghiệp AI", page_icon="🎓", layout="centered")

# Lấy Groq API Key từ Streamlit Secrets hoặc biến môi trường
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
client = Groq(api_key=GROQ_API_KEY)
model="mixtral-8x7b-32768"
st.title("🎓 Cố vấn Định hướng Nghề nghiệp AI")
st.caption("Dự án KHKT - Tích hợp Mô hình Holland & Dữ liệu Chuyên gia (RAG)")

# --- 2. HÀM TỰ ĐỘNG ĐỌC TÀI LIỆU (OPTIMIZED RAG) ---
@st.cache_resource
def doc_tat_ca_file_word():
    noi_dung_tong = ""
    for file_name in os.listdir("."):
        if file_name.endswith(".docx") and not file_name.startswith("~$"):
            try:
                van_ban = docx2txt.process(file_name)
                noi_dung_tong += f"\n\n--- TÀI LIỆU: {file_name} ---\n" + van_ban
            except Exception as e:
                pass
    return noi_dung_tong

du_lieu_chuyen_gia = doc_tat_ca_file_word()

# --- 3. KHỞI TẠO TÍNH CÁCH VÀ DỮ LIỆU BỐ CỤC AI ---
SYSTEM_PROMPT = f"""
Bạn là Cố vấn Hướng nghiệp AI thân thiện, am hiểu sâu sắc về định hướng nghề nghiệp cho học sinh THPT tại Việt Nam.
Nhiệm vụ của bạn:
1. Đồng hành, tư vấn tâm lý học đường và tư vấn ngành nghề theo bài trắc nghiệm tính cách Holland (RIASEC).
2. Tra cứu và đưa ra thông tin chính xác từ dữ liệu chuyên gia được cung cấp dưới đây.
3. Trả lời tự nhiên, xưng "tớ" - "cậu" hoặc "mình" - "bạn", giọng văn gần gũi, khích lệ và ngắn gọn, dễ hiểu.

DỮ LIỆU CHUYÊN GIA DÙNG ĐỂ TƯ VẤN (RAG):
{du_lieu_chuyen_gia}
"""

# Khởi tạo lịch sử trò chuyện trong session_state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Xin chào! Tớ là Cố vấn Hướng nghiệp AI. Cậu tên là gì và hiện đang học lớp mấy rồi?"}
    ]

# --- 4. HIỂN THỊ LỊCH SỬ CHÁT TRÊN GIAO DIỆN ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# Nút bắt đầu lại cuộc trò chuyện ở sidebar
with st.sidebar:
    st.header("⚙️ Tùy chọn")
    if st.button("🔄 Bắt đầu lại cuộc trò chuyện"):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": "Xin chào! Tớ là Cố vấn Hướng nghiệp AI. Cậu tên là gì và hiện đang học lớp mấy rồi?"}
        ]
        st.rerun()

# --- 5. XỬ LÝ NHẬP TIN NHẮN VÀ PHẢN HỒI TỪ AI (GROQ API) ---
if prompt := st.chat_input("Nhập tin nhắn..."):
    # Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Gọi Groq API để tạo câu trả lời
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Gọi API streaming tạo trải nghiệm gõ chữ theo thời gian thực
            completion = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=2048,
                stream=True,
            )
            
            for chunk in completion:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            error_msg = f"Lỗi kết nối Groq API: {str(e)}. Bạn hãy thử lại sau ít giây nhé!"
            message_placeholder.error(error_msg)
