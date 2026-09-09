import argparse
import json
import subprocess
import tempfile
from pathlib import Path


HIDE_TAG = "__nbconvert_hide_input__"


def run(cmd):
    print("+", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def export_collapse(src: Path):
    """
    所有代码都不写入 HTML。
    """
    run([
        "jupyter",
        "nbconvert",
        "--to", "html",
        "--no-input",
        "--output", src.stem,
        "--output-dir", str(src.parent),
        str(src),
    ])


def export_expand(src: Path):
    """
    所有代码都写入 HTML。
    """
    run([
        "jupyter",
        "nbconvert",
        "--to", "html",
        "--show-input",
        "--output", src.stem,
        "--output-dir", str(src.parent),
        str(src),
    ])


def export_keep(src: Path):
    """
    根据 JupyterLab 中原来的 source_hidden 状态决定
    是否把每个代码单元的源代码写入 HTML。
    """

    with src.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue

        hidden = (
            cell.get("metadata", {})
                .get("jupyter", {})
                .get("source_hidden", False)
        )

        if hidden:
            metadata = cell.setdefault("metadata", {})
            tags = metadata.setdefault("tags", [])

            if HIDE_TAG not in tags:
                tags.append(HIDE_TAG)

    # 临时 notebook 放在原文件目录，避免相对路径出现问题
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".ipynb",
        prefix=".nbconvert-",
        dir=src.parent,
        encoding="utf-8",
        delete=False,
    ) as f:
        json.dump(nb, f, ensure_ascii=False)
        temp_path = Path(f.name)

    try:
        run([
            "jupyter",
            "nbconvert",
            "--to", "html",

            "--TagRemovePreprocessor.enabled=True",
            f"--TagRemovePreprocessor.remove_input_tags={{{HIDE_TAG}}}",

            "--output", src.stem,
            "--output-dir", str(src.parent),

            str(temp_path),
        ])

    finally:
        temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Convert Jupyter Notebook to HTML."
    )

    parser.add_argument(
        "file",
        type=Path,
        help="输入 .ipynb 文件",
    )

    parser.add_argument(
        "mode",
        choices=["collapse", "expand", "keep"],
        help="""
collapse : HTML 中删除全部代码
expand   : HTML 中保留全部代码
keep     : 保持 notebook 原始折叠状态
""",
    )

    args = parser.parse_args()

    src = args.file.expanduser().resolve()

    if not src.exists():
        parser.error(f"文件不存在: {src}")

    if src.suffix.lower() != ".ipynb":
        parser.error("输入必须是 .ipynb 文件")

    if args.mode == "collapse":
        export_collapse(src)

    elif args.mode == "expand":
        export_expand(src)

    elif args.mode == "keep":
        export_keep(src)

    print(f"输出: {src.with_suffix('.html')}")


if __name__ == "__main__":
    main()
