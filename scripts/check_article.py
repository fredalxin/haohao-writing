#!/usr/bin/env python3
"""只读扫描常见 Markdown 文章；提示位置，不判定作者意图、不打分。"""

import argparse
import json
import re
from pathlib import Path


PATTERNS = {
    "中文半角标点": r"[\u4e00-\u9fff]\s*[,;:.]|[,;:]\s*[\u4e00-\u9fff]",
    "编号标题": r"^#{1,6}\s*(?:[一二三四五六七八九十]+[、.]|\d+[.、）)]|其[一二三四五六七八九十]|第[一二三四五六七八九十\d]+(?:章节|章|节|步|刀|条|个|板斧|维度|方面)|[一二三四五六七八九十\d]+(?:刀|步|条|板斧|维度))",
    "翻案句式": r"(?:不是[^，。；！？\n]{1,30}[，,](?:而)?是[^，。！？\n]{1,30}|不是[^。！？\n]{1,35}?而是|这不是[^，。！？\n]{0,30}|[^，。！？\n]{1,20}不是病[，,][^。！？\n]{1,20}才是病|管的是[^，。！？\n]{1,20}[，,]?不管|不在[^，。！？\n]{1,15}[，,]?而(?:在|是)|你以为[^，。！？\n]{1,30}[，,]?其实|(?:看似|表面上)[^，。！？\n]{1,30}[，,]?实则|回头才(?:发现|明白)|真正[^，。！？\n]{1,20}的是|不重要[，,]重要的是)",
    "元话语": r"值得深思|值得关注|值得玩味|不禁让人|引人深思|发人深省|令人深思|不禁要问",
    "破折号": r"——|—",
    "长气口": r"[^，、；：。！？,;:.!?“”「」\n]{28,}",
}

RHYTHM = ("句长单调", "连续软尾", "调子单一")


def prose_lines(text):
    # ponytail: 只处理常见 Markdown；复杂 HTML、缩进代码和嵌套链接需人工豁免，确有需求再接 Markdown 解析器。
    fence = None
    header = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    frontmatter = bool(header and re.search(r"^[\w-]+:", header[1], re.M))
    for number, line in enumerate(text.splitlines(), 1):
        if frontmatter:
            if number > 1 and line.strip() == "---":
                frontmatter = False
            continue
        marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, tail = marker.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
            continue
        if fence is not None:
            continue
        line = re.sub(r"(`+).*?\1", " ", line)
        line = re.sub(r"!?\[([^\]]*)\]\([^\n]*?\)", r"\1", line)
        line = re.sub(r"https?://[^\s<>]+", " ", line)
        yield number, line


def rhythm_findings(lines, findings):
    # ponytail: 句式只是字面代理；不解析语法。标点、英文缩写及特殊排版的误报由编辑复核。
    paragraphs, current = [], []
    for number, line in lines + [(0, "")]:
        if not line.strip() or line.lstrip().startswith(("#", "|", "- ", "* ")):
            if current:
                paragraphs.append(current)
                current = []
            continue
        for match in re.finditer(r"[^。！？；]+[。！？；]?", line):
            sentence = match.group().strip(" >*_\t")
            length = len(re.findall(r"[\u4e00-\u9fffA-Za-z]", sentence))
            if length:
                current.append((number, sentence, length))

    all_sentences = []
    for paragraph in paragraphs:
        all_sentences.extend(paragraph)
        # 两个可观察的连续三句窗口，重叠时只报该串的第一处。
        previous = {"句长单调": False, "连续软尾": False}
        for i in range(len(paragraph) - 2):
            group = paragraph[i:i + 3]
            lengths = [row[2] for row in group]
            signals = {
                "句长单调": min(lengths) >= 8 and max(lengths) - min(lengths) <= 10,
                "连续软尾": all(re.search(r"(?:的|了|性|化|问题|工作|东西|事情|情况|方面)[。！？；]?$", row[1]) for row in group),
            }
            for name, matched in signals.items():
                if matched and not previous[name]:
                    findings[name].append({"line": group[0][0], "text": " ".join(row[1] for row in group), "lengths": lengths})
                previous[name] = matched

    # 短文样本太少，不给整篇比例提示。问句或短句少不是质量结论。
    if len(all_sentences) >= 10:
        varied = sum(length <= 15 or sentence.endswith("？") for _, sentence, length in all_sentences)
        if varied / len(all_sentences) < 0.05:
            findings["调子单一"].append({"line": all_sentences[0][0], "text": "短句或问句比例低于 5%，请结合文体检查。", "sentences": len(all_sentences), "short_or_question": varied})


def scan(text):
    findings = {name: [] for name in (*PATTERNS, *RHYTHM)}
    lines = list(prose_lines(text))
    for number, line in lines:
        for name, pattern in PATTERNS.items():
            if name == "长气口" and line.lstrip().startswith("#"):
                continue
            for match in re.finditer(pattern, line):
                excerpt = match.group().strip()
                if name == "长气口" and len(re.findall(r"[\u4e00-\u9fffA-Za-z]", excerpt)) < 28:
                    continue
                findings[name].append({"line": number, "text": excerpt})
    rhythm_findings(lines, findings)
    return {"counts": {name: len(rows) for name, rows in findings.items()}, "findings": findings}


def self_test():
    sample = "---\ntitle: 标题\n---\n## 一、标题\n中文,混用:标点;结尾.\n```python\n中文,代码\n```\n`中文,代码` [链接](https://x.test/中文,文件.md) 1,000 3.14\n![插图](图片/中文,图.png)\n值得深思，这不是答案。\n"
    report = scan(sample)
    assert report["counts"]["中文半角标点"] == 4
    assert report["counts"]["编号标题"] == 1
    assert report["findings"]["元话语"][0]["line"] == 11
    assert report["counts"]["翻案句式"] == 1
    assert scan("~~~text\n中文,代码\n~~~~\n正文，正确。\n")["counts"]["中文半角标点"] == 0
    assert scan("[中文,标签](x)")["counts"]["中文半角标点"] == 1
    assert scan("文" * 30 + "。")["counts"]["长气口"] == 1
    assert scan("---\n正文,有标点。\n")["counts"]["中文半角标点"] == 1
    assert scan("---\n正文,有标点。\n---\n")["counts"]["中文半角标点"] == 1
    for heading in ("## 其一：开头", "## 三条写作建议", "## 第二个问题"):
        assert scan(heading)["counts"]["编号标题"] == 1
    for sentence in ("不是数量，是依据。", "管的是事实，不管风格。", "长句不是病，憋气才是病。"):
        assert scan(sentence)["counts"]["翻案句式"] == 1
    rhythmic = scan("我们先检查导出的问题。然后确认缓存的情况。最后记录本次的工作。")
    assert rhythmic["counts"]["句长单调"] == 1
    assert rhythmic["counts"]["连续软尾"] == 1
    assert scan("文" * 20 + "。\n\n短。\n\n" + "字" * 20 + "。")["counts"]["句长单调"] == 0
    assert scan(("文" * 20 + "。") * 10)["counts"]["调子单一"] == 1
    assert scan(("文" * 20 + "。") * 9)["counts"]["调子单一"] == 0
    assert scan(("文" * 20 + "。") * 9 + "为什么？")["counts"]["调子单一"] == 0
    print("自检通过")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.article:
        print(json.dumps(scan(args.article.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))
    else:
        parser.error("请提供文章路径或 --self-test")
