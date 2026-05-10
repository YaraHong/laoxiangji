import re


def fix_text(text: str) -> str:
    """修复文本编码和常见格式问题"""
    # 替换不可见控制字符（保留常见空白）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    # 统一换行为 \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 合并连续空白（不合并换行）
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text


def clean_text(text: str) -> str:
    """清理文档中的干扰内容"""
    # 移除页码（如 "第 1 页"、"Page 1"、"1 / 20"）
    text = re.sub(r"第\s*\d+\s*页", "", text)
    text = re.sub(r"Page\s*\d+\s*(of\s*\d+)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+\s*/\s*\d+\s*页?", "", text)

    # 移除页眉页脚常见标记
    text = re.sub(r"^.*?(?:页眉|页脚|header|footer).*?$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    # 移除目录行（连续的点和页码）
    text = re.sub(r"^.*\.{5,}\s*\d+$", "", text, flags=re.MULTILINE)

    # 移除纯数字单行（可能是页码残留）
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # 跳过空行、纯数字行、纯符号行
        if not stripped:
            cleaned_lines.append("")
            continue
        if re.match(r"^\d{1,4}$", stripped):
            continue
        if re.match(r"^[-_=*]{3,}$", stripped):
            cleaned_lines.append("")
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def clean_document_text(text: str) -> str:
    """对文档内容进行完整的数据清理"""
    text = fix_text(text)
    text = clean_text(text)

    # 合并连续空行（最多保留1个空行）
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 去除首尾空白
    text = text.strip()

    return text
