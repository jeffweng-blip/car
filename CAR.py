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
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# --- 基礎設定 ---
st.set_page_config(page_title="神通企業總部-停車申請單產生器", layout="centered")

def get_roc_date_str(date_obj):
    """將 datetime 轉為 民國年格式字串"""
    roc_year = date_obj.year - 1911
    return f"{roc_year} 年 {date_obj.strftime('%m 月 %d 日')}"

# 1. 讀取 INI 設定檔
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
companies = config.sections()
if 'Common' in companies:
    companies.remove('Common')

st.title("🚗 停車申請單產生器")

# 2. 介面輸入區
selected_company = st.selectbox("公司名稱", options=companies)

def get_val(key):
    try:
        return config.get(selected_company, key).split(',')[0]
    except:
        return ""

title = get_val("Titles")
name = get_val("Names")
plate = get_val("CarPlates")
reason = get_val("Reasons")
applicant = get_val("Applicants")

col1, col2 = st.columns(2)
with col1:
    st.info(f"**職稱：** {title}")
    st.info(f"**姓名：** {name}")
    st.info(f"**車號：** {plate}")
with col2:
    st.info(f"**申請原因：** {reason}")
    st.info(f"**申請人：** {applicant}")

st.divider()
st.subheader("日期與時間設定")
# 預設日期為 3 天後
default_date = datetime.now() + timedelta(days=3)
selected_date = st.date_input("預計停車日期", value=default_date)
roc_selected_date = get_roc_date_str(selected_date)

try:
    common_times = config.get('Common', 'Times').split(',')
except:
    common_times = ["09:00 時 00 分 ~ 18 時 00 分"]
selected_time = st.selectbox("預計停車時間", options=common_times)

today_roc = get_roc_date_str(datetime.now())

# --- PDF 生成函數 ---
def generate_pdf_buffer():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    font_name = "MSJH"
    font_bold_name = "MSJH-Bold"
    
    # 字型路徑判斷
    local_font = "msjh.ttc"
    local_font_bold = "msjhbd.ttc"
    
    if os.path.exists(local_font):
        pdfmetrics.registerFont(TTFont(font_name, local_font))
        pdfmetrics.registerFont(TTFont(font_bold_name, local_font_bold))
    else:
        # 本地 Windows 測試路徑
        pdfmetrics.registerFont(TTFont(font_name, "C:/Windows/Fonts/msjh.ttc"))
        pdfmetrics.registerFont(TTFont(font_bold_name, "C:/Windows/Fonts/msjhbd.ttc"))

    t_x, t_top_y, t_w = 57.5, height - 95, 480
    row_hs = [35, 35, 35, 35, 85]

    # 1. 標題
    c.setFont(font_name, 20)
    c.drawCentredString(width/2, height - 60, "神通企業總部大樓臨時停車申請單")
    
    # 2. 表頭 (申請部門、填單日期)
    c.setFont(font_name, 11)
    c.drawString(t_x, t_top_y + 8, "申請部門：")
    c.drawRightString(t_x + t_w, t_top_y + 8, f"填單日期： {today_roc}")

    # 3. 表格數據 (使用您圖片中的格式)
    full_date_range = f"{roc_selected_date} ~ {roc_selected_date}"
    data = [
        ['公司', selected_company, '職稱', title],
        ['姓名', name, '車號', plate],
        ['預計停車日期', full_date_range, '', ''],
        ['預計停車時間', selected_time, '', ''],
        ['申請\n原因', reason, '', '']
    ]

    table = Table(data, colWidths=[80, 160, 80, 160], rowHeights=row_hs)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (1, 2), (3, 2)), 
        ('SPAN', (1, 3), (3, 3)), 
        ('SPAN', (1, 4), (3, 4)),
        ('ALIGN', (1, 4), (1, 4), 'LEFT'),
        ('LEFTPADDING', (1, 4), (1, 4), 12),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, t_x, t_top_y - sum(row_hs))

    # 4. 雙線外框
    c.setLineWidth(0.8)
    c.rect(t_x, t_top_y - sum(row_hs), t_w, sum(row_hs))
    c.rect(t_x - 2, t_top_y - sum(row_hs) - 2, t_w + 4, sum(row_hs) + 4)

    # 5. 簽署區 (根據您的新圖片修改排版)
    y_f = t_top_y - sum(row_hs) - 25
    c.setFont(font_name, 12)
    # 部級主管在左側
    c.drawString(t_x, y_f, "部級主管：")
    # 申請人在右側
    c.drawRightString(t_x + t_w, y_f, f"申請人：{applicant}")
    
    # 總務部獨立一行 (參考一般公文排版)
    c.drawString(t_x, y_f - 40, "總務部：")
    
    # 6. 表單編號與底部警語
    c.setFont(font_name, 9)
    c.drawString(t_x, y_f - 75, "GEP-99-4-12-A")
    
    c.setFont(font_bold_name, 10.5)
    c.drawCentredString(width/2, y_f - 100, "*本單須經部級(含)以上主管及總務部簽字後，送警衛室憑單放行*")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 下載按鈕 ---
st.divider()
pdf_data = generate_pdf_buffer()
st.download_button(
    label="📥 下載 PDF 申請單",
    data=pdf_data,
    file_name=f"停車申請單_{name}.pdf",
    mime="application/pdf",
    use_container_width=True
)
