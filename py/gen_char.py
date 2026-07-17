#!/usr/bin/env python3
"""沉星尽春 - 人设管理脚本

读写 resource/data/chars.json，追加/更新人设数据。

用法：
  python gen_char.py                              # 交互模式，逐行输入（可连续创建）
  python gen_char.py --file input.txt             # 从文本文件读取（用 ==== 分隔多个人设）
  python gen_char.py "姓名: xxx\n字: xxx\n..."    # 命令行传入文本

批量导入：
  在 --file 文本文件中用独占一行的 ==== 或 --- 分隔多个人设：
    姓名: 张三
    ...
    ====
    姓名: 李四
    ...
"""

import io
import json
import os
import re
import sys

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
CHARS_JSON = os.path.join(ROOT, 'resource', 'data', 'chars.json')
FIELD_KEYS = ['姓名', '字', '年龄', '所属势力', '职业',
              '状态', '关键词', '性格', '经历', '外貌', '衣着', '备注']

_BATCH_RE = re.compile(r'\n={3,}\s*\n|\n-{3,}\s*\n')


def split_blocks(text: str) -> list[str]:
    return [b.strip() for b in _BATCH_RE.split(text) if b.strip()]


def to_slug(name: str) -> str:
    if HAS_PYPINYIN:
        s = ''.join(lazy_pinyin(name, style=Style.NORMAL, strict=False))
        return re.sub(r'[^a-z0-9]', '', s.lower())
    print(f'[!] 未安装 pypinyin，无法自动转换 "{name}"')
    return input('请输入目录名（拼音，如 fanwenqing）: ').strip().lower()


def read_json() -> dict:
    if os.path.exists(CHARS_JSON):
        with open(CHARS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"title": "朱砂所点", "lead": "朱砂所点，群像登场。点击查看各人物详情卷宗。", "list": [], "characters": {}}


def write_json(data: dict):
    with open(CHARS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_fields(text: str) -> dict:
    text = text.strip().lstrip('\ufeff')
    fields = {}
    pattern = r'(?:^|\n)\s*(' + '|'.join(FIELD_KEYS) + r')\s*[:：]\s*'
    parts = re.split(pattern, text, maxsplit=0)
    for i in range(1, len(parts), 2):
        key = parts[i]
        val = parts[i + 1].strip() if i + 1 < len(parts) else ''
        fields[key] = val
    return fields


def build_character(fields: dict) -> dict:
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

    lead = f'{status} · {occupation}' if status and occupation else (status or occupation or keywords or name)

    tags = []
    if faction:
        tags.append(faction)
    if occupation:
        tags.append(occupation)
    if status:
        tags.append(status)
    for kw in [k.strip() for k in keywords.replace('，', ',').split(',') if k.strip()]:
        tags.append(kw)

    sections = []
    sections.append({"heading": "外貌", "text": appearance})
    sections.append({"heading": "衣着", "text": clothing, "list": True})
    sections.append({"heading": "经历", "text": experience, "wide": True})
    sections.append({"heading": "性格", "text": personality})
    sections.append({"heading": "备注", "text": notes or "待补。"})

    return {
        "mark": mark,
        "name": name,
        "alias": alias,
        "lead": lead,
        "tags": tags,
        "quote": personality,
        "faction": faction,
        "status": status,
        "sections": sections,
    }


def interact_input() -> str:
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
        stripped = line.strip()
        is_new_field = False
        for k in FIELD_KEYS:
            if re.match(rf'^{k}\s*[:：]', stripped):
                is_new_field = True
                break
        if is_new_field:
            last_key = re.split(r'[:：]', stripped, maxsplit=1)[0].strip()
        elif stripped == '' and last_key in ('性格', '经历', '外貌', '衣着', '备注'):
            last_key = None
        lines.append(line)
    return '\n'.join(lines)


def _create_one(text: str, force_yes: bool) -> str | None:
    fields = parse_fields(text)
    name = fields.get('姓名', '')
    if not name:
        print('[✗] 未找到「姓名」字段，跳过此条目')
        return None

    print(f'\n── 解析结果 ──')
    for k, v in fields.items():
        print(f'  {k}: {v[:40]}{"..." if len(v) > 40 else ""}')
    print()

    slug = to_slug(name)
    if not slug:
        print('[✗] 目录名不能为空')
        return None

    data = read_json()
    existing = data["characters"].get(slug)

    if existing and not force_yes:
        ans = input(f'[!] "{name}" ({slug}) 已存在，是否覆盖？(y/N): ')
        if ans.lower() != 'y':
            print('[✗] 跳过')
            return None

    char_data = build_character(fields)
    data["characters"][slug] = char_data
    if slug not in data["list"]:
        data["list"].append(slug)

    write_json(data)
    verb = '更新' if existing else '创建'
    print(f'[✓] 已{verb} {slug}  ({name})')
    return slug


def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    force_yes = '-y' in sys.argv or '--yes' in sys.argv
    is_file = len(sys.argv) >= 3 and sys.argv[1] == '--file'

    if len(sys.argv) == 2 and sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return

    text_source: str | None = None
    if is_file:
        filepath = sys.argv[2]
        if not os.path.exists(filepath):
            print(f'[✗] 文件不存在: {filepath}')
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8') as f:
            text_source = f.read()
    elif len(sys.argv) >= 2 and sys.argv[1] not in ('-h', '--help', '-y', '--yes'):
        text_source = sys.argv[1]

    if text_source is None:
        created_slugs: list[str] = []
        while True:
            text = interact_input()
            if not text.strip():
                if not created_slugs:
                    print('[✗] 无输入内容')
                    sys.exit(1)
                break
            slug = _create_one(text, force_yes)
            if slug:
                created_slugs.append(slug)
            try:
                again = input('\n继续创建下一个人设？(y/N): ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            if again.lower() != 'y':
                break
        if not created_slugs:
            sys.exit(1)
        if len(created_slugs) > 1:
            print(f'\n[Done] 已批量创建 {len(created_slugs)} 个人设')
        else:
            print(f'\n[Done] 人设创建完成 → {created_slugs[0]}')
        return

    blocks = split_blocks(text_source)
    if not blocks:
        print('[✗] 无输入内容')
        sys.exit(1)

    block_count = len(blocks)
    if block_count > 1:
        print(f'[i] 检测到 {block_count} 个人设条目，开始批量创建...')

    created_slugs = []
    for i, block in enumerate(blocks):
        if block_count > 1:
            print(f'\n── 第 {i+1}/{block_count} 个 ──')
        slug = _create_one(block, force_yes)
        if slug:
            created_slugs.append(slug)

    if not created_slugs:
        print('\n[✗] 未能创建任何人设')
        sys.exit(1)

    if len(created_slugs) > 1:
        print(f'\n[Done] 已批量创建 {len(created_slugs)} 个人设')
    else:
        print(f'\n[Done] 人设创建完成 → {created_slugs[0]}')


if __name__ == '__main__':
    main()
