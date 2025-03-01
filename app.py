import streamlit as st
from PIL import Image
import cv2
import numpy as np
import pytesseract
import requests
import io


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    img = np.array(image.convert('RGB'))
    img = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

st.title("OCR & バーコードスキャンデモ")
tab1, tab2, tab3 = st.tabs(["OCR", "バーコードスキャン", "本検索"])

with tab1:
    st.header("OCR")
    uploaded_files = st.file_uploader("画像ファイルを選択してください", type=["png", "jpg", "jpeg", "bmp", "tiff"], accept_multiple_files=True)

    if uploaded_files:
        for idx, uploaded_file in enumerate(uploaded_files, 1):
            image = Image.open(uploaded_file)
            processed_image = preprocess_image(image)
            col1, col2 = st.columns(2)
            with col1:
                st.image(image, caption=f"オリジナル画像 {idx}: {uploaded_file.name}", use_column_width=True)
            with col2:
                st.image(processed_image, caption=f"前処理後画像{idx}", use_column_width=True)
            text = pytesseract.image_to_string(processed_image, lang='jpn')
            st.text_area(f"OCR結果 ({uploaded_file.name})", text, height=200)
            
with tab2:
    st.header("バーコードスキャン")
    if st.button("スキャン開始"):
        cap = cv2.VideoCapture(0)
        detector = cv2.barcode_BarcodeDetector()
        barcode_detected = False
        result_text =""
        frame_placeholder = st.empty()
        # バーコードが検出されるまでループ
        while cap.isOpened() and not barcode_detected:
            ret, frame = cap.read()
            if not ret:
                break
            retval, decoded_info, decoded_type = detector.detectAndDecode(frame)
            # decoded_infoがNoneまたは空文字列でなければ検出成功とみなす
            if (retval and decoded_info is not None and len(decoded_info) > 0
                and str(decoded_info[0]) !=""):
                result_text = str(decoded_info[0])
                # 結果を画像上に描画
                cv2.putText(frame, result_text, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                barcode_detected = True
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb)
        cap.release()
        if barcode_detected:
            st.success(f"検出されたバーコード: {result_text}")
        else:
            st.error("バーコードが検出されませんでした。")
with tab3:
    st.header("本検索")
    book_ISBN = st.text_input("本のISBN(13桁)を入力してください")
    if st.button("検索"):
        if len(book_ISBN) !=13 or not book_ISBN.isdigit():
            st.error("正しい13桁のISBNを入力してください。")
        else:
            try:
                thumb_url = f"https://ndlsearch.ndl.go.jp/thumbnail/{book_ISBN}.jpg"
                thumb_response = requests.get(thumb_url)
                if thumb_response.ok:
                    try:
                        cover_image = Image.open(io.BytesIO(thumb_response.content))
                        st.image(cover_image, caption=f"書影 for ISBN{book_ISBN}")
                    except Exception as e:
                        st.error(f"書影が見つかりませんでした エラー:{e}")
                else:
                    st.error("サムネイル取得に失敗しました。HTTPステータス: {thumb_response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"サムネイル取得時に通信エラーが発生しました:{e}")
            
            st.markdown("---")

            # OpenSearch API で書誌情報を取得（JSON形式）
            try:
                url_opensearch = f"https://ndlsearch.ndl.go.jp/api/opensearch?isbn={book_ISBN}&format=json"
                resp_meta = requests.get(url_opensearch)
                if resp_meta.ok:
                    try:
                        data = resp_meta.json()
                    except Exception as e:
                        st.error(f"書誌情報のJSON解析に失敗しました: {e}")
                        st.stop()
                    
                    # 典型的なレスポンス例: data["@graph"][0]["items"][0] にメタデータが格納される
                    items = data.get("@graph", [])
                    if not items:
                        st.warning("書誌情報が見つかりませんでした。(@graph が空)")
                        st.stop()

                    # "items"キーの中に複数書誌情報があることが多い
                    graph0 = items[0]
                    record_list = graph0.get("items", [])
                    if not record_list:
                        st.warning("書誌情報が見つかりませんでした。(items が空)")
                        st.stop()
                    
                    record = record_list[0]
                    # タイトル・著者・出版社を取得 (キーは "dc:title", "dc:creator", "dc:publisher" など)
                    title = record.get("dc:title", "不明")
                    creator = record.get("dc:creator", "不明")
                    publisher = record.get("dc:publisher", "不明")

                    st.subheader("書誌情報")
                    st.write(f"**タイトル**: {title}")
                    st.write(f"**著者**: {creator}")
                    st.write(f"**出版社**: {publisher}")
                else:
                    st.error(f"書誌情報の取得に失敗しました。HTTPステータス: {resp_meta.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"書誌情報取得時に通信エラーが発生しました: {e}")

