from pathlib import Path
import sys
import numpy as np

# When using pip packages, this line is not needed; only needed when running this script from the core directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.uzoncalc import *
from core.uzoncalc.extension.echarts import EChart


@uzon_calc()
async def sheet():
    doc_title("T-Section Moment of Inertia Calculation")
    page_size("A4")

    H1("T-Section Moment of Inertia Calculation")

    Info(
        "This document calculates the moment of inertia of a T-shaped section about its neutral axis."
    )

    toc("Table of Contents")

    H2("Section Basic Parameters")

    """
    A T-section consists of two rectangular parts: the flange (upper part) and the web (lower part).
    The geometric parameters of each part are defined below.
    """

    H3("Flange Parameters")

    "Flange width:"
    b_f = 300 * unit.millimeter
    alias("b_f", "Flange width b_f")

    "Flange thickness:"
    h_f = 50 * unit.millimeter
    alias("h_f", "Flange thickness h_f")

    H3("Web Parameters")

    "Web width:"
    b_w = 100 * unit.millimeter
    alias("b_w", "Web width b_w")

    "Web height:"
    h_w = 200 * unit.millimeter
    alias("h_w", "Web height h_w")

    "Total section height:"
    h_total = h_f + h_w
    alias("h_total", "Total section height h")

    Br()

    H2("Section Geometric Properties")

    H3("Area Calculation")

    "Flange area:"
    A_f = b_f * h_f
    alias("A_f", "Flange area A_f")

    "Web area:"
    A_w = b_w * h_w
    alias("A_w", "Web area A_w")

    "Total area:"
    A_total = A_f + A_w
    alias("A_total", "Total area A")

    H3("Neutral Axis Position")

    """
    Using the bottom of the section as the reference axis (y=0), calculate the distance from the centroid of each part to the reference axis.
    """

    "Flange centroid height (from bottom):"
    y_f = h_w + h_f / 2
    alias("y_f", "Flange centroid height y_f")

    "Web centroid height (from bottom):"
    y_w = h_w / 2
    alias("y_w", "Web centroid height y_w")

    "Neutral axis position (from bottom):"
    y_c = (A_f * y_f + A_w * y_w) / A_total
    alias("y_c", "Neutral axis position y_c")

    Br()

    H2("Moment of Inertia Calculation")

    H3("Moment of Inertia about Neutral Axis")

    """
    Using the parallel axis theorem to calculate the moment of inertia of each part about the neutral axis.
    Formula: I_c = I_g + A * d²
    where I_g is the self moment of inertia, A is the area, and d is the distance from the centroid to the neutral axis.
    """

    "Flange self moment of inertia (about its centroidal axis):"
    I_f_self = b_f * h_f**3 / 12
    alias("I_f_self", "Flange self moment of inertia I_f,g")

    "Distance from flange to neutral axis:"
    d_f = abs(y_f - y_c)
    alias("d_f", "Flange to neutral axis distance d_f")

    "Flange moment of inertia about neutral axis:"
    I_f = I_f_self + A_f * d_f**2
    alias("I_f", "Flange moment of inertia I_f")

    Br()

    "Web self moment of inertia (about its centroidal axis):"
    I_w_self = b_w * h_w**3 / 12
    alias("I_w_self", "Web self moment of inertia I_w,g")

    "Distance from web to neutral axis:"
    d_w = abs(y_w - y_c)
    alias("d_w", "Web to neutral axis distance d_w")

    "Web moment of inertia about neutral axis:"
    I_w = I_w_self + A_w * d_w**2
    alias("I_w", "Web moment of inertia I_w")

    Br()

    "Total moment of inertia of T-section (about neutral axis):"
    I_total = I_f + I_w
    alias("I_total", "Total moment of inertia I_c")

    Br()

    H3("Section Modulus")

    "Distance from upper extreme fiber (flange) to neutral axis:"
    e_top = h_total - y_c
    alias("e_top", "Upper distance e_top")

    "Distance from lower extreme fiber (web bottom) to neutral axis:"
    e_bottom = y_c
    alias("e_bottom", "Lower distance e_bottom")

    "Upper section modulus:"
    W_top = I_total / e_top
    alias("W_top", "Upper section modulus W_top")

    "Lower section modulus:"
    W_bottom = I_total / e_bottom
    alias("W_bottom", "Lower section modulus W_bottom")

    Br()

    H2("Section Properties Comparison Table")

    Table(
        [
            [
                th("Property", rowspan=2),
                th("Flange Part", rowspan=1),
                th("Web Part", rowspan=1),
                th("Total", rowspan=1),
            ],
        ],
        [
            ["Width (mm)", f"{b_f.magnitude:.0f}", f"{b_w.magnitude:.0f}", "-"],
            [
                "Height (mm)",
                f"{h_f.magnitude:.0f}",
                f"{h_w.magnitude:.0f}",
                f"{h_total.magnitude:.0f}",
            ],
            [
                "Area (mm²)",
                f"{A_f.magnitude:.0f}",
                f"{A_w.magnitude:.0f}",
                f"{A_total.magnitude:.0f}",
            ],
            [
                "Self Moment of Inertia (mm⁴)",
                f"{I_f_self.magnitude:.2e}",
                f"{I_w_self.magnitude:.2e}",
                "-",
            ],
            [
                "Distance to Neutral Axis (mm)",
                f"{d_f.magnitude:.2f}",
                f"{d_w.magnitude:.2f}",
                "-",
            ],
            [
                "Moment of Inertia about Neutral Axis (mm⁴)",
                f"{I_f.magnitude:.2e}",
                f"{I_w.magnitude:.2e}",
                f"{I_total.magnitude:.2e}",
            ],
        ],
        title="T-Section Properties Summary Table",
    )

    Br()

    H2("Calculation Results Summary")

    H3("Geometric Properties")

    inline()
    "Total section area A = "
    A_total
    endInline()

    inline()
    "Neutral axis position (from bottom) y_c = "
    y_c
    endInline()

    H3("Moment of Inertia")

    inline()
    "Section moment of inertia I_c = "
    I_total
    endInline()

    H3("Section Modulus")

    inline()
    "Upper section modulus W_top = "
    W_top
    endInline()

    inline()
    "Lower section modulus W_bottom = "
    W_bottom
    endInline()

    Br()

    H2("Section Diagram")

    """
    The following ECharts diagram shows the geometric schematic of the T-section with key dimensions labeled.
    """

    # Calculate values for plotting
    b_f_val = b_f.to(unit.millimeter).magnitude
    h_f_val = h_f.to(unit.millimeter).magnitude
    b_w_val = b_w.to(unit.millimeter).magnitude
    h_w_val = h_w.to(unit.millimeter).magnitude
    y_c_val = y_c.to(unit.millimeter).magnitude

    EChart(
        {
            "title": {"text": "T-Section Geometric Diagram"},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "10%", "right": "10%", "bottom": "10%", "top": "10%"},
            "xAxis": {
                "type": "value",
                "min": -50,
                "max": max(b_f_val, b_w_val) + 50,
                "name": "Width (mm)",
            },
            "yAxis": {
                "type": "value",
                "min": -50,
                "max": h_f_val + h_w_val + 50,
                "name": "Height (mm)",
            },
            "series": [
                {
                    "type": "scatter",
                    "symbolSize": 8,
                    "data": [
                        [(b_f_val - b_w_val) / 2, h_w_val],  # Flange bottom left
                        [
                            (b_f_val - b_w_val) / 2 + b_w_val,
                            h_w_val,
                        ],  # Flange bottom right
                        [
                            (b_f_val - b_w_val) / 2 + b_w_val,
                            h_w_val + h_f_val,
                        ],  # Flange top right
                        [(b_f_val - b_w_val) / 2, h_w_val + h_f_val],  # Flange top left
                        [0, 0],  # Web bottom left
                        [b_w_val, 0],  # Web bottom right
                        [b_w_val, h_w_val],  # Web top right
                        [0, h_w_val],  # Web top left
                        [b_f_val / 2, y_c_val],  # Neutral axis position
                    ],
                    "itemStyle": {"color": "rgba(0, 0, 0, 0)"},
                }
            ],
            "markLine": {
                "data": [
                    {
                        "yAxis": y_c_val,
                        "name": "Neutral Axis",
                        "lineStyle": {"color": "red", "type": "dashed"},
                    },
                ]
            },
        }
    )

    Br()

    H2("Calculation Notes")

    """
    This calculation uses the parallel axis theorem to compute the moment of inertia of the T-section. The specific steps are:

    1. Decompose the T-section into two rectangular parts: flange and web;

    2. Define the geometric parameters of each part (width and height);

    3. Select a reference axis (in this example, the bottom of the section is chosen as reference) and calculate the centroid position of each part;

    4. Calculate the centroid position of the entire section (i.e., the neutral axis position);

    5. Using the parallel axis theorem, calculate the moment of inertia of each part about the neutral axis;

    6. Sum the moments of inertia of each part to obtain the total moment of inertia;

    7. Calculate the section modulus based on the neutral axis position and extreme fiber distances.

    This method is applicable to all section shapes composed of rectangles.
    """

    save("../output/T_section_moment_of_inertia_en.html")


if __name__ == "__main__":
    ctx = run_sync(sheet)
