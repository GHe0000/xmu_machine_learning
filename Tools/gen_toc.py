import argparse
import nbformat
import re
from pathlib import Path

def generate_toc(notebook_path: str, toc_title="目录"):
    """读取 .ipynb 文件并打印 Markdown 目录"""
    path = Path(notebook_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {notebook_path}")

    nb = nbformat.read(path, as_version=4)
    headers = []

    # 提取所有 markdown 标题
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            for line in cell.source.splitlines():
                if re.match(r"^#+\s", line):
                    level = len(line) - len(line.lstrip("#"))
                    title = line.lstrip("# ").strip()
                    if title:
                        anchor = re.sub(r"[^\w\-一-龥]", "", title.replace(" ", "-")).lower()
                        headers.append((level, title, anchor))

    if not headers:
        print("未找到任何 Markdown 标题。")
        return

    # 生成目录 Markdown
    toc_lines = [f"# {toc_title}", ""]
    for level, title, anchor in headers:
        indent = "  " * (level - 1)
        toc_lines.append(f"{indent}- [{title}](#{anchor})")

    toc_md = "\n".join(toc_lines)
    print("```markdown")
    print(toc_md)
    print("```")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 Jupyter Notebook 的 Markdown 目录")
    parser.add_argument("--path", required=True, help="Notebook 文件路径 (.ipynb)")
    parser.add_argument("--title", default="目录", help="目录标题（默认：目录）")
    args = parser.parse_args()
    generate_toc(args.path, args.title)
