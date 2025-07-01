# crawler/utilis/data_processing.py
"""
此模組包含通用的資料處理函數，例如字元清理和巢狀結構扁平化。
"""

import json
import re
from typing import Any, List, Dict, Optional


def remove_illegal_chars(text: Any) -> Any:
    """
    從字串中移除非 ASCII 字元，但保留換行符和回車符。
    如果輸入不是字串，則原樣返回。

    Args:
        text (Any): 要清理的輸入文字。

    Returns:
        Any: 清理後的字串，如果輸入不是字串則為原始輸入。
    """
    if isinstance(text, str):
        # 僅允許 ASCII 可列印字元 (0x20-0x7E)、換行符 (0x0A)、回車符 (0x0D) 以及中文字符 (0x4E00-0x9FFF)
        cleaned_text: str = "".join(
            char
            for char in text
            if 0x20 <= ord(char) <= 0x7E
            or ord(char) in [0x0A, 0x0D]
            or (0x4E00 <= ord(char) <= 0x9FFF)
        )
        return cleaned_text
    return text


def clean_text(text: Any) -> str:
    """
    清理文字內容，移除斷行符號、表情符號及其他非文字字元，只保留文字。
    Args:
        text (Any): 要清理的輸入文字。
    Returns:
        str: 清理後的文字。
    """
    if not isinstance(text, str):
        text = str(text)

    # 移除斷行符號，替換為空格
    text = text.replace('\n', ' ').replace('\r', ' ')

    # 移除表情符號及其他非文字字元，只保留字母、數字、常見標點符號和中文字符
    # \w 匹配字母、數字、底線
    # \s 匹配空白字元
    # \u4e00-\u9fff 匹配中文字符
    # 其他標點符號可以根據需要添加
    cleaned_text = re.sub(r'[^\w\s.,!?;:()\'"-—\u4e00-\u9fff]+', '', text)

    return cleaned_text.strip()


def flatten_jobcat_recursive(
    node_list: List[Dict[str, Any]],
    parent_des: Optional[str] = None,
    parent_no: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    遞迴地扁平化職位類別的巢狀結構。

    Args:
        node_list (List[Dict[str, Any]]): 當前層級的職位類別節點列表。
        parent_des (Optional[str]): 父類別的中文描述，用於構建扁平化後的資料。
        parent_no (Optional[str]): 父類別的代碼，用於構建扁平化後的資料。

    Returns:
        List[Dict[str, str]]: 扁平化後的職位類別列表，每個元素是一個字典，包含父類別和當前類別的資訊。
    """
    flat_list: List[Dict[str, str]] = []
    for node in node_list:
        row: Dict[str, str] = {
            "parent_code": parent_no if parent_no is not None else "",
            "parent_name": parent_des if parent_des is not None else "",
            "job_code": node.get("no") if node.get("no") is not None else "",
            "job_name": node.get("des") if node.get("des") is not None else "",
        }
        flat_list.append(row)
        if "n" in node and node["n"]:
            children_list: List[Dict[str, str]] = flatten_jobcat_recursive(
                node_list=node["n"],
                parent_des=node.get("des"),
                parent_no=node.get("no"),
            )
            flat_list.extend(children_list)
    return flat_list