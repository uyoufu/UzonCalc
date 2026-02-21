import os


def get_user_calcs_root(user_id: int) -> str:
    """
    获取用户计算报告相对路径根目录
    不会创建目录
    例如: data/calcs/{user_id}
    """
    return f"data/calcs/{user_id}"


def combine_calc_category_path(user_id: int, categoryName: str) -> str:
    """
    组合用户计算分类的完整路径
    会自动创建所需目录

    参数:
    - user_id: 用户 ID
    - categoryName: 分类名称 (例如分类文件名)

    返回:
    - 完整路径字符串
    """
    user_root = get_user_calcs_root(user_id)
    full_path = os.path.join(user_root, categoryName)
    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path


def combine_calc_report_path(user_id: int, reportName: str, categoryName: str) -> str:
    """
    组合用户计算报告的完整路径
    会自动创建所需目录

    参数:
    - user_id: 用户 ID
    - reportName: 报告名称 (例如报告文件名)

    返回:
    - 完整路径字符串
    """
    user_root = get_user_calcs_root(user_id)

    full_path = os.path.join(user_root, categoryName, reportName)

    if not full_path.endswith(".py"):
        full_path += ".py"

    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path


def build_calc_report_file_path(
    user_id: int, report_name: str, category_name: str
) -> str:
    """
    构建计算报告源码文件绝对路径
    """
    return os.path.abspath(
        combine_calc_report_path(user_id, report_name, category_name)
    )


def sync_calc_report_file(old_file_path: str, new_file_path: str) -> None:
    """
    同步计算报告文件路径（重命名或移动）
    """
    if old_file_path == new_file_path:
        return

    if not os.path.exists(old_file_path):
        return

    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    os.replace(old_file_path, new_file_path)


def write_calc_report_file(file_path: str, content: str) -> None:
    """
    写入计算报告源码文件
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def _safe_makedirs(path: str) -> bool:
    os.makedirs(path, exist_ok=True)
    return True


def _safe_rename(src: str, dst: str) -> bool:
    try:
        os.rename(src, dst)
        return True
    except OSError:
        return False


def _safe_rmdir(path: str) -> bool:
    try:
        os.rmdir(path)
        return True
    except OSError:
        return False


def cleanup_empty_parent_dirs(user_id: int, start_dir: str) -> bool:
    """
    清理空父目录，最多清理到用户根目录 data/calcs/{user_id}
    """
    user_root = os.path.abspath(get_user_calcs_root(user_id))
    current_dir = os.path.abspath(start_dir)

    cleaned = False
    while current_dir.startswith(user_root) and current_dir != user_root:
        if not _safe_rmdir(current_dir):
            break
        cleaned = True
        current_dir = os.path.dirname(current_dir)

    return cleaned


def create_category_directory(user_id: int, category_name: str) -> bool:
    """
    创建分类目录（支持多级目录）
    """
    category_path = combine_calc_category_path(user_id, category_name)
    return _safe_makedirs(category_path)


def rename_category_directory(user_id: int, old_name: str, new_name: str) -> bool:
    """
    重命名分类目录（支持多级目录）
    """
    if old_name == new_name:
        return True

    old_path = os.path.abspath(combine_calc_category_path(user_id, old_name))
    new_path = os.path.abspath(combine_calc_category_path(user_id, new_name))

    if old_path == new_path:
        return True

    if os.path.exists(new_path):
        return False

    if os.path.exists(old_path):
        if not _safe_rename(old_path, new_path):
            return False
        cleanup_empty_parent_dirs(user_id, os.path.dirname(old_path))
        return True

    return _safe_makedirs(new_path)


def delete_category_directory(user_id: int, category_name: str) -> bool:
    """
    删除分类目录（仅删除空目录，避免误删其他多级分类目录）
    """
    category_path = os.path.abspath(combine_calc_category_path(user_id, category_name))

    if not os.path.exists(category_path):
        return True

    if not _safe_rmdir(category_path):
        return False
    cleanup_empty_parent_dirs(user_id, os.path.dirname(category_path))
    return True
