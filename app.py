import streamlit as st
from bundler import bundle_html

# --- 翻訳データ ---
TRANSLATIONS = {
    "Japanese": {
        "page_title": "Webページ単一ファイル変換",
        "app_title": "🌐 Webページ単一ファイル変換機",
        "desc": """
        指定したURLのWebページをダウンロードし、画像やCSSを埋め込んだ**単一のHTMLファイル**に変換します。
        - 動的サイト(SPA)対応
        - Robots.txt 無視
        - リンク自動修正
        """,
        "input_label": "URLを入力してください",
        "input_ph": "https://example.com",
        "btn_convert": "変換・ダウンロード準備",
        "error_no_url": "URLを入力してください。",
        "spinner": "ページを解析・変換中... (動的サイトの場合は時間がかかります)",
        "success": "変換完了！",
        "preview": "プレビュー",
        "download_section": "ダウンロード",
        "download_btn": "HTMLファイルをダウンロード",
        "info": "ダウンロードしたファイルはオフラインでも表示可能です。",
        "settings": "設定",
        "ui_lang": "アプリの表示言語",
        "content_lang": "Webページの言語設定 (Accept-Language)",
        "content_lang_help": "多言語対応サイト(Wikipediaなど)で、どの言語のページを取得するかを指定します。"
    },
    "English": {
        "page_title": "Single-File Converter",
        "app_title": "🌐 Webpage Single-File Converter",
        "desc": """
        Downloads a webpage and converts it into a **single HTML file** with embedded images and CSS.
        - Supports Dynamic Sites (SPA)
        - Ignores Robots.txt
        - Auto-fixes Links
        """,
        "input_label": "Enter URL",
        "input_ph": "https://example.com",
        "btn_convert": "Start Conversion",
        "error_no_url": "Please enter a URL.",
        "spinner": "Processing... (This may take time for dynamic sites)",
        "success": "Conversion Complete!",
        "preview": "Preview",
        "download_section": "Download",
        "download_btn": "Download HTML",
        "info": "The downloaded file can be viewed offline.",
        "settings": "Settings",
        "ui_lang": "App UI Language",
        "content_lang": "Content Language (Accept-Language)",
        "content_lang_help": "Determines which language version to fetch for multi-lingual sites."
    }
}

# --- 言語設定 (サイドバー) ---
st.set_page_config(page_title="Webpage Saver", layout="wide")

with st.sidebar:
    st.header("⚙️ Settings")
    
    # UI言語の選択
    selected_ui_lang = st.selectbox(
        "Language / 言語",
        ["Japanese", "English"],
        index=0
    )
    
    # コンテンツ取得言語の選択
    st.markdown("---")
    st.subheader("Target Content")
    content_lang_option = st.selectbox(
        TRANSLATIONS[selected_ui_lang]["content_lang"],
        ["Japanese (ja-JP)", "English (en-US)", "Chinese (zh-CN)", "Korean (ko-KR)"],
        index=0,
        help=TRANSLATIONS[selected_ui_lang]["content_lang_help"]
    )
    
    # ロケールコードの抽出 (例: "Japanese (ja-JP)" -> "ja-JP")
    target_lang_code = content_lang_option.split("(")[-1].replace(")", "")

# テキスト辞書の取得
t = TRANSLATIONS[selected_ui_lang]

# --- メインコンテンツ ---
st.title(t["app_title"])
st.markdown(t["desc"])

url = st.text_input(t["input_label"], placeholder=t["input_ph"])

if st.button(t["btn_convert"]):
    if not url:
        st.error(t["error_no_url"])
    else:
        with st.spinner(t["spinner"]):
            try:
                # 選択されたコンテンツ言語コードを渡す
                html_content = bundle_html(url, lang_code=target_lang_code)
                
                st.success(t["success"])
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader(t["preview"])
                    st.components.v1.html(html_content, height=600, scrolling=True)

                with col2:
                    st.subheader(t["download_section"])
                    st.download_button(
                        label=t["download_btn"],
                        data=html_content,
                        file_name="downloaded_page.html",
                        mime="text/html"
                    )
                    st.info(t["info"])

            except Exception as e:
                st.error(f"Error: {e}")
