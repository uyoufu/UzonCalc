# 带单位
from pint import UnitRegistry

unit = UnitRegistry()
unit.formatter.default_format = "~"


if __name__ == "__main__":
    q = 2.3e-6 * unit.m**3 / (unit.s**2 * unit.kg)
    print(f"{q:~P}")

    speed2 = 10 * unit.m / unit.second + (2 * unit.m / unit.second)
    print(f"speed2 = {speed2:~P}")
