import streamlit as st
from bundler import bundle_html
import time

st.set_page_config(page_title="SingleFile Downloader", layout="wide")

st.title("🌐 Webpage Single-File Converter")
st.markdown("""
指定したURLのWebページをダウンロードし、画像やCSSを埋め込んだ**単一のHTMLファイル**に変換します。
- 動的サイト(SPA)対応
- Robots.txt 無視
- リンクの自動修正
""")

url = st.text_input("URLを入力してください", placeholder="https://example.com")

if st.button("変換・ダウンロード準備"):
    if not url:
        st.error("URLを入力してください。")
    else:
        with st.spinner("ページを解析・変換中... (動的サイトの場合は時間がかかります)"):
            try:
                # 変換処理実行
                html_content = bundle_html(url)
                
                # 成功メッセージ
                st.success("変換完了！")
                
                # プレビューとダウンロードボタンをカラムで分ける
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("プレビュー")
                    # iframeでプレビューを表示
                    st.components.v1.html(html_content, height=600, scrolling=True)

                with col2:
                    st.subheader("ダウンロード")
                    st.download_button(
                        label="HTMLファイルをダウンロード",
                        data=html_content,
                        file_name="downloaded_page.html",
                        mime="text/html"
                    )
                    
                    st.info("ダウンロードしたファイルはオフラインでも（ある程度）正しく表示されます。")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
