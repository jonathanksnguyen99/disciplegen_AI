import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai

API_KEY_CUA_BAN = "AIzaSyCGDW0PkFmQLS_JS0Nhn2CzWtLzCY8pu7M"

def doc_website(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} 
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        doan_van = soup.find_all('p')
        return " ".join([p.get_text() for p in doan_van])
    except Exception as e:
        return ""

st.set_page_config(page_title="AI DiscipleGen", page_icon="📖")
st.title("📖 Trợ lý DiscipleGen")
st.caption("Khám phá Kinh Thánh theo phương pháp Quan sát - Giải nghĩa - Áp dụng")

# --- SỬA LỖI TẠI ĐÂY: BẢO VỆ ĐƯỜNG TRUYỀN (CLIENT) ---
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY_CUA_BAN)

if "tai_lieu" not in st.session_state:
    st.session_state.tai_lieu = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "phien_chat" not in st.session_state:
    tu_duy = """
    Bạn là người hướng dẫn Kinh Thánh theo DiscipleGen. 
    1. Trả lời trực tiếp và dễ hiểu.
    2. Sau khi trả lời, đặt MỘT câu hỏi Socratic để người học suy nghĩ thêm.
    3. Luôn khích lệ, khiêm nhường.
    """
    # Dùng client trong bộ nhớ (session_state) để khởi tạo phiên chat
    st.session_state.phien_chat = st.session_state.client.chats.create(
        model='gemini-2.5-flash',
        config={'system_instruction': tu_duy}
    )

# --- THANH BÊN (SIDEBAR) ĐỂ NẠP KIẾN THỨC ---
with st.sidebar:
    st.header("⚙️ Nạp Bài Học")
    link = st.text_input("Dán link từ disciplegen.com:")
    if st.button("Đọc Website"):
        if link:
            with st.spinner("Đang tải kiến thức..."):
                st.session_state.tai_lieu = doc_website(link)
            st.success("Nạp thành công! AI đã sẵn sàng.")
        else:
            st.warning("Vui lòng dán link vào ô trên.")

# --- KHU VỰC CHAT CHÍNH ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if cau_hoi := st.chat_input("Bạn muốn hỏi gì về Kinh Thánh?"):
    
    with st.chat_message("user"):
        st.markdown(cau_hoi)
    st.session_state.messages.append({"role": "user", "content": cau_hoi})

    if st.session_state.tai_lieu != "":
        cau_hoi_gui_ai = f"DỰA VÀO TÀI LIỆU SAU: {st.session_state.tai_lieu}\n\nHãy trả lời: {cau_hoi}"
    else:
        cau_hoi_gui_ai = cau_hoi

    with st.chat_message("ai"):
        # Sử dụng phien_chat đang được bảo vệ trong session_state
        response = st.session_state.phien_chat.send_message(cau_hoi_gui_ai)
        st.markdown(response.text)
    
    st.session_state.messages.append({"role": "ai", "content": response.text})