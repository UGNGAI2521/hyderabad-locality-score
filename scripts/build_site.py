"""Wrap src/page.html (written for the claude.ai artifact viewer, which adds its own <html>/<head>/<body>)
into a standalone index.html for any static host such as GitHub Pages. Run after every edit to src/page.html."""
page = open("src/page.html", encoding="utf-8").read()
split = page.index('<header class="top">')  # title, meta, links and styles go in <head>; the rest is the body
head, body = page[:split], page[split:]
reset = (":root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
         "body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}")
html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f"<style>{reset}</style>\n{head.strip()}\n</head>\n<body>\n{body.strip()}\n</body>\n</html>\n")
assert html.count("<title>") == 1 and "<header" in html
open("index.html", "w", encoding="utf-8").write(html)
print("index.html", len(html) // 1024, "KB")

from build_pages import main as build_pages  # one page per locality, the locality index and sitemap.xml
build_pages()
