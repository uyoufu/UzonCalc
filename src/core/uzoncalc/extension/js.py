from ..context_utils.elements import Props, h


def js(js_code: str):
    """
    wrap JS code in a script tag
    """

    return f"""
    <script>
        (function() {{
            {js_code}
        }})();
    </script>
"""


def Js(
    js_code: str,
    classes: str | None = None,
    *,
    props: Props | None = None,
    tag: str = "figure",
):
    """
    wrap JS code in a script tag inside a figure element
    """
    h(tag, js(js_code), classes=classes, props=props, persist=True)
