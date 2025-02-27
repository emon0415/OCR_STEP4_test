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
    camera_image = st.camera_input("バーコードを撮影してください")
    if camera_image:
        image = Image.open(camera_image)
        st.image(image, caption="撮影したバーコード画像", use_column_width=True)
        np_img = np.array(image.convert("RGB"))
        detector = cv2.barcode_BarcodeDetector()
        retval, decoded_info, decoded_type = detector.detectAndDecode(np_img)
        if not isinstance(decoded_info, (list, tuple)):
            decoded_info = []
        if not isinstance(decoded_info, (list, tuple)):
            decoded_type = []
        if retval and decoded_info is not None and decoded_type is not None:
            for info, btype in zip(decoded_info, decoded_type):
                st.write(f"検出されたバーコード ({btype}): {info}")
                if btype == "EAN13":
                    st.write("ISBNとして検出された可能性があります。")
        else:
            st.write("バーコードが検出されませんでした。")

