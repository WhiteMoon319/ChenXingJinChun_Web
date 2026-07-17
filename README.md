# 沉星尽春

大景王朝世界观设定展示站 —— 今上五子夺嫡主线，收录世界观、固设皇子、人物卷宗与剧情年表。

> 在线访问：[cxjc.whitemoon319.xyz](https://cxjc.whitemoon319.xyz)

## 技术栈

原生 HTML5 · CSS3 · JavaScript，JSON 驱动渲染，零构建流程的纯静态站点，可直接部署到 GitHub Pages。Python 脚本辅助管理 JSON 数据。

## 页面导览

| 路径 | 内容 |
| --- | --- |
| `/` | 响应式首页（世界观概述、门户导航） |
| `world/` | 大景王朝背景：开国史、卷首详阅、全境与州府舆图 |
| `preset/` | 五位皇子固设名录，各含详细页（年纪主线进程、时代背景、相关人物、注意事项） |
| `chars/` | 人物卷宗一览与各角色详情页 |
| `forces/` | 势力展示（朝堂职官表、皇室玉牒） |
| `timeline/` | 太祖定鼎以来的剧情年表 |
| `m/` | 轻量移动端入口 |

## 本地运行

需通过 HTTP 服务访问，以保证路径行为与线上一致。

```bash
python -m http.server 8000
```

访问 `http://localhost:8000/` 即可。

## 目录结构

```text
.
├── index.html
├── m/index.html
├── py/               # gen_char.py、del_char.py
├── world/index.html
├── preset/
│   ├── index.html
│   └── detail.html
├── chars/
│   ├── index.html
│   └── detail.html
├── forces/
│   ├── index.html
│   ├── officials/index.html
│   └── royal/index.html
├── timeline/index.html
├── resource/
│   ├── css/
│   │   ├── style.css
│   │   └── mobile.css
│   ├── js/site-nav.js
│   ├── img/            # Logo、背景、舆图
│   └── data/           # JSON 数据文件
├── CNAME
├── robots.txt
├── sitemap.xml
└── 404.html
```

## 响应式适配

所有页面共用统一响应式布局，不再按 User-Agent 分流。断点：

- **768px**：内容切换为单列布局
- **599px**：启用折叠导航，紧凑排版

`/m/` 作为轻量入口独立保留。

## 暗色主题

通过 `prefers-color-scheme: dark` 跟随系统自动切换夜纸深色主题，覆盖纸纹、导航、卡片、时间轴、舆图画框、按钮等全部组件。文字对比度对齐 WCAG AA 标准。

## 可访问性

- 语义化 HTML 地标（`<main>`、`<nav>`、`<h1>`）
- 每页注入跳过导航链接（Tab 聚焦可见）
- 当前栏目自动标记 `aria-current="page"`
- `:focus-visible` 键盘焦点样式
- 交互控件均提供 `aria-label`
- `prefers-reduced-motion` 动画降级

## SEO

- 全页面 `canonical` 链接指向自定义域名
- 首页 Open Graph 元数据
- `sitemap.xml` + `robots.txt` + 自定义 `404.html`

## 开发指引

### 样式

| 文件 | 作用范围 |
| --- | --- |
| `resource/css/style.css` | 主站及全部内容页 |
| `resource/css/mobile.css` | `/m/` 手机目录页 |

### JavaScript

所有页面需加载 `resource/js/site-nav.js`，根据文件层级使用对应相对路径：

```html
<script defer src="resource/js/site-nav.js"></script>       <!-- 根目录 -->
<script defer src="../resource/js/site-nav.js"></script>    <!-- 一级目录及 detail.html -->
<script defer src="../../resource/js/site-nav.js"></script> <!-- 二级目录（如 forces/officials/） -->
```

### 新增内容

内容数据以 JSON 存储于 `resource/data/`，页面通过 `fetch` 动态渲染。

- **人设**：`py/gen_char.py` 写入 `resource/data/chars.json`，`chars/` 下页面自动读取渲染
- **删除人设**：`py/del_char.py` 从 JSON 移除条目
- **固设、年表、势力**：直接编辑对应 JSON 文件即可

```bash
python py/gen_char.py                       # 交互式创建
python py/gen_char.py --file input.txt      # 批量导入
python py/del_char.py -i -b                 # 交互式批量删除
python py/del_char.py muche jiangsun        # 按 slug 删除
```

> 不再需要复制 HTML 模板或手动修改列表页，所有列表与详情页均由 JSON 驱动。
