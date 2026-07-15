#!/usr/bin/env python3
"""沉星尽春 - 人设生成脚本

输入人设信息文本，自动生成人设文件夹与HTML文件，
并更新人设列表页与各详情页的前后翻页链接。

用法：
  python gen_char.py                              # 交互模式，逐行输入
  python gen_char.py --file input.txt             # 从文本文件读取
  python gen_char.py "姓名: xxx\n字: xxx\n..."    # 命令行传入文本
"""

import os
import re
import sys

# ── 路径配置 ───────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
CHARS_DIR = os.path.join(ROOT, 'chars')
INDEX_PATH = os.path.join(CHARS_DIR, 'index.html')
SITEMAP_PATH = os.path.join(ROOT, 'sitemap.xml')
README_PATH = os.path.join(ROOT, 'README.md')
BASE_URL = 'https://cxjc.whitemoon319.xyz'

# ── 拼音（可选依赖） ────────────────────────────────────
try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False


def to_slug(name: str) -> str:
    """中文名 → 拼音 slug，无 pypinyin 时手动输入"""
    if HAS_PYPINYIN:
        s = ''.join(lazy_pinyin(name, style=Style.NORMAL, strict=False))
        return re.sub(r'[^a-z0-9]', '', s.lower())
    print(f'[!] 未安装 pypinyin，无法自动转换 "{name}"')
    return input('请输入目录名（拼音，如 fanwenqing）: ').strip().lower()


# ── 字段解析 ───────────────────────────────────────────
FIELD_KEYS = ['姓名', '字', '年龄', '所属势力', '职业',
              '状态', '关键词', '性格', '经历', '外貌', '衣着', '备注']


def parse_fields(text: str) -> dict:
    """解析「字段名: 内容」格式文本，支持多行内容"""
    text = text.strip().lstrip('\ufeff')  # 去除 BOM
    fields = {}
    pattern = r'(?:^|\n)\s*(' + '|'.join(FIELD_KEYS) + r')\s*[:：]\s*'
    parts = re.split(pattern, text, maxsplit=0)
    for i in range(1, len(parts), 2):
        key = parts[i]
        val = parts[i + 1].strip() if i + 1 < len(parts) else ''
        fields[key] = val
    return fields


def interact_input() -> str:
    """交互模式逐字段输入，两次回车结束"""
    print('请输入人设信息（每行一个字段，格式：字段名: 内容）')
    print('多行字段（性格/经历/外貌/衣着/备注）输入完后空行结束')
    print('全部输入完成后输入 END 或 Ctrl+C 结束\n')
    lines = []
    last_key = None
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip().upper() == 'END':
            break
        # 检查是否新字段开始
        stripped = line.strip()
        is_new_field = False
        for k in FIELD_KEYS:
            if re.match(rf'^{k}\s*[:：]', stripped):
                is_new_field = True
                break
        if is_new_field:
            last_key = re.split(r'[:：]', stripped, maxsplit=1)[0].strip()
        elif stripped == '' and last_key in ('性格', '经历', '外貌', '衣着', '备注'):
            # 多行字段空行表示该字段结束
            last_key = None
        lines.append(line)
    return '\n'.join(lines)


# ── HTML 片段 ──────────────────────────────────────────

def nav_html() -> str:
    return ('<nav class="site-nav"><div class="site-nav-inner">'
            '<a class="site-logo" href="../../index.html">'
            '<img src="../../resource/img/logo.webp" alt="沉星尽春" />'
            '<span class="site-logo-text">沉星尽春</span></a>'
            '<ul class="nav-links">'
            '<li><a class="nav-link" href="../../world/">卷首</a></li>'
            '<li><a class="nav-link" href="../../preset/">固设</a></li>'
            '<li><a class="nav-link active" href="../">人设</a></li>'
            '<li><a class="nav-link" href="../../forces/">势力</a></li>'
            '<li><a class="nav-link" href="../../timeline/">年表</a></li>'
            '<li><a class="nav-link" href="../../index.html#about">跋</a></li>'
            '</ul></div></nav>')


def gen_detail_html(fields: dict, slug: str,
                    prev_info: tuple | None,
                    next_info: tuple | None) -> str:
    """生成人设详情页完整 HTML"""
    name = fields.get('姓名', '')
    zi = fields.get('字', '')
    age = fields.get('年龄', '')
    faction = fields.get('所属势力', '')
    occupation = fields.get('职业', '')
    status = fields.get('状态', '')
    keywords = fields.get('关键词', '')
    personality = fields.get('性格', '')
    experience = fields.get('经历', '')
    appearance = fields.get('外貌', '')
    clothing = fields.get('衣着', '')
    notes = fields.get('备注', '')

    mark = name[0] if name else '?'
    alias_parts = []
    if zi:
        alias_parts.append(f'字{zi}')
    if age:
        alias_parts.append(f'年{age}')
    alias = ' · '.join(alias_parts) if alias_parts else '身份待补'

    facts = []
    if faction:
        facts.append(f'<span>{faction}</span>')
    if occupation:
        facts.append(f'<span>{occupation}</span>')
    if status:
        facts.append(f'<span>{status}</span>')
    for kw in [k.strip() for k in keywords.replace('，', ',').split(',') if k.strip()]:
        facts.append(f'<span>{kw}</span>')
    facts_html = ''.join(facts)

    lead = f'{status} · {occupation}' if status and occupation else (status or occupation or keywords or name)

    # 内容段落：按是否需要列表渲染
    def content_section(heading: str, text: str, use_list: bool = False, delay: int = 0, wide: bool = False):
        cls = 'character-section reveal'
        if wide:
            cls += ' wide'
        d = f' data-delay="{delay}"' if delay else ''
        if use_list and text.strip():
            items = '\n'.join(f'<li>{line.strip()}</li>'
                              for line in text.strip().splitlines() if line.strip())
            body = f'<ul>{items}</ul>'
        else:
            body = f'<p>{text.strip()}</p>' if text.strip() else '<p>待补。</p>'
        return f'<section class="{cls}"{d}><h2>{heading}</h2>{body}</section>'

    sections = []
    sections.append(content_section('外貌', appearance, delay=0))
    sections.append(content_section('衣着', clothing, use_list=True, delay=1))
    sections.append(content_section('经历', experience, delay=2, wide=True))
    sections.append(content_section('性格', personality, delay=0))
    sections.append(content_section('备注', notes, delay=1))

    # 翻页
    pagination = '<div class="character-pagination">'
    if prev_info:
        pagination += f'<a class="btn btn-ghost" href="../{prev_info[0]}/">← {prev_info[1]}</a>'
    else:
        pagination += '<a class="btn btn-ghost" href="../">← 人设一览</a>'
    if next_info:
        pagination += f'<a class="btn btn-primary" href="../{next_info[0]}/">{next_info[1]} →</a>'
    else:
        pagination += '<a class="btn btn-primary" href="../">人设一览 →</a>'
    pagination += '</div>'

    esc_name = name
    desc = f'{name}，{alias}' if alias else name

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc_name}｜人物卷宗｜沉星尽春</title>
  <meta name="description" content="沉星尽春人物卷宗：{desc}。" />
  <link rel="canonical" href="{BASE_URL}/chars/{slug}/" />
  <link rel="icon" type="image/webp" href="../../resource/img/favicon.webp" />
  <link rel="stylesheet" href="../../resource/css/style.css" />
  <script defer src="../../resource/js/site-nav.js"></script>
</head>
<body>
  {nav_html()}

  <main class="character-page" style="--cc: var(--cinnabar);">
    <a class="character-back" href="../">← 返回人设一览</a>
    <section class="character-hero reveal in">
      <div class="character-mark">{mark}</div>
      <div><p class="character-kicker">人物卷宗</p><h1 class="character-heading">{esc_name}</h1><p class="character-alias">{alias}</p><p class="character-lead">{lead}</p><div class="character-facts">{facts_html}</div></div>
    </section>
    <div class="character-content">
      {'\n      '.join(sections)}
    </div>
    {pagination}
  </main>
  <footer class="site-footer"><img class="footer-seal" src="../../resource/img/favicon.webp" alt="" /><h3>沉星尽春</h3><p>人物卷宗 · {esc_name}</p></footer>
<script>const io=new IntersectionObserver(es=>es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add('in');io.unobserve(e.target)}}}}),{{threshold:.12}});document.querySelectorAll('.reveal:not(.in)').forEach(e=>io.observe(e));</script>
<script>(function(){{var ref=document.referrer;if(!ref)return;var m=ref.match(/forces\\/(officials|royal)\\//);if(!m)return;var url='../../forces/'+m[1]+'/',text='\u2190 \u8FD4\u56DE'+(m[1]==='officials'?'\u5927\u666F\u5B98\u5458\u540D\u5355':'\u7687\u5BB6\u7389\u7252');var el=document.querySelector('.character-back');if(el){{el.href=url;el.textContent=text;}}var pa=document.querySelector('.character-pagination .btn-ghost');if(pa&&pa.textContent.indexOf('\u4EBA\u8BBE\u4E00\u89C8')>=0){{pa.href=url;pa.textContent=text;}}}})();</script>
</body>
</html>'''


def gen_card_html(slug: str, fields: dict, delay: int) -> str:
    """生成人设列表页卡片 HTML"""
    name = fields.get('姓名', '')
    faction = fields.get('所属势力', '')
    status = fields.get('状态', '')
    mark = name[0] if name else '?'
    quote = fields.get('性格', '')
    if quote:
        quote = quote.strip().split('。')[0] + '。' if '。' in quote else quote[:30]

    return f'''      <a class="char-card reveal" data-delay="{delay}" href="{slug}/" style="--cc: var(--cinnabar);">
        <div class="char-portrait">{mark}</div>
        <div class="char-body">
          <h3 class="char-name">{name}</h3>
          <p class="char-title">外貌 · 衣着 · 经历 · 性格 · 备注</p>
          <p class="char-quote">{quote}</p>
          <div class="char-meta">
            <span class="kingdom-tag">{faction}</span>
            <span>{status}</span>
          </div>
        </div>
      </a>'''


# ── 列表页操作 ─────────────────────────────────────────

def read_index() -> str:
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def write_index(html: str):
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(html)


def get_char_slugs(html: str) -> list:
    """从列表页提取真实人物 slug（排除 template）"""
    slugs = []
    for m in re.finditer(r'href="([^"]+?)/"\s+style="--cc:', html):
        slug = m.group(1)
        if slug != 'template':
            slugs.append(slug)
    return slugs


def add_card_to_index(slug: str, fields: dict):
    """在列表页模板卡片之前插入新人卡片，并更新引导语"""
    html = read_index()
    existing = get_char_slugs(html)
    if slug in existing:
        print(f'[!] "{slug}" 已存在于列表页，跳过插入')
        return

    card = gen_card_html(slug, fields, delay=len(existing) + 1)

    # 在模板卡片之前插入：匹配 href="template/" 的整行卡片
    pattern = re.compile(
        r'(      <a class="char-card reveal" data-delay=")\d+(" href="template/")',
    )
    match = pattern.search(html)
    if match:
        new_delay = len(existing) + 2
        html = html[:match.start()] + card + '\n\n' + match.group(1) + str(new_delay) + match.group(2) + html[match.end():]
    else:
        # 没有模板卡片，插入到 .chars 容器末尾
        html = html.replace('\n    </div>\n\n    <p style="text-align:center',
                            '\n' + card + '\n    </div>\n\n    <p style="text-align:center')

    # 更新引导语
    if len(existing) == 0:
        html = html.replace('人物卷宗尚未录入，待正式设定后逐一补全。',
                            '朱砂所点，群像登场。点击查看各人物详情卷宗。')

    write_index(html)
    print(f'[✓] 已更新列表页，插入 {slug}')


def remove_card_from_index(slug: str):
    """从列表页移除指定卡片，若无人设则恢复默认引导语"""
    html = read_index()
    pattern = re.compile(
        r'\n      <a class="char-card reveal" data-delay="\d+" href="'
        + re.escape(slug) + r'/" style="--cc: var\(--cinnabar\);">.*?</a>\n',
        re.DOTALL
    )
    html, count = pattern.subn('', html)

    if count == 0:
        print(f'[!] 未在列表页找到 {slug}')
        return

    # 修复 data-delay 序号
    def renumber(m):
        i = int(m.group(1))
        return f'data-delay="{i}"'
    # 简单处理：保持现有序号即可，不强制重排

    # 若已无真实人设，恢复默认引导语
    remaining = get_char_slugs(html)
    if not remaining:
        html = html.replace('朱砂所点，群像登场。点击查看各人物详情卷宗。',
                            '人物卷宗尚未录入，待正式设定后逐一补全。')

    write_index(html)
    print(f'[✓] 已从列表页移除 {slug}')


# ── Sitemap 同步 ──────────────────────────────────────

def add_to_sitemap(slug: str):
    """在 sitemap.xml 中 chars/ 条目后插入新人物条目"""
    with open(SITEMAP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    entry = f'  <url><loc>{BASE_URL}/chars/{slug}/</loc></url>\n'
    if entry in content:
        print(f'[!] sitemap 中已存在 {slug}，跳过')
        return

    anchor = f'  <url><loc>{BASE_URL}/chars/</loc></url>\n'
    if anchor not in content:
        print('[!] 未在 sitemap 中找到 chars/ 锚点，跳过')
        return

    content = content.replace(anchor, anchor + entry, 1)
    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[✓] 已更新 sitemap，插入 {slug}')


# ── 翻页同步 ───────────────────────────────────────────

def rebuild_all_pagination():
    """遍历所有人设详情页，重建翻页链接"""
    html = read_index()
    slugs = get_char_slugs(html)
    if not slugs:
        print('[i] 当前无人设，跳过翻页同步')
        return

    # 收集每个 slug 的姓名
    slug_names = []
    for slug in slugs:
        detail_path = os.path.join(CHARS_DIR, slug, 'index.html')
        if os.path.exists(detail_path):
            with open(detail_path, 'r', encoding='utf-8') as f:
                content = f.read()
            m = re.search(r'<h1 class="character-heading">(.+?)</h1>', content)
            name = m.group(1) if m else slug
        else:
            name = slug
        slug_names.append((slug, name))

    pagination_re = re.compile(
        r'<div class="character-pagination">.*?</div>',
        re.DOTALL
    )

    for i, (slug, name) in enumerate(slug_names):
        detail_path = os.path.join(CHARS_DIR, slug, 'index.html')
        if not os.path.exists(detail_path):
            continue

        prev_info = slug_names[i - 1] if i > 0 else None
        next_info = slug_names[i + 1] if i < len(slug_names) - 1 else None

        pagination = '<div class="character-pagination">'
        if prev_info:
            pagination += f'<a class="btn btn-ghost" href="../{prev_info[0]}/">← {prev_info[1]}</a>'
        else:
            pagination += f'<a class="btn btn-ghost" href="../">← 人设一览</a>'
        if next_info:
            pagination += f'<a class="btn btn-primary" href="../{next_info[0]}/">{next_info[1]} →</a>'
        else:
            pagination += f'<a class="btn btn-primary" href="../">人设一览 →</a>'
        pagination += '</div>'

        with open(detail_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = pagination_re.sub(pagination, content, count=1)

        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'[✓] 翻页同步: {slug}')

    print(f'[✓] 全部 {len(slug_names)} 个人设翻页已同步')


# ── README 同步 ──────────────────────────────────────

def update_readme():
    """根据当前人设目录更新 README 中的目录树"""
    if not os.path.exists(README_PATH):
        return

    slugs = sorted([d for d in os.listdir(CHARS_DIR)
                    if os.path.isdir(os.path.join(CHARS_DIR, d)) and d != 'template'])

    tree_lines = ['│   ├── index.html']
    if slugs:
        for i, s in enumerate(slugs):
            prefix = '│   └──' if i == len(slugs) - 1 else '│   ├──'
            tree_lines.append(f'{prefix} {s}/index.html')

    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 chars/ 目录块（在 ```text 代码块内）
    pattern = re.compile(
        r'├── chars/\n(?:│   .*\n)*',
    )
    replacement = '├── chars/\n' + '\n'.join(tree_lines) + '\n'
    content = pattern.sub(replacement, content, count=1)

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[✓] 已更新 README 目录树')


# ── 主入口 ─────────────────────────────────────────────
def main():
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    text = ''

    if len(sys.argv) >= 3 and sys.argv[1] == '--file':
        filepath = sys.argv[2]
        if not os.path.exists(filepath):
            print(f'[✗] 文件不存在: {filepath}')
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    elif len(sys.argv) >= 2 and sys.argv[1] not in ('--file', '-h', '--help', '-y', '--yes'):
        text = sys.argv[1]
    elif len(sys.argv) == 2 and sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return
    else:
        text = interact_input()

    force_yes = '-y' in sys.argv or '--yes' in sys.argv

    if not text.strip():
        print('[✗] 无输入内容')
        sys.exit(1)

    fields = parse_fields(text)

    name = fields.get('姓名', '')
    if not name:
        print('[✗] 未找到「姓名」字段')
        sys.exit(1)

    print(f'\n── 解析结果 ──')
    for k, v in fields.items():
        print(f'  {k}: {v[:40]}{"..." if len(v) > 40 else ""}')
    print()

    slug = to_slug(name)
    if not slug:
        print('[✗] 目录名不能为空')
        sys.exit(1)

    char_dir = os.path.join(CHARS_DIR, slug)
    if os.path.exists(char_dir) and not force_yes:
        ans = input(f'[!] 目录 {slug}/ 已存在，是否覆盖？(y/N): ')
        if ans.lower() != 'y':
            print('[✗] 已取消')
            sys.exit(0)

    os.makedirs(char_dir, exist_ok=True)

    # 先生成 HTML（无翻页先占位）
    detail_html = gen_detail_html(fields, slug, None, None)

    detail_path = os.path.join(char_dir, 'index.html')
    with open(detail_path, 'w', encoding='utf-8') as f:
        f.write(detail_html)
    print(f'[✓] 已生成 {slug}/index.html')

    # 更新列表页
    add_card_to_index(slug, fields)

    # 同步全部翻页
    rebuild_all_pagination()

    # 同步 sitemap
    add_to_sitemap(slug)

    # 同步 README
    update_readme()

    print(f'\n[Done] 人设 "{name}" 创建完成 → {slug}/')


if __name__ == '__main__':
    main()
