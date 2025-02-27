import streamlit as st
from PIL import Image
import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    img = np.array(image.convert('RGB'))
    img = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

st.title("OCR & バーコードスキャンデモ")
tab1, tab2 = st.tabs(["OCR", "バーコードスキャン"])

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

