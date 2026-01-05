"""
HTML template for rendering calculation sheets with LaTeX support.
"""


def get_html_template(content: str) -> str:
    """
    Generate HTML template with user-provided content and LaTeX rendering support.

    Args:
        content: The main content to be inserted into the template.

    Returns:
        Complete HTML string.
    """
    html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UzonCalc Calculation Sheet</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }
        .content {
            max-width: 800px;
            margin: 0 auto;
        }
        .latex {
            font-size: 1.2em;
        }
    </style>
    <!-- MathJax for LaTeX rendering -->
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
    <div class="content">
        <p>{content}</p> 
    </div>
</body>
</html>
"""
    return html_template.replace(r"{content}", content)
