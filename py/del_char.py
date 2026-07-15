#!/usr/bin/env python3
"""沉星尽春 - 人设删除脚本

删除指定人设的文件夹，并从列表页移除、同步其余人设翻页链接。

用法：
  python del_char.py <slug>           # 按目录名删除
  python del_char.py --name <姓名>    # 按姓名查找并删除
  python del_char.py -i               # 交互式列出所有人设供选择
"""

import os
import re
import sys
import shutil

# ── 路径配置 ───────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
CHARS_DIR = os.path.join(ROOT, 'chars')
INDEX_PATH = os.path.join(CHARS_DIR, 'index.html')
SITEMAP_PATH = os.path.join(ROOT, 'sitemap.xml')
README_PATH = os.path.join(ROOT, 'README.md')
BASE_URL = 'https://cxjc.whitemoon319.xyz'


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


def get_slug_by_name(name: str) -> str | None:
    """遍历人设目录，按姓名查找 slug"""
    for entry in os.listdir(CHARS_DIR):
        if entry == 'template':
            continue
        detail_path = os.path.join(CHARS_DIR, entry, 'index.html')
        if os.path.isfile(detail_path):
            with open(detail_path, 'r', encoding='utf-8') as f:
                content = f.read()
            m = re.search(r'<h1 class="character-heading">(.+?)</h1>', content)
            if m and m.group(1) == name:
                return entry
    return None


def remove_card_from_index(slug: str):
    """从列表页移除指定卡片"""
    html = read_index()
    pattern = re.compile(
        r'\n      <a class="char-card reveal" data-delay="\d+" href="'
        + re.escape(slug) + r'/" style="--cc: var\(--cinnabar\);">.*?</a>\n',
        re.DOTALL
    )
    html, count = pattern.subn('', html)

    if count == 0:
        print(f'[!] 未在列表页找到 {slug}')
        return False

    # 若已无真实人设，恢复默认引导语
    remaining = get_char_slugs(html)
    if not remaining:
        html = html.replace('朱砂所点，群像登场。点击查看各人物详情卷宗。',
                            '人物卷宗尚未录入，待正式设定后逐一补全。')

    write_index(html)
    print(f'[✓] 已从列表页移除 {slug}')
    return True


def remove_from_sitemap(slug: str):
    """从 sitemap.xml 中删除人物条目"""
    if not os.path.exists(SITEMAP_PATH):
        print('[!] sitemap 不存在，跳过')
        return

    with open(SITEMAP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    entry = f'  <url><loc>{BASE_URL}/chars/{slug}/</loc></url>\n'
    if entry not in content:
        print(f'[!] sitemap 中未找到 {slug}，跳过')
        return

    content = content.replace(entry, '', 1)
    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[✓] 已从 sitemap 移除 {slug}')


def rebuild_all_pagination():
    """遍历所有人设详情页，重建翻页链接"""
    html = read_index()
    slugs = get_char_slugs(html)
    if not slugs:
        print('[i] 当前无人设，跳过翻页同步')
        return

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

    print(f'[✓] 剩余 {len(slug_names)} 个人设翻页已同步')


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

    pattern = re.compile(
        r'├── chars/\n(?:│   .*\n)*',
    )
    replacement = '├── chars/\n' + '\n'.join(tree_lines) + '\n'
    content = pattern.sub(replacement, content, count=1)

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print('[✓] 已更新 README 目录树')


def interactive_select() -> str | None:
    """交互式列出人设供选择"""
    html = read_index()
    slugs = get_char_slugs(html)
    if not slugs:
        print('[i] 当前没有任何人设')
        return None

    names = []
    for slug in slugs:
        detail_path = os.path.join(CHARS_DIR, slug, 'index.html')
        if os.path.isfile(detail_path):
            with open(detail_path, 'r', encoding='utf-8') as f:
                content = f.read()
            m = re.search(r'<h1 class="character-heading">(.+?)</h1>', content)
            names.append(m.group(1) if m else slug)
        else:
            names.append(slug)

    print('\n当前人设列表：')
    for i, (slug, name) in enumerate(zip(slugs, names)):
        print(f'  [{i}] {name}  ({slug}/)')

    try:
        choice = input('\n请输入序号或 slug 删除 (q 取消): ').strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if choice.lower() == 'q':
        return None

    if choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(slugs):
            return slugs[idx]
    else:
        if choice in slugs:
            return choice

    print('[✗] 无效选择')
    return None


def main():
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    if len(sys.argv) >= 2 and sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return

    force_yes = '-y' in sys.argv or '--yes' in sys.argv

    slug = None

    if len(sys.argv) == 2 and sys.argv[1] == '-i':
        slug = interactive_select()
    elif len(sys.argv) >= 3 and sys.argv[1] == '--name':
        name = sys.argv[2]
        slug = get_slug_by_name(name)
        if not slug:
            print(f'[✗] 未找到姓名为 "{name}" 的人设')
            sys.exit(1)
    elif len(sys.argv) >= 2:
        slug = sys.argv[1]
    else:
        slug = interactive_select()

    if not slug:
        print('[✗] 未选择人设')
        sys.exit(1)

    # 验证存在
    char_dir = os.path.join(CHARS_DIR, slug)
    if not os.path.isdir(char_dir) or not os.path.isfile(os.path.join(char_dir, 'index.html')):
        print(f'[✗] 人设 "{slug}" 不存在')
        sys.exit(1)

    # 读取姓名
    with open(os.path.join(char_dir, 'index.html'), 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'<h1 class="character-heading">(.+?)</h1>', content)
    name = m.group(1) if m else slug

    # 确认
    if not force_yes:
        ans = input(f'\n确认删除 "{name}" ({slug}/)？(y/N): ')
        if ans.lower() != 'y':
            print('[✗] 已取消')
            sys.exit(0)

    # 删除目录
    shutil.rmtree(char_dir)
    print(f'[✓] 已删除目录 {slug}/')

    # 更新列表页
    remove_card_from_index(slug)

    # 同步翻页
    rebuild_all_pagination()

    # 同步 sitemap
    remove_from_sitemap(slug)

    # 同步 README
    update_readme()

    print(f'\n[Done] 人设 "{name}" 已删除')


if __name__ == '__main__':
    main()
