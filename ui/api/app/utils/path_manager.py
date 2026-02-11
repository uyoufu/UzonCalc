import os


def get_user_calcs_root(user_id: int) -> str:
    """
    获取用户计算报告相对路径根目录
    不会创建目录
    例如: data/calcs/{user_id}
    """
    return f"data/calcs/{user_id}"


def combine_calc_report_path(user_id: int, reportName: str) -> str:
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
    full_path = os.path.join(user_root, reportName)
    if not full_path.endswith(".py"):
        full_path += ".py"

    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path
