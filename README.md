# 好好写作

把中文写自然，把值得分享的发现讲出来。好好写作是一套可独立使用的文章写作 Skill，包含中文编辑、叙事方法、完整范例和温暖手绘插图规范。

## 怎样帮你写

- **语言有气息。** 拆掉生硬的翻译腔，让动作直接出现，再补回具体细节、停顿和留白。改顺的时候，保留原有事实、条件和确定程度。
- **读者一路有发现。** 从具体问题进入，用例子、对照和解释推动理解。每一节都让读者多看见一点。
- **观点从材料里长出来。** 沿着“锚定 → 追问 → 架桥 → 落点”展开思考，让读者跟上作者为什么在意这件事。
- **插图帮助看清关系。** 用统一的温暖手绘风格呈现对照、步骤、变化和边界。一幅图解决一个理解问题。

适合理念文章、经验分享、技术解释、观点与方法文章，也可以改写已有稿件或只交文字。用户亲改过部分内容时，会从改前改后的差别学习表达偏好，再接着修改。

## 安装与使用

下载 [Skill 安装包](dist/haohao-writing.zip)，解压后把 `haohao-writing` 文件夹放进所用工具的技能目录。Codex 本地目录为 `~/.codex/skills/haohao-writing/`。已有同名版本时，保留旧版备份再替换。

方法、范例和文字扫描脚本均在包内；实际配图需要当前环境提供图像生成工具。

可以这样发起任务：

> 用 haohao-writing，把这些材料写成一篇文章。先用一个具体例子说明问题，再讲清怎么做，并在需要看清关系的地方配手绘图。

> 用 haohao-writing 修改这篇文章。我亲自改过前两段，请参照它们的表达修改后面的部分，只交文字。

## 方法与范例

从 [Skill 入口](SKILL.md) 按任务选读，也可以直接看：

| 内容 | 文件 |
| --- | --- |
| 中文表达与具体改法 | [中文写法](references/writing.md)、[句式诊断](references/sentence-patterns.md) |
| 整篇编辑、事实保护与用户改稿偏好 | [编辑流程](references/editing.md) |
| 从材料到自然表达的改写对照 | [文章改写示例](references/article-examples.md) |
| 好奇、递进、意义与文体 | [构思与叙事](references/narrative.md) |
| 不同题材的连续正文及拆解 | [完整叙事范例](references/narrative-examples.md) |
| 构图、画风、提示词与成图检查 | [温暖手绘插图](references/illustration.md) |

## 扫描与打包

脚本仅使用 Python 3 标准库。扫描器用于定位值得回读的句式，不自动改文，也不凭命中次数判断文章质量，详见 [扫描说明](references/scan-notes.md)。

```bash
python3 scripts/check_article.py path/to/article.md
python3 scripts/package_skill.py
```

打包命令会检查包内文件链接，在临时解压目录验证扫描器，并生成 `dist/haohao-writing.zip`。
