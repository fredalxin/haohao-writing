#!/usr/bin/env python3
"""构建独立 Skill ZIP，在临时解压目录核对方法页和工具。仅使用标准库。"""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile


def check_links(root, paths):
    checked = 0
    for path in paths:
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        # ponytail: 校验本包使用的普通 Markdown 链接，不实现任意 Markdown 语法。
        text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$", "", text)
        text = re.sub(r"(`+).*?\1", "", text)
        for target in re.findall(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0].strip("<>")
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                raise ValueError(f"包内引用无效：{path.relative_to(root)} → {target}")
            checked += 1
    return checked


def self_test():
    with tempfile.TemporaryDirectory(prefix="haohao-package-check-") as temporary:
        root = Path(temporary)
        reference = root / "references/example.md"
        reference.parent.mkdir(parents=True)
        reference.write_text("示例")
        page = root / "SKILL.md"
        page.write_text("[方法](references/example.md)\n`[示例](missing.md)`\n")
        assert check_links(root, [page]) == 1
        page.write_text("[参考](missing.md)")
        try:
            check_links(root, [page])
        except ValueError:
            pass
        else:
            raise AssertionError("未识别缺失的参考链接")


def build():
    self_test()
    root = Path(__file__).resolve().parents[1]
    files = [root / "SKILL.md"]
    for directory in ("agents", "references", "scripts"):
        files.extend(path for path in (root / directory).rglob("*") if path.is_file() and path.suffix in (".md", ".json", ".yaml", ".txt", ".py"))
    files = sorted(set(files))
    check_links(root, files)
    output = root / "dist/haohao-writing.zip"
    output.parent.mkdir(exist_ok=True)
    # 先验证临时包，再替换已交付的包；失败不破坏已有 ZIP。
    with tempfile.TemporaryDirectory(prefix="haohao-writing-package-", dir=output.parent) as temporary:
        temp = Path(temporary)
        candidate = temp / output.name
        with zipfile.ZipFile(candidate, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, str(Path("haohao-writing") / path.relative_to(root)))
        with zipfile.ZipFile(candidate) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"ZIP 校验失败：{bad}")
            archive.extractall(temp / "unpacked")
        unpacked = temp / "unpacked/haohao-writing"
        links = check_links(unpacked, list(unpacked.rglob("*.md")))
        command = [sys.executable, "-I", "-B", str(unpacked / "scripts/check_article.py")]
        subprocess.run(command + ["--self-test"], cwd=unpacked, check=True, capture_output=True, text=True)
        result = subprocess.run(command + [str(unpacked / "references/narrative-examples.md")], cwd=unpacked, check=True, capture_output=True, text=True)
        counts = json.loads(result.stdout)["counts"]
        candidate.replace(output)
    print(json.dumps({"package": str(output), "files": len(files), "local_links_verified": links, "package_guard_self_test": "passed", "scanner_self_test": "passed", "example_scan": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
