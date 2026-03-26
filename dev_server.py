"""
简易 FastAPI 开发服务器，用于预览 HTML 文件
"""

import os
import argparse
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

app = FastAPI(title="HTML Preview Server")

# 全局变量存储根目录
ROOT_DIR = None

# 排除的目录
EXCLUDE_DIRS = {".venv", "node_modules", "__pycache__", ".git", ".pytest_cache"}


@app.get("/")
async def root(q: str = Query("", description="搜索文件")):
    """根路径显示可用文件列表，支持搜索过滤"""
    if ROOT_DIR is None:
        raise HTTPException(status_code=500, detail="Root directory not set")

    html_files = []
    for root, dirs, files in os.walk(ROOT_DIR):
        # 过滤排除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for f in files:
            if f.endswith(".html"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, ROOT_DIR)

                # 搜索过滤
                if q and q.lower() not in rel_path.lower():
                    continue

                html_files.append(
                    f'<li><a href="/preview/{rel_path}">{rel_path}</a></li>'
                )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HTML Preview Server</title>
        <style>
            :root {{
                --primary: #867cf0;
                --secondary: #42b883;
                --bg-1: #f7f8ff;
                --bg-2: #ffffff;
                --text-main: #1f2430;
                --text-sub: #5c6273;
                --line: rgba(134, 124, 240, 0.18);
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
                background:
                    radial-gradient(1000px 520px at 8% 0%, rgba(134, 124, 240, 0.2) 0%, rgba(134, 124, 240, 0) 55%),
                    radial-gradient(860px 460px at 100% 100%, rgba(66, 184, 131, 0.17) 0%, rgba(66, 184, 131, 0) 60%),
                    linear-gradient(180deg, var(--bg-1) 0%, #f3f5fb 100%);
                min-height: 100vh;
                padding: 40px 20px;
                color: var(--text-main);
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                color: #7f88f4;
                margin-bottom: 40px;
            }}
            .header h1 {{
                font-size: 2.5rem;
                font-weight: 300;
                margin-bottom: 8px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header p {{
                font-size: 0.95rem;
                opacity: 0.85;
                background: rgba(255,255,255,0.15);
                display: inline-block;
                padding: 6px 16px;
                border-radius: 20px;
                word-break: break-all;
                max-width: 100%;
            }}
            .search-box {{
                background: white;
                border-radius: 16px;
                padding: 8px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                margin-bottom: 30px;
            }}
            .search-box form {{
                display: flex;
                align-items: center;
            }}
            .search-box input {{
                flex: 1;
                border: none;
                outline: none;
                padding: 16px 20px;
                font-size: 1rem;
                color: #333;
                background: transparent;
            }}
            .search-box input::placeholder {{
                color: #999;
            }}
            .search-box button {{
                background: linear-gradient(135deg, var(--primary) 0%, #7f88f4 48%, var(--secondary) 100%);
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 10px;
                font-size: 0.95rem;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .search-box button:hover {{
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(134, 124, 240, 0.35);
            }}
            .card {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                overflow: hidden;
            }}
            .card-header {{
                padding: 20px 24px;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .card-header h2 {{
                font-size: 1.1rem;
                font-weight: 600;
                color: #333;
            }}
            .count {{
                background: linear-gradient(135deg, var(--primary) 0%, #7f88f4 48%, var(--secondary) 100%);
                color: white;
                padding: 4px 14px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 500;
            }}
            .file-list {{
                padding: 16px 24px 24px;
                columns: 2;
                column-gap: 16px;
            }}
            .file-list li {{
                list-style: none;
                margin-bottom: 10px;
                break-inside: avoid;
            }}
            .file-list a {{
                display: flex;
                align-items: center;
                padding: 12px 16px;
                background: #f8f9fa;
                border-radius: 10px;
                color: #555;
                text-decoration: none;
                font-size: 0.9rem;
                transition: all 0.2s;
                border: 1px solid transparent;
            }}
            .file-list a:hover {{
                background: linear-gradient(135deg, rgba(134,124,240,0.1) 0%, rgba(66,184,131,0.1) 100%);
                border-color: rgba(134, 124, 240, 0.3);
                color: var(--primary);
                transform: translateX(4px);
            }}
            .file-icon {{
                margin-right: 10px;
                font-size: 1.1rem;
            }}
            .empty {{
                text-align: center;
                padding: 60px 20px;
                color: #999;
            }}
            .empty-icon {{
                font-size: 3rem;
                margin-bottom: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>HTML Preview Server</h1>
                <p>{ROOT_DIR}</p>
            </div>
            <div class="search-box">
                <form method="get">
                    <input type="text" name="q" placeholder="搜索 HTML 文件..." value="{q}" autofocus>
                    <button type="submit">搜索</button>
                </form>
            </div>
            <div class="card">
                <div class="card-header">
                    <h2>可用文件</h2>
                    <span class="count">{len(html_files)} 个文件</span>
                </div>
                <ul class="file-list">
                    {"".join(html_files) if html_files else '<div class="empty"><div class="empty-icon">📭</div><p>没有找到 HTML 文件</p></div>'}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/preview/{file_path:path}")
async def preview_html(file_path: str):
    """预览指定路径的 HTML 文件"""
    if ROOT_DIR is None:
        raise HTTPException(status_code=500, detail="Root directory not set")

    file_full_path = os.path.join(ROOT_DIR, file_path)

    # 检查是否在排除目录中
    normalized_path = os.path.normpath(file_full_path)
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in normalized_path.split(os.sep):
            raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(file_full_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    if not file_full_path.endswith(".html"):
        raise HTTPException(status_code=400, detail="Only HTML files are supported")

    return FileResponse(file_full_path)


@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """提供静态文件服务（CSS, JS, 图片等）"""
    if ROOT_DIR is None:
        raise HTTPException(status_code=500, detail="Root directory not set")

    file_full_path = os.path.join(ROOT_DIR, file_path)

    if not os.path.exists(file_full_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    return FileResponse(file_full_path)


def main():
    parser = argparse.ArgumentParser(description="HTML Preview Server")
    parser.add_argument(
        "-r",
        "--root",
        default=".",
        help="Root directory to serve (default: current directory)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )

    args = parser.parse_args()

    global ROOT_DIR
    ROOT_DIR = os.path.abspath(args.root)

    if not os.path.isdir(ROOT_DIR):
        print(f"Error: {ROOT_DIR} is not a directory")
        return

    print(f"Serving HTML files from: {ROOT_DIR}")
    print(f"Access at: http://{args.host}:{args.port}")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
