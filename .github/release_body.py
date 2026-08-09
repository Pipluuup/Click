"""从 CHANGELOG.md 提取指定版本的更新日志，生成 GitHub Release 正文（RELEASE_BODY.md）。

用法：python .github/release_body.py <版本标签，如 v1.0.1>
"""
import re
import sys


def main():
    tag = sys.argv[1]
    text = open("CHANGELOG.md", encoding="utf-8").read()

    # 按 "## [版本]" 拆分成各版本段落
    sections = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^## \[(.+?)\]", line)
        if m:
            current = m.group(1)
            sections[current] = [line]
        elif current is not None:
            sections[current].append(line)

    body = "\n".join(sections.get(tag, ["# " + tag, "", "详见 CHANGELOG.md。"]))
    header = (
        "## Click 字母随机连发器 " + tag + "\n\n"
        + body
        + "\n\n- Windows 可执行文件：`Click-" + tag + "-win64.exe`（免 Python 环境，双击即用）\n"
        + "- 使用说明见仓库 [README.md](README.md)\n"
    )
    with open("RELEASE_BODY.md", "w", encoding="utf-8") as f:
        f.write(header)
    print(header)


if __name__ == "__main__":
    main()
