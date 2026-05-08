import streamlit as st
import configparser
from datetime import datetime, timedelta
import io
import os

# PDF 生成套件 (僅需 reportlab)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 基礎設定 ---
st.set_page_config(page_title="神通套印產生器", layout="centered")

def get_roc_parts(date_obj):
    """取得民國年、月、日的數字"""
    return {
        "year": str(date_obj.year - 1911),
        "month": str(date_obj.month),
        "day": str(date_obj.day)
    }

# 1. 讀取設定檔
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
companies = config.sections()
if 'Common' in companies: companies.remove('Common')

st.title("🖨️ 神通申請單「套印」產生器")

# --- UI 介面 ---
selected_company = st.selectbox("公司名稱", options=companies)
# 側邊欄：座標輔助模式
show_helper = st.sidebar.checkbox("開啟座標輔助模式", value=False)

def get_val(key):
    try: return config.get(selected_company, key).split(',')[0]
    except: return ""

title = get_val("Titles")
name = get_val("Names")
plate = get_val("CarPlates")
reason = get_val("Reasons")
applicant = get_val("Applicants")

# 預計停車日期 (使用 Streamlit 內建選擇器，不需要 tkcalendar)
default_date = datetime.now() + timedelta(days=3)
selected_date = st.date_input("預計停車日期", value=default_date)

# 轉換日期格式
roc_date_parts = get_roc_parts(selected_date)
roc_date_range = f"{roc_date_parts['year']}/{roc_date_parts['month']}/{roc_date_parts['day']}"

try: 
    common_times = config.get('Common', 'Times').split(',')
except: 
    common_times = ["09:00~18:00"]
selected_time = st.selectbox("預計停車時間", options=common_times)

# 填單日期 (自動抓取當天)
today = get_roc_parts(datetime.now())

# --- PDF 套印邏輯 ---
def generate_overlay_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w_a4, h_a4 = A4

    # 1. 註冊字型
    font_name = "MSJH"
    font_bold_name = "MSJH-Bold"
    local_font = "msjh.ttc"
    local_font_bold = "msjhbd.ttc"

    if os.path.exists(local_font):
        pdfmetrics.registerFont(TTFont(font_name, local_font))
        pdfmetrics.registerFont(TTFont(font_bold_name, local_font_bold))
    else:
        # 本地測試路徑
        try:
            pdfmetrics.registerFont(TTFont(font_name, "C:/Windows/Fonts/msjh.ttc"))
            pdfmetrics.registerFont(TTFont(font_bold_name, "C:/Windows/Fonts/msjhbd.ttc"))
        except:
            font_name = "Helvetica" # 備用

    # 2. 畫入底圖
    bg_path = "template.png"
    if os.path.exists(bg_path):
        c.drawImage(bg_path, 0, 0, width=w_a4, height=h_a4)

    # 3. 繪製文字
    c.setFont(font_name, 12)
    
    # 申請部門與填單日期
    c.drawString(150, 750, "KBT")             
    c.drawString(360, 750, today['year'])      
    c.drawString(410, 750, today['month'])     
    c.drawString(450, 750, today['day'])       

    # 表格內容
    c.drawString(150, 725, selected_company)  
    c.drawString(350, 725, title)             
    c.drawString(350, 690, name)              
    c.drawString(410, 650, plate)             
    c.drawString(160, 615, f"{roc_date_range} ~ {roc_date_range}")
    c.drawString(160, 580, selected_time)
    
    # 申請原因 (直列)
    reason_y = 520
    for char in reason:
        c.drawCentredString(75, reason_y, char)
        reason_y -= 15

    # 座標輔助線
    if show_helper:
        c.setStrokeColorRGB(1, 0, 0)
        c.setFont("Helvetica", 8)
        for x in range(0, int(w_a4), 50):
            c.line(x, 0, x, h_a4)
            c.drawString(x+2, 10, str(x))
        for y in range(0, int(h_a4), 50):
            c.line(0, y, w_a4, y)
            c.drawString(10, y+2, str(y))

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 下載區 ---
st.divider()
pdf_output = generate_overlay_pdf()
st.download_button(
    label="📥 點我下載套印 PDF",
    data=pdf_output,
    file_name=f"停車申請單_{name}.pdf",
    mime="application/pdf",
    use_container_width=True
)
