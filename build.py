"""index.src.html 하나에서 두 가지 게시본을 만든다.

    python build.py

  index.html       Claude 아티팩트용 — 조각(HTML 스켈레톤 없음), 이미지는 data URI로 삽입
  docs/index.html  GitHub Pages용 — 완전한 문서, 이미지는 docs/img/*.webp 를 상대경로로 참조
"""
import base64
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).parent
IMG = HERE / "img"
DOCS = HERE / "docs"
PLACEHOLDER = re.compile(r"__IMG:([\w-]+)__")

# 시안 등 다른 파일: `python build.py 시안.html` → 시안.built.html (data URI만 삽입)
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        f = pathlib.Path(arg)
        out = f.with_name(f.stem + ".built.html")
        cache_: dict[str, str] = {}
        def _uri(name: str) -> str:
            if name not in cache_:
                cache_[name] = "data:image/webp;base64," + base64.b64encode((IMG / f"{name}.webp").read_bytes()).decode()
            return cache_[name]
        out.write_text(PLACEHOLDER.sub(lambda m: _uri(m.group(1)), f.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"{out.name} {out.stat().st_size / 1024:.0f} KB")
    sys.exit(0)

src = (HERE / "index.src.html").read_text(encoding="utf-8")

# ── 1. 아티팩트용: data URI 삽입 ─────────────────────────────
cache: dict[str, str] = {}


def uri(name: str) -> str:
    if name not in cache:
        data = (IMG / f"{name}.webp").read_bytes()
        cache[name] = "data:image/webp;base64," + base64.b64encode(data).decode()
    return cache[name]


artifact = PLACEHOLDER.sub(lambda m: uri(m.group(1)), src)
(HERE / "index.html").write_text(artifact, encoding="utf-8")
print(f"index.html       {len(artifact.encode()) / 1024:.0f} KB (artifact)")

# ── 2. GitHub Pages용: 완전한 문서 + 상대경로 이미지 ─────────
HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="인원·지역·예산만 보내면 24시간 안에 활동·식당·견적을 묶은 제안 세 가지가 옵니다. 기업 팀·동호회 활동을 담당자 대신 찾고, 예약하고, 증빙하고, 효과까지 보고합니다.">
<meta property="og:type" content="website">
<meta property="og:title" content="모두의 취미 — 이번 달, 우리 뭐 하지?">
<meta property="og:description" content="조건만 보내면 24시간 안에 제안 세 가지. 활동부터 식당, 증빙, 효과 보고서까지 담당자 대신 합니다.">
<meta property="og:image" content="img/cooking-class.webp">
<meta name="theme-color" content="#C24A14">
<style>[hidden]{display:none!important}</style>
"""
# <title> 은 원본 맨 위에 있으므로 head 안으로 옮긴다
title_m = re.search(r"<title>.*?</title>\n?", src)
title = title_m.group(0) if title_m else ""
body = src.replace(title, "", 1) if title else src
# 원본은 <title> 뒤에 <link>·<style> 이 오고 그 다음 <nav> 부터 본문이다
split = body.index("<nav")
head_part, main_part = body[:split], body[split:]
pages = (
    HEAD + title + head_part + "</head>\n<body>\n"
    + PLACEHOLDER.sub(lambda m: f"img/{m.group(1)}.webp", main_part)
    + "</body>\n</html>\n"
)
DOCS.mkdir(exist_ok=True)
(DOCS / "index.html").write_text(pages, encoding="utf-8")
# OneDrive 가 폴더를 잠그는 일이 있어 rmtree 대신 파일 단위로 덮어쓴다
(DOCS / "img").mkdir(exist_ok=True)
for f in IMG.glob("*.webp"):
    shutil.copyfile(f, DOCS / "img" / f.name)
(DOCS / ".nojekyll").write_text("")
print(f"docs/index.html  {len(pages.encode()) / 1024:.0f} KB (GitHub Pages) + docs/img/ {len(list((DOCS / 'img').iterdir()))} files")
