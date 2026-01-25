import json
import os
from typing import Any
import hashlib


class JsonDB:
    """
    Json 数据库管理类
    """

    def __init__(self, json_path: str):
        self.json_path = json_path
        # 若存在文件，则读取，否则新建
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def __get_key(self, key: Any) -> str:
        if isinstance(key, (str, int, float)):
            return str(key)
        else:
            str_key = json.dumps(key, ensure_ascii=False, sort_keys=True)
            hash_key = hashlib.sha256(str_key.encode("utf-8")).hexdigest()
            return hash_key

    def get(self, key: Any, default=None):
        """
        获取指定键的值，若不存在则返回默认值
        """

        str_key = self.__get_key(key)
        return self.data.get(str_key, default)

    def set(self, key: Any, value):
        """
        更新单个键值对
        """

        # 如果是字符串或者数字，直接转换成字符串作为键
        str_key = self.__get_key(key)
        self.data[str_key] = value

    def save(self):
        # 保存数据到文件
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
