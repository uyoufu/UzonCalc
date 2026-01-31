def deep_update(base_dict, *update_dicts: dict | tuple[dict | None] | None) -> dict:
    """递归合并字典，支持多个字典参数，类似 JavaScript 的 Object.assign"""
    for update_dict in update_dicts:
        if not isinstance(update_dict, dict):
            continue

        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    return base_dict


class DotDict(dict):
    """支持点号访问的字典"""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{item}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{item}'")

    def deep_update(self, *update_dicts):
        """递归合并字典，支持多个字典参数，类似 JavaScript 的 Object.assign"""
        deep_update(self, *update_dicts)
        return self
