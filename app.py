from flask import Flask, render_template, request
import requests
import xml.etree.ElementTree as ET
import base64
import os

# --- 기존 헬퍼 함수들은 그대로 사용 ---

# API 키
API_KEY = "4A7CB46C6B20C81A26D17C60503C92C4"
LOGO_FILE = "logo.jpg"

def image_to_base64(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"

def get_word_info(word):
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
    
    watermark_style = ""
    if logo_data_uri:
        watermark_style = f".card::before {{ content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: url('{logo_data_uri}'); background-position: center; background-repeat: no-repeat; background-size: 50%; opacity: 0.15; z-index: -1; }}"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=KoPub+Batang:wght@400;700&display=swap');
        body {{ margin: 10px; font-family: 'KoPub Batang', serif; }}
        .card-container {{ display: flex; flex-wrap: wrap; gap: 0; }}
        .card {{ width: 63.5mm; height: 38.1mm; border: 1px dotted #ccc; box-sizing: border-box; padding: 3mm; display: flex; flex-direction: column; position: relative; overflow: hidden; }}
        {watermark_style}
        .word {{ font-size: 14pt; font-weight: bold; text-align: center; border-bottom: 1px solid #eee; padding-bottom: 1mm; margin-bottom: 1mm; }}
        .definitions {{ list-style-position: inside; padding-left: 0; margin: 0; font-size: 8pt; flex-grow: 1; }}
        .definitions li {{ margin-bottom: 1mm; }}
        .definition {{ display: inline; }}
        .example {{ font-size: 7pt; color: #555; font-style: italic; padding-left: 10px; }}
        @media print {{ body {{ margin: 0; }} .card {{ border: none; page-break-inside: avoid; }} }}
    </style>
    """
    html = f"""
    <html><head><meta charset='utf-8'><title>단어 라벨 인쇄</title>{css}</head>
    <body><div class="card-container">{cards_html}</div></body></html>"""
    return html

# --- Flask 웹 애플리케이션 부분 ---
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 사용자가 폼을 통해 단어를 입력한 경우
        input_text = request.form['words']
        if not input_text:
            return render_template('index.html', error="단어를 입력해주세요.")
        
        unique_words = list(dict.fromkeys([w.strip() for w in input_text.replace("\n", ",").split(",") if w.strip()]))
        words_data = {word: get_word_info(word) for word in unique_words}
        logo_data = image_to_base64(LOGO_FILE)
        
        # 결과 HTML을 직접 반환
        return generate_cards_html(words_data, logo_data)
    
    # GET 요청일 경우, 입력 폼을 보여줌
    return render_template('index.html')

if __name__ == '__main__':
    # 이 부분은 Render에서는 Gunicorn이 대체하므로 직접 실행되지 않음
    app.run(debug=True)