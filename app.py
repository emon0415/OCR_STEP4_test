import streamlit as st
from PIL import Image
import cv2
import numpy as np
import pytesseract
import requests
import io
import xml.etree.ElementTree as ET
import speech_recognition as sr


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    img = np.array(image.convert('RGB'))
    img = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

st.title("OCR & バーコードスキャンデモ")
tab1, tab2, tab3, tab4 = st.tabs(["OCR", "バーコードスキャン", "本検索", "音声入力"])

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
    scan_mode = st.radio("スキャンモードを選択してください", 
                         ("リアルタイムスキャン (ローカル用)", "静止画撮影スキャン (デプロイ用)"))
    
    if scan_mode == "リアルタイムスキャン (ローカル用)":
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
    else:
        camera_image = st.camera_input("バーコードを撮影してください (デプロイ用)")
        if camera_image:
            image = Image.open(camera_image)
            st.image(image, caption="撮影した画像", use_column_width=True)
            np_img = np.array(image.convert("RGB"))
            detector = cv2.barcode_BarcodeDetector()
            retval, decoded_info, decoded_type = detector.detectAndDecode(np_img)
            if retval and decoded_info is not None and len(decoded_info) > 0 and str(decoded_info[0]) != "":
                result_text = str(decoded_info[0])
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
            # --- サムネイル画像取得 ---
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

            # OpenSearch API で書誌情報を取得（XML形式）
            try:
                url_opensearch = f"https://ndlsearch.ndl.go.jp/api/opensearch?isbn={book_ISBN}&format=json"
                resp_meta = requests.get(url_opensearch)
                if resp_meta.ok:
                    if not resp_meta.text.strip():
                        st.warning("書誌情報のレスポンスが空です。対象のISBNに該当する情報が存在しない可能性があります。")
                    else:
                        try:
                            root = ET.fromstring(resp_meta.text)
                        except Exception as e:
                            st.error(f"書誌情報のJSON解析に失敗しました: {e}")
                            st.stop()
                    
                    channel = root.find('channel')
                    if channel is None:
                        st.warning("書誌情報が見つかりませんでした。(channel が見つからない)")
                        st.stop()
                    item = channel.find('item')
                    if item is None:
                        st.warning("書誌情報が見つかりませんでした。(item が見つからない)")
                        st.stop()

                    title = None
                    creator =None
                    pub_date = None
                    price = None
                    for child in item:
                        tag = child.tag
                        if tag.endswith('title') and title is None:
                            title = child.text
                        elif tag.endswith('creator') and creator is None:
                            creator = child.text
                        elif tag.endswith('date') and pub_date is None:
                            pub_date = child.text
                        elif tag.endswith('price') and price is None:
                            price = child.text

                    st.subheader("書誌情報")
                    st.write(f"**タイトル**: {title if title else '不明'}")
                    st.write(f"**著者**: {creator if creator else '不明'}")
                    st.write(f"**出版社**: {pub_date if pub_date else '不明'}")
                    st.write(f"**価格**: {price if price else '不明'}")
                else:
                    st.error(f"書誌情報の取得に失敗しました。HTTPステータス: {resp_meta.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"書誌情報取得時に通信エラーが発生しました: {e}")

with tab4:
    set_language_list = {
    '日本語' : 'ja',
    '英語' : 'en-US',
    }

    set_language = '日本語'

    def file_speech_to_text(audio_file,set_language):
        with sr.AudioFile(audio_file) as source:
            audio = sr.Recognizer().record(source)

        try:
            text = sr.Recognizer().recognize_google(audio, language=set_language_list[set_language])
        except:
            text = '音声認識に失敗しました'
        return text

    def mic_speech_to_text(set_language):
        with sr.Microphone() as source:
            audio = sr.Recognizer().listen(source)
        try:
            text= sr.Recognizer().recognize_google(audio, language=set_language_list[set_language])
        except:
            text = '音声認識に失敗しました'
        return text


    st.title('文字起こしアプリ')
    st.write('音声認識する言語を選んでください')
    set_language = st.selectbox('音声認識する言語を選んでください。', set_language_list.keys())
    current_language_state = st.empty()
    current_language_state.write('選択中の言語:' + set_language)

    file_upload =st.file_uploader('ここに音声認識したファイルをアップロードしてください。', type=['wav'])

    if (file_upload != None):
        st.write('音声認識結果:')
        result_text = file_speech_to_text(file_upload, set_language)
        st.write(result_text)
        st.audio(file_upload)

    st.write('マイクでの音声認識はこちらのボタンから')

    if st.button('音声認識開始'):
        state = st.empty()
        state.write('音声認識中')
        result_text = mic_speech_to_text(set_language)
        state.write('音声認識結果：')
        st.write(result_text)

