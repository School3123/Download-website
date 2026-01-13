import base64
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def fetch_resource_as_base64(url, session=None):
    """リソースをダウンロードしてBase64文字列として返す"""
    try:
        if session:
            response = session.get(url, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        response.raise_for_status()
        encoded = base64.b64encode(response.content).decode('utf-8')
        mime_type = response.headers.get('Content-Type', '').split(';')[0]
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def bundle_html(url):
    """URLのページをダウンロードし、リソースを埋め込んだ単一HTMLを返す"""
    
    # Robots.txtはPlaywright/Requestsではデフォルトでチェックされないため、
    # 明示的にUser-Agentを一般的なブラウザに設定して無視・回避します。
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    with sync_playwright() as p:
        # ブラウザ起動 (ヘッドレスモード)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()

        print(f"Accessing {url}...")
        # ページにアクセスし、ネットワーク通信が落ち着くまで待機（動的サイト対応）
        page.goto(url, wait_until="networkidle")
        
        # DOMが完全にレンダリングされた状態のHTMLを取得
        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, "html.parser")
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})

    # 1. CSS (<link rel="stylesheet">) を <style> に変換して埋め込む
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href:
            abs_url = urljoin(url, href)
            try:
                res = session.get(abs_url, timeout=10)
                if res.status_code == 200:
                    new_style = soup.new_tag("style")
                    new_style.string = res.text
                    link.replace_with(new_style)
            except Exception as e:
                print(f"Failed to inline CSS {abs_url}: {e}")

    # 2. 画像 (<img>) を Base64 に変換して埋め込む
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            abs_url = urljoin(url, src)
            base64_data = fetch_resource_as_base64(abs_url, session)
            if base64_data:
                img['src'] = base64_data
                # srcsetがある場合は削除（表示崩れ防止）
                if img.has_attr('srcset'):
                    del img['srcset']

    # 3. JavaScript (<script src="...">) を埋め込む
    # 注意: 複雑なJSは埋め込むと動かない場合がありますが、基本構造は維持します
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            abs_url = urljoin(url, src)
            try:
                res = session.get(abs_url, timeout=10)
                if res.status_code == 200:
                    script.string = res.text
                    del script['src']
            except Exception:
                pass

    # 4. リンク (<a>) を絶対パスに書き換え
    # ローカルの単一ファイルからクリックしても正しくWebへ遷移するようにする
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and not href.startswith("#") and not href.startswith("javascript:"):
            a['href'] = urljoin(url, href)
            a['target'] = "_blank" # 新しいタブで開くようにする

    return str(soup)
