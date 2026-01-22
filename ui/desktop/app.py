import webview

html = """
<!doctype html>
<html><body><h1>pywebview 示例</h1><button onclick="window.pywebview.api.ping()">Ping</button></body></html>
"""


class JsApi:
    def ping(self):
        print("ping from JS")
        return "pong"


# 启动后台服务
def start_backend():
    print("后台服务已启动")


start_backend()

webview.create_window("UzonCalc", html=html, js_api=JsApi())
webview.start()


# 关闭后台服务
def close_backend():
    print("后台服务已关闭")


close_backend()
