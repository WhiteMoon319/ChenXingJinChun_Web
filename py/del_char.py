#!/usr/bin/env python3
"""沉星尽春 - 人设删除脚本

从 resource/data/chars.json 中删除指定人设条目。

用法：
  python del_char.py <slug> [slug2 ...]  # 按 slug 删除（支持多个）
  python del_char.py --name <姓名>       # 按姓名查找并删除
  python del_char.py -i                  # 交互式列出所有人设供选择
  python del_char.py -i -b               # 交互式批量选择删除
  python del_char.py --all               # 删除所有人设
"""

import io
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
CHARS_JSON = os.path.join(ROOT, 'resource', 'data', 'chars.json')


def read_json() -> dict:
    if os.path.exists(CHARS_JSON):
        with open(CHARS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"title": "朱砂所点", "lead": "朱砂所点，群像登场。点击查看各人物详情卷宗。", "list": [], "characters": {}}


def write_json(data: dict):
    with open(CHARS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_slug_by_name(data: dict, name: str) -> str | None:
    for slug, c in data["characters"].items():
        if c.get("name") == name:
            return slug
    return None


def _print_char_list(data: dict):
    print('\n当前人设列表：')
    for i, slug in enumerate(data["list"]):
        c = data["characters"].get(slug, {})
        name = c.get("name", slug)
        print(f'  [{i}] {name}  ({slug})')


def interactive_select(data: dict) -> str | None:
    if not data["list"]:
        print('[i] 当前没有任何人设')
        return None

    _print_char_list(data)

    try:
        choice = input('\n请输入序号或 slug 删除 (q 取消): ').strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if choice.lower() == 'q':
        return None

    if choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(data["list"]):
            return data["list"][idx]
    else:
        if choice in data["characters"]:
            return choice

    print('[✗] 无效选择')
    return None


def interactive_batch_select(data: dict) -> list[str]:
    if not data["list"]:
        print('[i] 当前没有任何人设')
        return []

    _print_char_list(data)

    try:
        choice = input('\n请输入要删除的序号或 slug（多个用空格/逗号分隔, q 取消）: ').strip()
    except (EOFError, KeyboardInterrupt):
        return []

    if choice.lower() == 'q':
        return []

    selected = set()
    parts = [p.strip() for p in re.split(r'[,，\s]+', choice) if p.strip()]
    for part in parts:
        if part.isdigit():
            idx = int(part)
            if 0 <= idx < len(data["list"]):
                selected.add(data["list"][idx])
            else:
                print(f'[!] 无效序号 {part}，已跳过')
        elif part in data["characters"]:
            selected.add(part)
        elif get_slug_by_name(data, part):
            selected.add(get_slug_by_name(data, part))
        else:
            print(f'[!] 无法识别 "{part}"，已跳过')

    return list(selected)


def _delete_single(data: dict, slug: str) -> bool:
    c = data["characters"].get(slug)
    if not c:
        print(f'[✗] 人设 "{slug}" 不存在')
        return False

    name = c.get("name", slug)
    del data["characters"][slug]
    if slug in data["list"]:
        data["list"].remove(slug)

    print(f'[✓] 已从 chars.json 删除 {slug}  ({name})')
    return True


def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    if len(sys.argv) >= 2 and sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return

    force_yes = '-y' in sys.argv or '--yes' in sys.argv
    batch_mode = '--all' in sys.argv or '-b' in sys.argv

    data = read_json()
    slugs: list[str] = []

    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    flags = set(a for a in sys.argv[1:] if a.startswith('-'))

    if '--all' in flags:
        slugs = list(data["list"])
        if not slugs:
            print('[i] 当前没有任何人设')
            return

    elif '-i' in flags and '-b' in flags:
        slugs = interactive_batch_select(data)

    elif '-i' in flags:
        slug = interactive_select(data)
        if slug:
            slugs.append(slug)

    elif '--name' in flags:
        name_idx = sys.argv.index('--name')
        if name_idx + 1 >= len(sys.argv):
            print('[✗] 请指定姓名: --name <姓名>')
            sys.exit(1)
        name = sys.argv[name_idx + 1]
        slug = get_slug_by_name(data, name)
        if slug:
            slugs.append(slug)
        else:
            print(f'[✗] 未找到姓名为 "{name}" 的人设')
            sys.exit(1)

    elif len(args) >= 2:
        slugs = args
        for slug in slugs:
            if slug not in data["characters"]:
                print(f'[✗] 人设 "{slug}" 不存在')
                sys.exit(1)

    elif len(args) == 1:
        slugs.append(args[0])

    else:
        slugs = interactive_batch_select(data)

    if not slugs:
        print('[✗] 未选择人设')
        sys.exit(1)

    slug_names = [(s, data["characters"].get(s, {}).get("name", s)) for s in slugs]
    if len(slug_names) > 1 or batch_mode:
        print('\n待删除人设：')
        for slug, name in slug_names:
            print(f'  - {name}  ({slug})')

    if not force_yes:
        if len(slug_names) > 1:
            ans = input(f'\n确认删除以上 {len(slug_names)} 个人设？(y/N): ')
        else:
            ans = input(f'\n确认删除 "{slug_names[0][1]}" ({slug_names[0][0]})？(y/N): ')
        if ans.lower() != 'y':
            print('[✗] 已取消')
            sys.exit(0)

    deleted = 0
    for slug, name in slug_names:
        if _delete_single(data, slug):
            deleted += 1

    if deleted == 0:
        print('\n[✗] 未能删除任何人设')
        sys.exit(1)

    write_json(data)

    if deleted > 1:
        print(f'\n[Done] 已批量删除 {deleted} 个人设')
    else:
        print(f'\n[Done] 人设 "{slug_names[0][1]}" 已删除')


if __name__ == '__main__':
    main()
