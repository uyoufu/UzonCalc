from ..tools_mcp import mcp


# 桥涵横向车道布载系数
@mcp.tool
def lane_load_factor(lane_num: int) -> float:
    """
    桥涵横向车道布载系数
    :param lane_num: 车道数,取值范围为1-8
    :return: 车道布载系数
    """

    tables = [[1, 2, 3, 4, 5, 6, 7, 8], [1.2, 1.0, 0.78, 0.67, 0.60, 0.55, 0.52, 0.50]]
    if lane_num < 1:
        return 1.0
    if lane_num > 8:
        return 0.50

    index = int(lane_num) - 1
    return tables[1][index]
