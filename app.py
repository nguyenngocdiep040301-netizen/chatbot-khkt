import os
import streamlit as st
import google.generativeai as genai
import docx2txt

# --- 1. CẤU HÌNH API KEY BẢO MẬT & MÔ HÌNH ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSy...")
MODEL_NAME = "gemini-3.8-flash"

st.set_page_config(page_title="Cố vấn Hướng nghiệp AI", page_icon="🎓", layout="centered")
st.title("🎓 Cố vấn Định hướng Nghề nghiệp AI")
st.caption("Dự án KHKT - Tích hợp Mô hình Holland & Dữ liệu Chuyên gia (RAG)")

# --- 2. HÀM TỰ ĐỘNG ĐỌC TẤT CẢ FILE WORD TRONG THƯ MỤC ---
@st.cache_resource
def doc_tat_ca_file_word():
    noi_dung_tong = ""
    for file_name in os.listdir("."):
        if file_name.endswith(".docx"):
            try:
                van_ban = docx2txt.process(file_name)
                noi_dung_tong += f"\n\n--- TÀI LIỆU: {file_name} ---\n" + van_ban
            except Exception:
                pass
    # THÊM DÒNG NÀY Ở DƯỚI CÙNG HÀM ĐỂ CẮT BỚT NỘI DUNG QuÁ DÀI:
    return noi_dung_tong[:40000]

du_lieu_bo_sung = doc_tat_ca_file_word()

genai.configure(api_key=GEMINI_API_KEY)

# --- 3. CẤU HÌNH SYSTEM INSTRUCTION ---
SYSTEM_INSTRUCTION = f"""
Bạn là "Cố vấn Hướng nghiệp AI" dành cho học sinh THPT.

Nhiệm vụ:
1. Trò chuyện, dẫn dắt học sinh làm trắc nghiệm Holland (RIASEC) tự nhiên.
2. TƯ VẤN BẮT BUỘC DỰA VÀO TÀI LIỆU CHUYÊN GIA SAU ĐÂY:
{du_lieu_bo_sung}
3. Trả lời ngắn gọn, gần gũi, thấu hiểu tâm lý học sinh.
4. KHI KẾT THÚC TRÒ CHUYỆN: Hãy cảm ơn, chúc bạn ấy học tốt và nhắn câu: "Cảm ơn bạn đã trải nghiệm! Bạn giúp tớ điền form đánh giá ngắn này nhé: [Dán link Google Form 2 của bạn vào đây]"
"""

# Nút bắt đầu lại ở menu bên trái phòng khi bị kẹt bộ nhớ
with st.sidebar:
    if st.button("🔄 Bắt đầu lại cuộc trò chuyện"):
        st.session_state.clear()
        st.rerun()

# --- 4. KHỞI TẠO VÀ TỰ XÓA BỘ NHỚ CŨ NẾU ĐỔI MODEL ---
if "chat_session" not in st.session_state or st.session_state.get("current_model") != MODEL_NAME:
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME, 
            system_instruction=SYSTEM_INSTRUCTION
        )
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.current_model = MODEL_NAME
        st.session_state.messages = [
            {"role": "assistant", "content": "Xin chào! Tớ là Cố vấn Hướng nghiệp AI. Cậu tên là gì và hiện đang học lớp mấy rồi?"}
        ]
    except Exception as e:
        st.error(f"Lỗi khởi tạo AI: {e}")

# --- 5. GIAO DIỆN CHAT (HIỂN THỊ TIN NHẮN & Ô NHẬP) ---
for msg in st.session_state.get("messages", []):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_prompt := st.chat_input("Nhập tin nhắn..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI đang suy nghĩ..."):
            try:
                response = st.session_state.chat_session.send_message(user_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                # Nếu gặp lỗi kết nối, tự động xóa phiên kẹt để khởi tạo lại
                if "chat_session" in st.session_state:
                    del st.session_state["chat_session"]
                st.error(f"Lỗi kết nối: {e}. Bạn hãy gửi lại tin nhắn một lần nữa nhé!")