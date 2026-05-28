from ..context_utils.elements import Div, Props


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
):
    """
    wrap JS code in a script tag inside a div element
    """
    return Div(js(js_code), classes=classes, props=props)
