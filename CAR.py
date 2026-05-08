import streamlit as st
import configparser
from datetime import datetime, timedelta
import io
import os
import re  # 導入正則表達式用於過濾文字

# PDF 生成套件
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
# 1. 選擇公司
selected_company = st.selectbox("公司名稱", options=companies)

def get_val(key):
    try: 
        val = config.get(selected_company, key).split(',')[0]
        return val.strip()
    except: 
        return ""

# 2. 自動抓取 INI 連動資訊
title = get_val("Titles")
name = get_val("Names")
plate = get_val("CarPlates")
reason = get_val("Reasons")
applicant = get_val("Applicants")

# 顯示連動資訊在畫面上
st.markdown("### 📋 申請單詳細資訊")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**職稱：** {title}")
    st.write(f"**姓名：** {name}")
    st.write(f"**車號：** {plate}")
with col2:
    st.write(f"**申請原因：** {reason}")
    st.write(f"**申請人：** {applicant}")

st.divider()

# 3. 日期與時間設定
st.subheader("⏰ 停車時間設定")
default_date = datetime.now() + timedelta(days=3)
selected_date = st.date_input("預計停車日期", value=default_date)

# 取得日期部件
roc_parts = get_roc_parts(selected_date)

# --- [更新] 時間選單：直接呈現 INI 原始內容 (包含中文字) ---
try: 
    display_times = config.get('Common', 'Times').split(',')
except: 
    display_times = ["09:00 ~ 18:00"]

selected_time = st.selectbox("預計停車時間", options=display_times)

# 填單日期 (自動抓取當天)
today = get_roc_parts(datetime.now())

# 側邊欄輔助模式
show_helper = st.sidebar.checkbox("開啟座標輔助模式", value=False)

# --- PDF 套印邏輯 ---
def generate_overlay_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w_a4, h_a4 = A4

    # 註冊字型
    font_name = "MSJH"
    font_bold_name = "MSJH-Bold"
    local_font = "msjh.ttc"
    local_font_bold = "msjhbd.ttc"

    if os.path.exists(local_font):
        pdfmetrics.registerFont(TTFont(font_name, local_font))
        pdfmetrics.registerFont(TTFont(font_bold_name, local_font_bold))
    else:
        try:
            pdfmetrics.registerFont(TTFont(font_name, "C:/Windows/Fonts/msjh.ttc"))
            pdfmetrics.registerFont(TTFont(font_bold_name, "C:/Windows/Fonts/msjhbd.ttc"))
        except:
            font_name = "Helvetica"

    # 畫入底圖
    bg_path = "template.png"
    if os.path.exists(bg_path):
        c.drawImage(bg_path, 0, 0, width=w_a4, height=h_a4)

    # 繪製文字
    c.setFont(font_name, 12)
    
    # 1. 申請部門與填單日期 (Y=750)
    c.drawString(150, 750, "KBT")              
    c.drawString(360, 750, today['year'])      
    c.drawString(410, 750, today['month'])     
    c.drawString(450, 750, today['day'])       

    # 2. 表格內容 (中間)
    c.drawString(150, 725, selected_company)  
    c.drawString(350, 725, title)             
    c.drawString(150, 690, name)              
    c.drawString(350, 690, plate)             
    
    # 預計停車日期 (Y=655)
    c.drawString(190, 655, roc_parts['year'])
    c.drawString(245, 655, roc_parts['month'])
    c.drawString(280, 655, roc_parts['day'])
    c.drawString(350, 655, roc_parts['year'])
    c.drawString(410, 655, roc_parts['month'])
    c.drawString(460, 655, roc_parts['day'])
    
    # --- [關鍵更新] 預計停車時間：套印時才過濾掉所有中文字與符號 ---
    try:
        # 1. 先將「時」替換為冒號，保留結構
        t_temp = selected_time.replace("時", ":")
        # 2. 只留下數字、冒號、波浪號，其餘(分、全日、括號、空格)全部刪除
        t_clean = re.sub(r'[^\d:~]', '', t_temp)
        # 3. 進行拆解
        parts = t_clean.replace('~', ':').split(':')
        
        sh = parts[0].strip() # 開始時
        sm = parts[1].strip() # 開始分
        eh = parts[-2].strip() if len(parts) > 2 else "" # 結束時
        em = parts[-1].strip() if len(parts) > 2 else "" # 結束分
        
        # 填入時、分位置 (Y=620)
        c.drawString(275, 620, sh)
        c.drawString(335, 620, sm)
        c.drawString(425, 620, eh)
        c.drawString(485, 620, em)
    except:
        # 萬一拆解失敗，直接印出原始字串 (保險機制)
        c.drawString(275, 620, selected_time)
    
    # 3. 申請原因 (Y=555)
    c.drawString(160, 555, reason)

    # 4. 簽署區 (Y=530)
    c.setFont(font_name, 12)
    c.drawString(410, 530, applicant) 

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

# --- 下載按鈕 ---
st.divider()
pdf_output = generate_overlay_pdf()
st.download_button(
    label="📥 生成並下載套印 PDF",
    data=pdf_output,
    file_name=f"停車申請單_{name}.pdf",
    mime="application/pdf",
    use_container_width=True
)
