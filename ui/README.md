# Development Document

## Directory Structure

1. `api` - Backend API
2. `web` - Frontend Web Application written in Vue
3. `desktop` - Desktop Application using webview


## Desktop Application

The desktop application is built using webview. When it starts, it performs the following steps:

1. Initialize the webview window.
2. Start the backend API server.
3. Load the frontend web application in the webview.