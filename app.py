import os
import streamlit as st
import google.generativeai as genai
import docx2txt

# --- 1. CẤU HÌNH TRANG & LẤY API KEY BẢO MẬT ---
st.set_page_config(page_title="Cố vấn Hướng nghiệp AI", page_icon="🎓", layout="centered")

# Lấy API Key và kích hoạt kết nối
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = 'gemini-3.8-flash'
model = genai.GenerativeModel(MODEL_NAME)

st.title("🎓 Cố vấn Định hướng Nghề nghiệp AI")
st.caption("Dự án KHKT - Tích hợp Mô hình Holland & Dữ liệu Chuyên gia (RAG)")

# --- 2. HÀM TỰ ĐỘNG ĐỌC TÀI LIỆU (TỐI ƯU TỐC ĐỘ & CHỐNG LỖI QUÁ TẢI) ---
@st.cache_resource
def doc_tat_ca_file_word():
    noi_dung_tong = ""
    for file_name in os.listdir("."):
        if file_name.endswith(".docx") and not file_name.startswith("~$"):
            try:
                van_ban = docx2txt.process(file_name)
                noi_dung_tong += f"\n\n--- TÀI LIỆU: {file_name} ---\n" + van_ban
            except Exception:
                pass
    # Cắt gọn tối đa 25.000 ký tự để AI phản hồi siêu nhanh, không quá tải token
    return noi_dung_tong[:10000]

du_lieu_bo_sung = doc_tat_ca_file_word()

# --- 3. KIỂM TRA BẢO MẬT API KEY ---
if not GEMINI_API_KEY:
    st.warning("⚠️ Chưa tìm thấy API Key! Vui lòng dán GEMINI_API_KEY vào mục Streamlit Secrets (Settings > Secrets).")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# --- 4. CẤU HÌNH CÂU LỆNH HỆ THỐNG ---
SYSTEM_INSTRUCTION = f"""
Bạn là "Cố vấn Hướng nghiệp AI" dành cho học sinh THPT.

Nhiệm vụ:
1. Trò chuyện, dẫn dắt học sinh làm trắc nghiệm Holland (RIASEC) tự nhiên.
2. TƯ VẤN BẮT BUỘC DỰA VÀO TÀI LIỆU CHUYÊN GIA SAU ĐÂY:
{du_lieu_bo_sung}
3. Trả lời ngắn gọn, súc tích, thân thiện, thấu hiểu tâm lý học sinh THPT.
4. KHI KẾT THÚC TRÒ CHUYỆN: Hãy cảm ơn, chúc bạn ấy học tốt và nhắn câu: "Cảm ơn bạn đã trải nghiệm! Bạn giúp tớ điền form đánh giá ngắn này nhé: [Dán link Google Form của bạn vào đây]"
"""

with st.sidebar:
    st.header("⚙️ Tùy chọn")
    if st.button("🔄 Bắt đầu lại cuộc trò chuyện", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 5. KHỞI TẠO BỘ NHỚ CHAT (TỰ ĐỘNG SỬA LỖI KẸT SESSION) ---
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
        st.stop()

# --- 6. GIAO DIỆN CHAT STREAMING SIÊU NHANH ---
for msg in st.session_state.get("messages", []):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_prompt := st.chat_input("Nhập tin nhắn..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(user_prompt, stream=True)

            def gen_stream():
                for chunk in response:
                    yield chunk.text

            full_text = st.write_stream(gen_stream())
            st.session_state.messages.append({"role": "assistant", "content": full_text})
        except Exception as e:
            if "chat_session" in st.session_state:
                del st.session_state["chat_session"]
            st.error(f"Lỗi kết nối: {e}. Bạn hãy gửi lại tin nhắn một lần nữa nhé!")
