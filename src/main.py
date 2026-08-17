import json
import os
import re
from pathlib import Path

import requests
from google import genai
from playwright.sync_api import sync_playwright

LIST_URL = os.getenv("X_LIST_URL", "https://x.com/i/lists/1305205166652694534")
STATE_FILE = Path("state.json")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"seen": []}


def save_state(state):
    state["seen"] = state["seen"][-1000:]
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_posts():
    auth = os.environ["X_AUTH_TOKEN"]
    ct0 = os.environ["X_CT0"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        context.add_cookies([
            {"name": "auth_token", "value": auth, "domain": ".x.com", "path": "/", "httpOnly": True, "secure": True},
            {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/", "httpOnly": False, "secure": True},
        ])
        page = context.new_page()
        page.goto(LIST_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        for _ in range(3):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(1500)

        posts = []
        for article in page.locator('article[data-testid="tweet"]').all():
            try:
                link = article.locator('a[href*="/status/"]').first.get_attribute("href")
                text = article.locator('[data-testid="tweetText"]').inner_text(timeout=2000)
                author = article.locator('[data-testid="User-Name"]').inner_text(timeout=2000)
                if not link or not text.strip():
                    continue
                match = re.search(r"/status/(\d+)", link)
                if not match:
                    continue
                posts.append({"id": match.group(1), "url": "https://x.com" + link if link.startswith("/") else link, "author": author, "text": text.strip()})
            except Exception:
                continue
        browser.close()
        return posts


def make_post(item):
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""Você é editor de uma página brasileira de notícias de futebol no X.

Transforme a notícia abaixo em um post curto, natural e original em português do Brasil.

Regras:
- Preserve exatamente nomes, clubes, valores, números e fatos.
- Não invente informações.
- Não diga que a informação é confirmada se a fonte não diz isso.
- Seja direto e jornalístico.
- Use emojis com moderação.
- Não use hashtags.
- Máximo de 280 caracteres.
- Não copie a estrutura palavra por palavra.

Fonte: {item['author']}
Texto: {item['text']}
"""
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text.strip()


def send_telegram(text, item):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    message = f"📰 NOVA NOTÍCIA\n\n{text}\n\n🔗 Fonte: {item['url']}"
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": message}, timeout=30)
    r.raise_for_status()


def main():
    state = load_state()
    posts = collect_posts()
    new_posts = [p for p in posts if p["id"] not in state["seen"]]
    # Process oldest first when several new posts are found.
    new_posts = list(reversed(new_posts))
    for item in new_posts:
        try:
            generated = make_post(item)
            send_telegram(generated, item)
            state["seen"].append(item["id"])
        except Exception as exc:
            print(f"Erro ao processar {item['id']}: {exc}")
    save_state(state)


if __name__ == "__main__":
    main()
