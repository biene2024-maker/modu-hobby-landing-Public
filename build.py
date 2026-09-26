"""원본 *.src.html 들에서 두 가지 게시본을 만든다.

    python build.py

  사업계획서 v2.0 부터 랜딩은 네 장이다 (3-Pillar).

    home.src.html      → docs/index.html          홈 · 3분기 선택
    index.src.html     → docs/teams/index.html    FOR TEAMS (담당자용, 기존 페이지)
    active50.src.html  → docs/50plus/index.html   어른의 취미생활 (사업부문 50+ Active Life)
    me.src.html        → docs/me/index.html       FOR ME (개인)

  아티팩트용 조각(HTML 스켈레톤 없음, 이미지는 data URI)도 같이 만든다.

    index.html   ← index.src.html    (기존 아티팩트 URL 이 이 파일을 쓴다. 이름 바꾸지 말 것)
    home.html    ← home.src.html
    active50.html, me.html

  docs/survey/ 와 docs/survey-50plus/ 는 이 스크립트가 만들지 않는다. 직접 편집한다.
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

# (원본, 아티팩트 출력, docs 하위 경로, og:description)
PAGES = [
    ("home.src.html", "home.html", "",
     "반복된 일상에 지친 어른들을 위한 Lifestyle Platform. 갑자기 생긴 시간, 우리 팀 활동, 어른의 취미생활 — 오늘 할 수 있는 경험을 찾아드립니다."),
    ("index.src.html", "index.html", "teams",
     "인원·지역·예산만 보내면 24시간 안에 활동·식당·견적을 묶은 제안 세 가지가 옵니다. "
     "기업 팀·동호회 활동을 담당자 대신 찾고, 예약하고, 증빙하고, 효과까지 보고합니다."),
    ("active50.src.html", "active50.html", "50plus",
     "어른의 취미생활 — 시간이 조금 더 내 것이 된 지금. 50+의 새로운 일상을 위한 취미·모임·웰니스·여행."),
    ("me.src.html", "me.html", "me",
     "오늘 갑자기 3시간이 비었다면. 지금 내 주변에서 할 수 있는 것을 찾아드립니다."),
]

HEAD_TMPL = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="모두의 취미">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{imgprefix}img/cooking-class.webp">
<meta name="theme-color" content="#C24A14">
<style>[hidden]{{display:none!important}}</style>
"""

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

cache: dict[str, str] = {}


def uri(name: str) -> str:
    if name not in cache:
        cache[name] = "data:image/webp;base64," + base64.b64encode((IMG / f"{name}.webp").read_bytes()).decode()
    return cache[name]


DOCS.mkdir(exist_ok=True)

for src_name, artifact_name, sub, desc in PAGES:
    src_path = HERE / src_name
    if not src_path.exists():
        print(f"!  {src_name} 없음 — 건너뜀")
        continue
    src = src_path.read_text(encoding="utf-8")

    # ── 1. 아티팩트용: data URI 삽입 ─────────────────────────
    artifact = PLACEHOLDER.sub(lambda m: uri(m.group(1)), src)
    (HERE / artifact_name).write_text(artifact, encoding="utf-8")
    print(f"{artifact_name:<16} {len(artifact.encode()) / 1024:>6.0f} KB (artifact)")

    # ── 2. GitHub Pages용: 완전한 문서 + 상대경로 이미지 ─────
    # 하위 폴더 페이지는 img 가 한 단계 위에 있다
    prefix = "../" if sub else ""
    # <title> 은 원본 맨 위에 있으므로 head 안으로 옮긴다
    title_m = re.search(r"<title>.*?</title>\n?", src)
    title = title_m.group(0) if title_m else ""
    body = src.replace(title, "", 1) if title else src
    # 원본은 <title> 뒤에 <link>·<style> 이 오고 그 다음 <nav> 부터 본문이다
    split = body.index("<nav")
    head_part, main_part = body[:split], body[split:]
    pages = (
        HEAD_TMPL.format(desc=desc, imgprefix=prefix) + title + head_part + "</head>\n<body>\n"
        + PLACEHOLDER.sub(lambda m: f"{prefix}img/{m.group(1)}.webp", main_part)
        + "</body>\n</html>\n"
    )
    out_dir = DOCS / sub if sub else DOCS
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(pages, encoding="utf-8")
    rel = f"docs/{sub}/index.html" if sub else "docs/index.html"
    print(f"{rel:<28} {len(pages.encode()) / 1024:>6.0f} KB (GitHub Pages)")

# OneDrive 가 폴더를 잠그는 일이 있어 rmtree 대신 파일 단위로 덮어쓴다
(DOCS / "img").mkdir(exist_ok=True)
for f in IMG.glob("*.webp"):
    shutil.copyfile(f, DOCS / "img" / f.name)
(DOCS / ".nojekyll").write_text("")
print(f"docs/img/ {len(list((DOCS / 'img').iterdir()))} files")
