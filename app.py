import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, scrolledtext
import requests
import xml.etree.ElementTree as ET
import tempfile
import webbrowser
import threading
import base64
import os

# === 사용자 설정 ===
API_KEY = "4A7CB46C6B20C81A26D17C60503C92C4"
LOGO_FILE = "logo.jpg" # 워터마크로 사용할 로고 파일 이름

# === 로고 이미지 처리 함수 ===
def image_to_base64(file_path):
    """이미지 파일을 읽어 Base64 데이터 URI로 변환합니다."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"

# === API 호출 함수 ===
def get_word_info(word):
    """지정한 단어의 여러 뜻과 예문을 리스트 형태로 가져옵니다."""
    url = f"https://stdict.korean.go.kr/api/search.do?key={API_KEY}&q={word}&req_type=xml&method=exact"
    meanings = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        if not items:
            return [{"definition": "[검색 결과 없음]"}]
        for item in items:
            word_name = item.findtext("word")
            for sense in item.findall("sense"):
                definition = sense.findtext("definition")
                example = sense.findtext("trans_entry/example")
                info = {
                    "word": word_name,
                    "definition": definition if definition else "",
                    "example": example.replace('-', ' - ') if example else ""
                }
                meanings.append(info)
        return meanings
    except Exception as e:
        return [{"definition": f"[오류 발생: {e}]"}]

# === 인쇄용 HTML 생성 함수 (워터마크 기능 추가) ===
def generate_cards_html(words_data, logo_data_uri):
    cards_html = ""
    for word, infos in words_data.items():
        cards_html += '<div class="card">'
        cards_html += f'<div class="word">{word}</div>'
        cards_html += '<ol class="definitions">'
        for info in infos[:3]:
            cards_html += '<li>'
            cards_html += f'<div class="definition">{info["definition"]}</div>'
            if info["example"]:
                cards_html += f'<div class="example">예) {info["example"]}</div>'
            cards_html += '</li>'
        cards_html += '</ol></div>'
    
    # 워터마크 CSS: 로고 데이터가 있을 경우에만 배경 이미지로 추가
    watermark_style = ""
    if logo_data_uri:
        watermark_style = f"""
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('{logo_data_uri}');
            background-position: center;
            background-repeat: no-repeat;
            background-size: 60%;
            opacity: 0.15; /* 워터마크 투명도 */
            z-index: -1;
        }}
        """

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=KoPub+Batang:wght@400;700&display=swap');
        body {{ margin: 0; font-family: 'KoPub Batang', serif; }}
        .card {{
            width: 80mm;
            height: 56mm;
            border: 1px solid #ccc;
            box-sizing: border-box;
            padding: 5mm;
            display: flex;
            flex-direction: column;
            page-break-after: always;
            position: relative; /* 워터마크 위치 기준 */
        }}
        {watermark_style}
        .word {{ font-size: 18pt; font-weight: bold; text-align: center; border-bottom: 1px solid #eee; padding-bottom: 3mm; margin-bottom: 3mm; }}
        .definitions {{ list-style-position: inside; padding-left: 0; margin: 0; font-size: 10pt; flex-grow: 1; }}
        .definitions li {{ margin-bottom: 2mm; }}
        .definition {{ display: inline; }}
        .example {{ font-size: 9pt; color: #555; font-style: italic; padding-left: 15px; }}
        
        @media print {{ @page {{ size: 80mm 56m; margin: 0; }} }}
    </style>
    """
    html = f"<html><head><meta charset='utf-8'><title>단어 카드 인쇄</title>{css}</head><body>{cards_html}</body></html>"
    return html

# === 단어 처리 로직 ===
def process_words_for_card():
    process_button.config(state=tk.DISABLED)
    input_text = text_input.get("1.0", tk.END).strip()
    if not input_text:
        messagebox.showwarning("경고", "단어를 입력해주세요.")
    else:
        unique_words = list(dict.fromkeys([w.strip() for w in input_text.replace("\n", ",").split(",") if w.strip()]))
        words_data = {word: get_word_info(word) for word in unique_words}
        logo_data = image_to_base64(LOGO_FILE)
        html_content = generate_cards_html(words_data, logo_data)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
            f.write(html_content)
            webbrowser.open(f"file://{f.name}")
    process_button.config(state=tk.NORMAL)

# === 쓰레드 시작 함수 ===
def start_processing_thread():
    thread = threading.Thread(target=process_words_for_card, daemon=True)
    thread.start()

# === Tkinter GUI 설정 ===
window = tk.Tk()
window.title("책나무 구월에듀포레점 국어사전")
window.geometry("500x450") # 창 크기 키움

# 기본 폰트 설정
default_font = tkfont.nametofont("TkDefaultFont")
default_font.configure(family="Malgun Gothic", size=10)

label = tk.Label(window, text="출력할 단어를 입력하세요:")
label.pack(pady=10, padx=10, anchor='w')

text_input = scrolledtext.ScrolledText(window, width=45, height=10, font=("Malgun Gothic", 11))
text_input.pack(pady=5, padx=10, fill='x')

process_button = tk.Button(window, text="출력", command=start_processing_thread)
process_button.pack(pady=10, padx=10, fill='x', ipady=10)

# 하단 저작권 문구 추가
footer_label = tk.Label(window, text="ⓒ책나무 구월에듀포레점 2025", fg="gray")
footer_label.pack(side='bottom', pady=5)

window.mainloop()