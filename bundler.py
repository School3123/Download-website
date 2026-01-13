import base64
import requests
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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
        # print(f"Error fetching {url}: {e}") # ログが多すぎる場合はコメントアウト
        return None

def bundle_html(url, lang_code="ja-JP"):
    """
    URLのページをダウンロードし、リソースを埋め込んだ単一HTMLを返す
    lang_code: 'ja-JP', 'en-US' などのロケールコード
    """
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    content = ""

    print(f"Starting process for {url} with locale {lang_code}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # コンテキスト作成時に言語設定(locale)とタイムゾーン、HTTPヘッダを指定
        context = browser.new_context(
            user_agent=user_agent,
            locale=lang_code,
            timezone_id="Asia/Tokyo" if "ja" in lang_code else "UTC",
            extra_http_headers={'Accept-Language': lang_code}
        )
        page = context.new_page()

        try:
            # タイムアウト対策済み設定
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 動的コンテンツ待機
            page.wait_for_timeout(3000) 
            
            # スクロールして遅延読み込みトリガー
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

        except PlaywrightTimeoutError:
            print("Timeout occurred! Loading whatever content is available...")
        except Exception as e:
            print(f"An error occurred during page load: {e}")
        
        content = page.content()
        browser.close()

    if not content:
        raise Exception("Failed to retrieve HTML content.")

    soup = BeautifulSoup(content, "html.parser")
    session = requests.Session()
    # Requests側にも言語設定を反映
    session.headers.update({
        'User-Agent': user_agent,
        'Accept-Language': lang_code
    })

    # 1. CSS
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
            except Exception:
                pass

    # 2. 画像
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src and img.get("data-src"):
            src = img.get("data-src")
            
        if src:
            abs_url = urljoin(url, src)
            base64_data = fetch_resource_as_base64(abs_url, session)
            if base64_data:
                img['src'] = base64_data
                if img.has_attr('srcset'): del img['srcset']
                if img.has_attr('loading'): del img['loading']

    # 3. JS
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

    # 4. リンク修正
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and not href.startswith("#") and not href.startswith("javascript:"):
            a['href'] = urljoin(url, href)
            a['target'] = "_blank"

    return str(soup)
