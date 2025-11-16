#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_index.py
- posts/*.html からメタ情報を抽出し、build/index_template.html を使って index.html を生成します。
- 抜粋は投稿本文（<article class="post"> または <main> の中身）から取り、HTML を除去して生テキストで出力します。
- タイトル・抜粋は HTML エスケープして index に埋め込みます。
"""

import re
import sys
import glob
import os
from datetime import datetime
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
POSTS_DIR = os.path.join(REPO_ROOT, "posts")
TEMPLATE_PATH = os.path.join(HERE, "index_template.html")
OUTPUT_PATH = os.path.join(REPO_ROOT, "index.html")

# 設定（必要ならここを編集）
SITE_TITLE = "日記ブログ — katurin"
SITE_DESCRIPTION = "日々の記録を綴るシンプルな日記ブログ"
SITE_SUB = "katurin.github.io"
SITE_OWNER = "katurin"

# --- ユーティリティ ---------------------------------------------------------
def strip_tags(html: str) -> str:
    """script/style を除去してからタグを簡易的に除去。エスケープ解除してトリムして返す。"""
    if html is None:
        return ""
    # remove script/style blocks
    text = re.sub(r'(?is)<script.*?>.*?</script>', '', html)
    text = re.sub(r'(?is)<style.*?>.*?</style>', '', text)
    # remove comments
    text = re.sub(r'(?s)<!--.*?-->', '', text)
    # remove tags
    text = re.sub(r'(?s)<[^>]+>', '', text)
    # unescape HTML entities
    text = _html.unescape(text)
    # normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_meta(html: str, filename: str):
    """投稿 HTML から title, date, excerpt, url, sortkey を抽出して返す dict."""
    # Title from <title> or first h1/h2
    title = None
    m = re.search(r'<title>(.*?)</title>', html, re.I|re.S)
    if m:
        title = m.group(1).strip()

    if not title:
        m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.I|re.S)
        if not m:
            m = re.search(r'<h2[^>]*>(.*?)</h2>', html, re.I|re.S)
        if m:
            title = strip_tags(m.group(1))
    if not title:
        title = filename

    # Date from <time class="post-date" datetime="..."> or filename YYYYMMDD
    date = None
    m = re.search(r'<time[^>]*class=["\']?post-date["\']?[^>]*datetime=["\']([^"\']+)["\']', html, re.I)
    if m:
        date = m.group(1)
    else:
        # try other time patterns: datetime attr without class, or <time datetime="...">
        m2 = re.search(r'<time[^>]*datetime=["\']([^"\']+)["\']', html, re.I)
        if m2:
            date = m2.group(1)

    if not date:
        m = re.search(r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})', filename)
        if m:
            date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        else:
            date = "1970-01-01"

    # Extract article content: prefer <article class="post">, then <main>, then <body>, fallback full html
    article_html = None
    m = re.search(r'(<article\b[^>]*class=["\']?[^"\'>]*post[^"\'>]*["\']?[^>]*>.*?</article>)', html, re.I|re.S)
    if m:
        article_html = m.group(1)
    else:
        m2 = re.search(r'(<main\b[^>]*>.*?</main>)', html, re.I|re.S)
        if m2:
            inner = m2.group(1)
            m3 = re.search(r'(<article\b.*?>.*?</article>)', inner, re.I|re.S)
            article_html = m3.group(1) if m3 else inner
        else:
            m4 = re.search(r'(<body\b[^>]*>.*?</body>)', html, re.I|re.S)
            article_html = m4.group(1) if m4 else html

    body_text = strip_tags(article_html or html)
    # excerpt length (chars). 日本語を含むので文字数ベースで切る
    max_len = 200
    excerpt = (body_text[:max_len] + "…") if len(body_text) > max_len else body_text

    # sortkey: ISO date if possible, otherwise date string
    try:
        sortkey = datetime.fromisoformat(date).isoformat()
    except Exception:
        sortkey = date

    return {
        "title": title,
        "date": date,
        "excerpt": excerpt,
        "url": f"posts/{filename}",
        "sortkey": sortkey
    }

# --- メイン処理 -------------------------------------------------------------
def build_index():
    # find post files
    files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))
    posts_meta = []

    for fpath in files:
        fname = os.path.basename(fpath)
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                html = fh.read()
        except Exception as e:
            print(f"Warning: failed to read {fpath}: {e}", file=sys.stderr)
            continue

        meta = extract_meta(html, fname)
        posts_meta.append(meta)

    # sort posts by sortkey desc (newest first)
    posts_meta.sort(key=lambda x: x.get("sortkey", ""), reverse=True)

    # create post blocks and recent links (escape content)
    post_blocks = []
    recent_links = []
    for meta in posts_meta:
        safe_title = _html.escape(meta["title"])
        safe_excerpt = _html.escape(meta["excerpt"])
        block = (
            f'    <article class="post" data-date="{meta["date"]}">\n'
            f'      <time class="post-date" datetime="{meta["date"]}">{meta["date"]}</time>\n'
            f'      <h2 class="post-title"><a href="{meta["url"]}">{safe_title}</a></h2>\n'
            f'      <div class="post-body"><p>{safe_excerpt}</p></div>\n'
            f'    </article>\n'
        )
        post_blocks.append(block)
        recent_links.append(f'          <li><a href="{meta["url"]}">{safe_title} — {meta["date"]}</a></li>')

    posts_block_html = "\n".join(post_blocks) if post_blocks else "    <!-- no posts -->"
    recent_links_html = "\n".join(recent_links) if recent_links else "          <!-- no recent posts -->"

    # load template
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as tf:
            template = tf.read()
    except Exception as e:
        print(f"ERROR: cannot read template at {TEMPLATE_PATH}: {e}", file=sys.stderr)
        return 1

    # replace placeholders (simple templating)
    out_html = template
    out_html = out_html.replace("{{ posts_block }}", posts_block_html)
    out_html = out_html.replace("{{ recent_links }}", recent_links_html)
    out_html = out_html.replace("{{ site_title }}", _html.escape(SITE_TITLE))
    out_html = out_html.replace("{{ site_description }}", _html.escape(SITE_DESCRIPTION))
    out_html = out_html.replace("{{ site_sub }}", _html.escape(SITE_SUB))
    out_html = out_html.replace("{{ site_owner }}", _html.escape(SITE_OWNER))

    # write output
    try:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as of:
            of.write(out_html)
        print(f"Wrote {OUTPUT_PATH}")
    except Exception as e:
        print(f"ERROR: failed to write {OUTPUT_PATH}: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(build_index())

    # 既存の build_index() を互換名 build() で呼べるようにする（serve.py 互換）
def build():
    return build_index()