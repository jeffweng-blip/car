import streamlit as st
import configparser
from datetime import datetime, timedelta
import io
import os
import re

# PDF 生成套件
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 基礎設定 ---
st.set_page_config(page_title="臨時停車申請單產生器", layout="wide")

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

# --- 版面縮排設定 ---
m_left, m_content, _ = st.columns([1, 8, 1])

with m_content:
    # 標題與子標題字級相同
    st.markdown("### 臨時停車申請單 產生器")

    # --- UI 介面 ---
    # 選擇公司 (寬度 1/3)
    col_company, _ = st.columns([1, 2])
    with col_company:
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

    # 顯示詳細資訊：垂直排列
    st.markdown("### 📋 申請單詳細資訊")
    st.write(f"**職稱：** {title}")
    st.write(f"**姓名：** {name}")
    st.write(f"**車號：** {plate}")
    st.write(f"**申請原因：** {reason}")
    st.write(f"**申請人：** {applicant}")

    st.divider()

    # 3. 日期與時間設定
    st.subheader("⏰ 停車時間設定")
    
    # 預計停車日期 (寬度 1/3)
    col_date, _ = st.columns([1, 2])
    with col_date:
        default_date = datetime.now() + timedelta(days=3)
        selected_date = st.date_input("預計停車日期", value=default_date)
        roc_parts = get_roc_parts(selected_date)

    # 時間選單 (寬度 1/3)
    col_time, _ = st.columns([1, 2])
    with col_time:
        try: 
            display_times = config.get('Common', 'Times').split(',')
        except: 
            display_times = ["09:00 ~ 18:00"]
        selected_time = st.selectbox("預計停車時間", options=display_times)

    today = get_roc_parts(datetime.now())
    show_helper = st.sidebar.checkbox("開啟座標輔助模式", value=False)

    # --- PDF 套印邏輯 ---
    def generate_overlay_pdf():
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w_a4, h_a4 = A4

        font_name = "MSJH"
        local_font = "msjh.ttc"

        if os.path.exists(local_font):
            pdfmetrics.registerFont(TTFont(font_name, local_font))
        else:
            try:
                pdfmetrics.registerFont(TTFont(font_name, "C:/Windows/Fonts/msjh.ttc"))
            except:
                font_name = "Helvetica"

        bg_path = "template.png"
        if os.path.exists(bg_path):
            c.drawImage(bg_path, 0, 0, width=w_a4, height=h_a4)

        # 套印字體大小 10
        c.setFont(font_name, 10)
        
        # 1. 申請部門與填單日期
        c.drawString(150, 750, "KBT")              
        c.drawString(360, 750, today['year'])      
        c.drawString(410, 750, today['month'])     
        c.drawString(450, 750, today['day'])       

        # 2. 表格內容
        c.drawString(150, 725, selected_company)  
        c.drawString(350, 725, title)             
        c.drawString(150, 690, name)              
        c.drawString(350, 690, plate)             
        
        # 預計停車日期 (修正縮排，移入函數內)
        c.drawString(190, 657, roc_parts['year'])
        c.drawString(245, 657, roc_parts['month'])
        c.drawString(290, 657, roc_parts['day'])
        c.drawString(350, 657, roc_parts['year'])
        c.drawString(410, 657, roc_parts['month'])
        c.drawString(455, 657, roc_parts['day'])
        
        # 預計停車時間 (修正縮排，移入函數內)
        try:
            t_temp = selected_time.replace("時", ":")
            t_clean = re.sub(r'[^\d:~]', '', t_temp)
            parts = t_clean.replace('~', ':').split(':')
            sh, sm = parts[0].strip(), parts[1].strip()
            eh = parts[-2].strip() if len(parts) > 2 else ""
            em = parts[-1].strip() if len(parts) > 2 else ""
            
            # 使用你調整過的座標
            c.drawString(190, 623, sh)
            c.drawString(245, 623, sm)
            c.drawString(310, 623, eh)
            c.drawString(365, 623, em)
        except:
            c.drawString(275, 620, selected_time)
        
        # 3. 申請原因
        c.drawString(160, 575, reason)

        # 4. 簽署區
        c.drawString(410, 530, applicant) 

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

    # --- 下載按鈕 (寬度 1/3) ---
    st.divider()
    col_btn, _ = st.columns([1, 2])
    with col_btn:
        pdf_output = generate_overlay_pdf()
        st.download_button(
            label="📥 生成並下載套印 PDF",
            data=pdf_output,
            file_name=f"停車申請單_{name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
