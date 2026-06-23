# uv 完全使用指南

> uv 是 Astral 开发的超高速 Python 包管理工具，用 Rust 编写，比 pip 快 10-100 倍。
> 它集成了 pip、pip-tools、virtualenv、pyenv 的功能，一个工具搞定一切。

---

## 目录

1. [安装与更新](#1-安装与更新)
2. [核心概念](#2-核心概念)
3. [项目管理（推荐工作流）](#3-项目管理推荐工作流)
4. [包管理（pip 兼容）](#4-包管理pip-兼容)
5. [Python 版本管理](#5-python-版本管理)
6. [工具运行（uvx / uv tool）](#6-工具运行uvx--uv-tool)
7. [脚本运行](#7-脚本运行)
8. [锁文件与可复现构建](#8-锁文件与可复现构建)
9. [配置与镜像](#9-配置与镜像)
10. [常见场景速查](#10-常见场景速查)
11. [与 pip / poetry / conda 对比](#11-与-pip--poetry--conda-对比)
12. [FAQ](#12-faq)

---

## 1. 安装与更新

### 安装

```bash
# Linux / macOS（官方推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS (Homebrew)
brew install uv

# pip（如果不想用官方脚本）
pip install uv
```

### 更新

```bash
uv self update
```

### 验证

```bash
uv --version
# uv 0.11.23 (示例)
```

---

## 2. 核心概念

| 概念 | 说明 |
|------|------|
| **项目 (Project)** | 有 `pyproject.toml` 的目录，uv 会自动管理虚拟环境和依赖 |
| **虚拟环境 (.venv)** | uv 默认在项目根目录创建 `.venv`，无需手动激活 |
| **锁文件 (uv.lock)** | 自动生成的精确依赖锁定文件，确保可复现安装 |
| **工具 (Tool)** | 独立安装的 CLI 工具（如 ruff、black），不污染项目依赖 |
| **uvx** | 运行工具的一次性命令（类似 `npx`） |

### uv 的设计哲学

- **不需要激活虚拟环境**：`uv run` 自动使用项目 `.venv`
- **不需要 pip install**：`uv add` 自动安装并更新 `pyproject.toml` 和 `uv.lock`
- **不需要 pyenv**：`uv python install` 直接管理 Python 版本

---

## 3. 项目管理（推荐工作流）

这是 uv 推荐的工作方式，适用于应用开发。

### 3.1 创建新项目

```bash
# 创建目录并初始化
mkdir my-project && cd my-project
uv init

# 或者直接指定名称
uv init my-project
```

`uv init` 会生成：

```
my-project/
├── .gitignore
├── .python-version    # 指定 Python 版本
├── pyproject.toml     # 项目元数据和依赖声明
├── main.py            # 入口文件模板
└── uv.lock            # 锁文件（首次 add 后生成）
```

### 3.2 添加依赖

```bash
# 添加运行时依赖
uv add requests
uv add flask sqlalchemy

# 添加开发依赖（仅开发时使用，不会打包）
uv add --dev pytest ruff mypy

# 添加带版本约束的依赖
uv add "requests>=2.28,<3.0"
uv add "flask==3.0.*"

# 从 Git 仓库添加
uv add "git+https://github.com/user/repo.git"

# 从本地路径添加
uv add ./my-local-package
```

每次 `uv add` 会自动：
1. 安装包到 `.venv`
2. 更新 `pyproject.toml` 的 `dependencies`
3. 更新 `uv.lock` 锁文件

### 3.3 移除依赖

```bash
uv remove requests
uv remove --dev pytest
```

### 3.4 同步环境

```bash
# 根据 pyproject.toml + uv.lock 安装所有依赖
uv sync

# 只同步生产依赖（不含 dev）
uv sync --no-dev

# 重新安装所有包（强制刷新）
uv sync --reinstall
```

### 3.5 运行项目

```bash
# 运行 Python 脚本（自动使用 .venv）
uv run python main.py

# 运行 pyproject.toml 中定义的脚本入口
uv run frp-monitor          # 如果定义了 [project.scripts]

# 运行模块
uv run python -m pytest
```

> **关键**：`uv run` 会自动确保依赖已安装，无需手动 `uv sync` 再运行。

### 3.6 查看项目状态

```bash
# 查看已安装的包
uv pip list

# 查看依赖树
uv tree

# 查看项目元数据
uv project version
```

### 3.7 构建与发布

```bash
# 构建 wheel 和 sdist
uv build

# 发布到 PyPI
uv publish

# 发布到私有仓库
uv publish --publish-url https://my-pypi.example.com
```

---

## 4. 包管理（pip 兼容）

如果你不想用项目管理，uv 也可以像 pip 一样直接操作。

### 4.1 安装包

```bash
# 在当前虚拟环境中安装
uv pip install requests flask

# 安装到指定虚拟环境
uv pip install --python .venv/bin/python requests

# 从 requirements.txt 安装
uv pip install -r requirements.txt

# 安装 extras
uv pip install "requests[security]"

# 安装本地包（开发模式）
uv pip install -e .
```

### 4.2 卸载包

```bash
uv pip uninstall requests
```

### 4.3 查看已安装包

```bash
uv pip list
uv pip show requests
```

### 4.4 编译 requirements.txt

```bash
# 从 pyproject.toml 生成 requirements.txt
uv pip compile pyproject.toml -o requirements.txt

# 从 requirements.in 生成 requirements.txt
uv pip compile requirements.in -o requirements.txt

# 带哈希校验
uv pip compile pyproject.toml -o requirements.txt --generate-hashes
```

### 4.5 创建虚拟环境

```bash
# 创建虚拟环境（通常不需要，uv 会自动创建）
uv venv

# 指定 Python 版本
uv venv --python 3.11

# 指定目录名
uv venv .my-venv
```

---

## 5. Python 版本管理

uv 内置了 Python 版本管理，无需 pyenv。

### 5.1 查看可用版本

```bash
uv python list
```

### 5.2 安装 Python

```bash
# 安装最新版
uv python install 3.12

# 安装指定版本
uv python install 3.11.9

# 安装多个版本
uv python install 3.10 3.11 3.12
```

### 5.3 固定项目 Python 版本

```bash
# 在项目中固定 Python 版本（写入 .python-version）
uv python pin 3.12

# 或手动编辑 .python-version
echo "3.12" > .python-version
```

### 5.4 查看当前使用的 Python

```bash
uv python find
```

---

## 6. 工具运行（uvx / uv tool）

用于运行独立的 CLI 工具，不污染项目依赖。

### 6.1 一次性运行（uvx）

```bash
# 直接运行工具（自动下载，用完即弃）
uvx ruff check .
uvx black --check .
uvx mypy src/
uvx pytest

# 指定版本
uvx ruff@0.5.0 check .

# 带参数
uvx pyclean --yes .
```

### 6.2 永久安装工具

```bash
# 全局安装工具
uv tool install ruff
uv tool install black
uv tool install pre-commit

# 列出已安装工具
uv tool list

# 升级工具
uv tool upgrade ruff

# 卸载工具
uv tool uninstall ruff
```

### 6.3 常用工具速查

```bash
# 代码格式化
uvx ruff format .

# 代码检查
uvx ruff check --fix .

# 类型检查
uvx mypy src/

# 安全审计
uvx pip-audit

# 依赖管理
uvx pip-tools compile requirements.in
```

---

## 7. 脚本运行

uv 可以管理单个 Python 脚本的依赖（无需创建项目）。

### 7.1 运行带依赖的脚本

```bash
# 自动安装脚本声明的依赖并运行
uv run --with requests script.py

# 多个依赖
uv run --with requests --with pandas script.py
```

### 7.2 脚本内声明依赖

在脚本顶部添加元数据：

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "pandas",
# ]
# ///

import requests
import pandas as pd

# 你的代码...
```

然后直接运行：

```bash
uv run script.py
# 自动安装 requests 和 pandas
```

### 7.3 初始化脚本元数据

```bash
# 为现有脚本添加元数据头
uv init --script script.py

# 添加依赖到脚本
uv add --script script.py requests pandas
```

---

## 8. 锁文件与可复现构建

### 8.1 uv.lock 的作用

- 记录所有依赖（包括传递依赖）的精确版本和哈希
- 确保团队成员和 CI 环境安装完全相同的依赖
- 跨平台：记录所有平台的依赖变体

### 8.2 更新锁文件

```bash
# 更新所有依赖到最新兼容版本
uv lock

# 更新指定包
uv lock --upgrade-package requests

# 只更新锁文件，不安装
uv lock
```

### 8.3 从锁文件安装

```bash
# uv sync 会自动使用 uv.lock
uv sync

# 等效于：
uv sync --frozen   # 严格使用锁文件，不尝试更新
```

### 8.4 导出为 requirements.txt

```bash
# 导出生产依赖
uv export --no-dev -o requirements.txt

# 导出所有依赖（含 dev）
uv export -o requirements-all.txt

# 带哈希
uv export --no-hashes -o requirements.txt
```

---

## 9. 配置与镜像

### 9.1 使用国内镜像（加速下载）

创建或编辑配置文件：

```bash
# 项目级配置
mkdir -p .python
cat > .python/config.toml << 'EOF'
[[index]]
url = "https://mirrors.aliyun.com/pypi/simple/"
default = true
EOF

# 或用户级配置
mkdir -p ~/.config/uv
cat > ~/.config/uv/uv.toml << 'EOF'
[[index]]
url = "https://mirrors.aliyun.com/pypi/simple/"
default = true
EOF
```

常用镜像源：

| 镜像 | URL |
|------|-----|
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |
| 清华 | `https://pypi.tuna.tsinghua.edu.cn/simple/` |
| 腾讯 | `https://mirrors.cloud.tencent.com/pypi/simple/` |
| 华为 | `https://repo.huaweicloud.com/repository/pypi/simple/` |

### 9.2 环境变量配置

```bash
# 设置 PyPI 镜像
export UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"

# 设置缓存目录
export UV_CACHE_DIR="/tmp/uv-cache"

# 设置 Python 安装目录
export UV_PYTHON_INSTALL_DIR="~/.local/share/uv/python"

# 禁用缓存
export UV_NO_CACHE=1
```

### 9.3 配置文件优先级

从高到低：
1. 命令行参数
2. 环境变量 (`UV_*`)
3. 项目配置 (`.python/config.toml` 或 `uv.toml`)
4. 用户配置 (`~/.config/uv/uv.toml`)
5. 系统配置 (`/etc/uv/uv.toml`)

### 9.4 查看配置

```bash
uv config
```

---

## 10. 常见场景速查

### 场景 1：新建 Flask 项目

```bash
mkdir flask-app && cd flask-app
uv init
uv add flask flask-sqlalchemy
uv add --dev pytest ruff
uv run python app.py
```

### 场景 2：从 requirements.txt 迁移

```bash
# 有 requirements.txt，想用 uv 管理
uv init
uv add -r requirements.txt
# 自动转换为 pyproject.toml + uv.lock
```

### 场景 3：运行 Jupyter Notebook

```bash
uv run --with jupyter jupyter lab
# 或
uvx jupyter lab
```

### 场景 4：在 CI 中使用

```yaml
# GitHub Actions 示例
- name: Install uv
  uses: astral-sh/setup-uv@v4

- name: Install dependencies
  run: uv sync --frozen

- name: Run tests
  run: uv run pytest
```

### 场景 5：Docker 中使用

```dockerfile
FROM python:3.12-slim

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 复制项目文件
WORKDIR /app
COPY pyproject.toml uv.lock ./

# 安装依赖（利用 Docker 层缓存）
RUN uv sync --frozen --no-dev

# 复制源码
COPY . .

# 运行
CMD ["uv", "run", "python", "main.py"]
```

### 场景 6：管理多个 Python 版本的测试

```bash
uv python install 3.10 3.11 3.12
uv run --python 3.10 pytest
uv run --python 3.11 pytest
uv run --python 3.12 pytest
```

### 场景 7：临时使用某个包（不安装）

```bash
uvx httpie GET https://httpbin.org/get
uvx cowsay "Hello uv"
```

---

## 11. 与 pip / poetry / conda 对比

| 功能 | uv | pip | poetry | conda |
|------|-----|-----|--------|-------|
| 安装速度 | ⚡ 极快 | 🐢 慢 | 🐢 慢 | 🐢 慢 |
| 虚拟环境管理 | ✅ 自动 | ❌ 需 venv | ✅ 自动 | ✅ 自动 |
| 锁文件 | ✅ uv.lock | ❌ 需 pip-tools | ✅ poetry.lock | ❌ |
| Python 版本管理 | ✅ 内置 | ❌ | ❌ | ✅ |
| 工具隔离 | ✅ uvx | ❌ | ❌ | ✅ env |
| pip 兼容 | ✅ | - | ❌ | ❌ |
| 跨平台锁 | ✅ | ❌ | ❌ | ❌ |
| 依赖解析速度 | ⚡ | 🐢 | 🐢 | 🐢 |

### 从 pip 迁移

```bash
# uv 的 pip 子命令完全兼容 pip
uv pip install -r requirements.txt
uv pip freeze
```

### 从 poetry 迁移

```bash
# uv 可以直接读取 pyproject.toml
# poetry.lock 不兼容，需要 uv 重新生成 uv.lock
uv lock
```

---

## 12. FAQ

### Q: uv 会取代 pyenv 吗？

是的，`uv python install` 和 `uv python pin` 完全替代了 pyenv 的功能。

### Q: 需要手动激活虚拟环境吗？

不需要。`uv run` 会自动使用项目的 `.venv`。如果需要手动激活：

```bash
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

### Q: uv.lock 和 poetry.lock 一样吗？

功能类似，但格式不同。uv.lock 是跨平台的（记录所有平台的依赖），poetry.lock 通常只记录当前平台。

### Q: 如何清理缓存？

```bash
uv cache clean
# 或只清理特定包
uv cache clean requests
```

### Q: 如何查看 uv 的缓存目录？

```bash
uv cache dir
```

### Q: uv 支持私有 PyPI 仓库吗？

支持。在 `pyproject.toml` 中配置：

```toml
[[tool.uv.index]]
url = "https://my-pypi.example.com/simple/"
name = "private"
```

或命令行：

```bash
uv add --index-url https://my-pypi.example.com/simple/ my-package
```

### Q: uv 可以管理 conda 环境吗？

不可以。uv 专注于 PyPI 生态系统，不支持 conda 包。如果你需要 conda（如科学计算中的非 Python 依赖），继续使用 conda/mamba。

---

## 命令速查表

```bash
# 项目管理
uv init [name]              # 初始化项目
uv add <pkg>                # 添加依赖
uv remove <pkg>             # 移除依赖
uv sync                     # 同步环境
uv lock                     # 更新锁文件
uv run <cmd>                # 运行命令
uv build                    # 构建包
uv publish                  # 发布到 PyPI

# 包管理（pip 兼容）
uv pip install <pkg>        # 安装包
uv pip uninstall <pkg>      # 卸载包
uv pip list                 # 列出包
uv pip freeze               # 输出冻结版本
uv pip compile <in> -o <out>  # 编译依赖文件

# Python 版本
uv python list              # 列出可用版本
uv python install <ver>     # 安装 Python
uv python pin <ver>         # 固定版本
uv python find              # 查看当前 Python

# 工具
uvx <tool> [args]           # 一次性运行工具
uv tool install <tool>      # 全局安装工具
uv tool list                # 列出已安装工具
uv tool upgrade <tool>      # 升级工具
uv tool uninstall <tool>    # 卸载工具

# 脚本
uv run --with <pkg> script.py  # 带依赖运行脚本
uv init --script script.py     # 初始化脚本元数据
uv add --script script.py <pkg>  # 添加脚本依赖

# 维护
uv self update              # 更新 uv 自身
uv cache clean              # 清理缓存
uv cache dir                # 查看缓存目录
uv config                   # 查看配置
```

---

*文档基于 uv 0.11.x，参考 [官方文档](https://docs.astral.sh/uv/)。*
