import streamlit as st
import configparser
from datetime import datetime, timedelta
import io
import os

# PDF 生成套件
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 基礎設定 ---
st.set_page_config(page_title="神通套印產生器", layout="centered")

def get_roc_date_str(date_obj):
    roc_year = date_obj.year - 1911
    return f"{roc_year}/{date_obj.strftime('%m/%d')}"

# 1. 讀取設定檔
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
companies = config.sections()
if 'Common' in companies: companies.remove('Common')

st.title("🖨️ 神通申請單「套印」產生器")

# --- UI 介面 ---
selected_company = st.selectbox("公司名稱", options=companies)
# 側邊欄：座標輔助模式
show_helper = st.sidebar.checkbox("開啟座標輔助模式", value=True)
st.sidebar.write("💡 開啟後，PDF 會顯示紅色座標點與尺規，方便你對齊。")

def get_val(key):
    try: return config.get(selected_company, key).split(',')[0]
    except: return ""

title = get_val("Titles")
name = get_val("Names")
plate = get_val("CarPlates")
reason = get_val("Reasons")
applicant = get_val("Applicants")

# 日期與時間
default_date = datetime.now() + timedelta(days=3)
selected_date = st.date_input("預計停車日期", value=default_date)
roc_selected_date = get_roc_date_str(selected_date)

try: common_times = config.get('Common', 'Times').split(',')
except: common_times = ["09:00~18:00"]
selected_time = st.selectbox("預計停車時間", options=common_times)

# --- PDF 套印邏輯 ---
def generate_overlay_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w_a4, h_a4 = A4  # 約 595 x 842 點

    # 1. 註冊字型
    font_name = "MSJH"
    local_font = "msjh.ttc"
    if os.path.exists(local_font):
        pdfmetrics.registerFont(TTFont(font_name, local_font))
    else:
        pdfmetrics.registerFont(TTFont(font_name, "C:/Windows/Fonts/msjh.ttc"))

    # 2. 畫入底圖 (請確保專案內有 template.png)
    bg_path = "template.png"
    if os.path.exists(bg_path):
        c.drawImage(bg_path, 0, 0, width=w_a4, height=h_a4)
    else:
        st.warning("⚠️ 找不到底圖 template.png，目前僅顯示文字。")

    # 3. 繪製文字 (這是最需要微調的部分，我先預設一些座標)
    c.setFont(font_name, 12)
    
    # 範例座標 (X, Y) - 請根據輔助模式看到的數字來修改這裡
    c.drawString(725, 150, selected_company)  # 公司名稱
    c.drawString(410, 685, title)             # 職稱
    c.drawString(160, 650, name)              # 姓名
    c.drawString(410, 650, plate)             # 車號
    
    # 日期 (民國年格式)
    c.drawString(160, 615, roc_selected_date + " ~ " + roc_selected_date)
    
    # 時間
    c.drawString(160, 580, selected_time)
    
    # 申請原因 (若要直列，需要迴圈繪製)
    reason_y = 500
    for char in reason[:10]: # 限制前10個字
        c.drawCentredString(100, reason_y, char)
        reason_y -= 15

    # 4. 座標輔助線 (開發完畢後可關閉)
    if show_helper:
        c.setStrokeColorRGB(1, 0, 0) # 紅色
        c.setFont("Helvetica", 8)
        # 畫尺規
        for x in range(0, int(w_a4), 50):
            c.line(x, 0, x, h_a4)
            c.drawString(x+2, 10, str(x))
        for y in range(0, int(h_a4), 50):
            c.line(0, y, w_a4, y)
            c.drawString(10, y+2, str(y))
        # 標記當前文字位置
        c.circle(160, 685, 2, stroke=1, fill=0) # 標記公司名稱位置

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 下載區 ---
st.divider()
if st.button("🚀 準備下載 PDF"):
    pdf_output = generate_overlay_pdf()
    st.download_button(
        label="📥 點我下載套印 PDF",
        data=pdf_output,
        file_name=f"停車申請單_{name}.pdf",
        mime="application/pdf"
    )
