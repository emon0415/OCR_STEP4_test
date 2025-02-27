import streamlit as st
from PIL import Image
import cv2
import numpy as np
import pytesseract
from pyzbar.pyzbar import decode

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
            #st.download_button("結果をダウンロード", data=text, file_name=f"OCR_{idx:03}.txt", mime="text/plain")
with tab2:
    st.header("バーコードスキャン")
    camera_image = st.camera_input("バーコードを撮影してください")
    if camera_image:
        image = Image.open(camera_image)
        st.image(image, caption="撮影したバーコード画像", use_column_width=True)
        np_img = np.array(image.convert("RGB"))
        barcodes = decode(np_img)
        if barcodes:
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type
                st.write(f"検出されたバーコード ({barcode_type}): {barcode_data}")
                if barcode_type == "EAN13":
                    st.write("ISBNとして検出された可能性があります。")
        else:
            st.write("バーコードが検出されませんでした。")

