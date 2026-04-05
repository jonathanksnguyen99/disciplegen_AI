import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai

# Cứu cánh cho lỗi cơ sở dữ liệu trên máy chủ Streamlit
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import chromadb

# 1. CẤU HÌNH BAN ĐẦU & KẾT NỐI API
st.set_page_config(page_title="AI DiscipleGen", page_icon="📖", layout="wide")
API_KEY_CUA_BAN = st.secrets["GEMINI_API_KEY"]

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY_CUA_BAN)

# 2. KHỞI TẠO "KÉT SẮT" TRÍ NHỚ (VECTOR DATABASE)
@st.cache_resource
def khoi_tao_database():
    # Tạo một thư mục ẩn tên là 'tri_nho_ai' để lưu dữ liệu vĩnh viễn
    client = chromadb.PersistentClient(path="./tri_nho_ai")
    ngan_tu = client.get_or_create_collection(name="disciplegen_docs")
    return ngan_tu

ngan_tu_ai = khoi_tao_database()

# 3. HÀM ĐỌC WEBSITE
def doc_website(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} 
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        doan_van = soup.find_all('p')
        noi_dung = " ".join([p.get_text() for p in doan_van])
        return noi_dung
    except Exception as e:
        return ""

# =========================================================
# GIAO DIỆN WEB CHÍNH
# =========================================================
st.title("📖 Trợ lý DiscipleGen")
st.caption("Khám phá Kinh Thánh tự động từ thư viện DiscipleGen.com")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CỘT BÊN TRÁI: DÀNH RIÊNG CHO BẠN (ADMIN) ---
with st.sidebar:
    st.header("👑 Khu vực Admin")
    st.markdown("Nhét kiến thức vào 'bộ não' của AI tại đây:")
    
    link_moi = st.text_input("Dán link bài học Disciplegen:")
    
    if st.button("Hút dữ liệu vào AI"):
        if link_moi:
            with st.spinner("Đang hút dữ liệu & chuyển thành Vector..."):
                noi_dung = doc_website(link_moi)
                if len(noi_dung) > 50:
                    # Mã hóa bài viết thành số và cất vào két sắt
                    id_bai_viet = f"bai_{ngan_tu_ai.count() + 1}"
                    ngan_tu_ai.add(
                        documents=[noi_dung],
                        metadatas=[{"nguon": link_moi}],
                        ids=[id_bai_viet]
                    )
                    st.success(f"Đã nạp bài học vào Két sắt! (Tổng số: {ngan_tu_ai.count()} bài)")
                else:
                    st.error("Không tìm thấy nội dung hoặc link bị lỗi.")
        else:
            st.warning("Vui lòng nhập link.")
            
    st.divider()
    st.metric(label="📚 Dung lượng não bộ (Số bài đã học)", value=ngan_tu_ai.count())

# --- CỘT BÊN PHẢI: KHUNG CHAT CHO NGƯỜI DÙNG ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if cau_hoi := st.chat_input("Hãy hỏi bất cứ điều gì về Kinh Thánh..."):
    # 1. In câu hỏi của người dùng
    with st.chat_message("user"):
        st.markdown(cau_hoi)
    st.session_state.messages.append({"role": "user", "content": cau_hoi})

    # 2. BƯỚC THẦN KỲ: Tự động lục tìm Két sắt xem có bài nào liên quan không
    tai_lieu_tim_duoc = ""
    nguon_goc = ""
    if ngan_tu_ai.count() > 0:
        ket_qua = ngan_tu_ai.query(query_texts=[cau_hoi], n_results=1)
        if ket_qua['documents'][0]:
            tai_lieu_tim_duoc = ket_qua['documents'][0][0]
            nguon_goc = ket_qua['metadatas'][0][0]['nguon']

    # 3. Lắp ráp "Bản hiến pháp" mới 
    prompt_thong_minh = f"""
    Bạn là người hướng dẫn Kinh Thánh và môn đồ hóa theo DiscipleGen. Nền tảng cốt lõi là các bài học từ website DiscipleGen.

    CÂU HỎI CỦA NGƯỜI DÙNG: {cau_hoi}
    
    TÀI LIỆU TỪ DISCIPLENGEN (DO HỆ THỐNG TỰ TÌM KIẾM):
    {tai_lieu_tim_duoc}

    Nguyên tắc trả lời:
    1. Ưu tiên tuyệt đối dùng TÀI LIỆU TỪ DISCIPLENGEN ở trên để trả lời.
    2. Nếu tài liệu trên bị trống hoặc không liên quan, hãy dùng kiến thức chung của bạn, nhưng BẮT BUỘC phải ghi: "Theo các tài liệu thần học chung..." hoặc "Kinh Thánh chép...".
    3. Trả lời trực tiếp, sau đó đặt MỘT câu hỏi gợi mở để người học suy ngẫm.
    """

    # 4. Gửi cho AI suy nghĩ và trả lời
    with st.chat_message("ai"):
        with st.spinner("AI đang tìm kiếm trong thư viện DiscipleGen..."):
            response = st.session_state.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_thong_minh
            )
            
            cau_tra_loi = response.text
            # Nếu AI dùng tài liệu nội bộ, tự động đính kèm nguồn cho chuyên nghiệp
            if tai_lieu_tim_duoc != "":
                cau_tra_loi += f"\n\n*(Nguồn tham khảo: {nguon_goc})*"
                
            st.markdown(cau_tra_loi)
            
    st.session_state.messages.append({"role": "ai", "content": cau_tra_loi})
