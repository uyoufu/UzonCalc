# 判断数据库
from typing import Callable
from fastapi import FastAPI
from config.config import app_config


def combine_lifespans(main_lifespan: Callable):
    """
    Combine the lifespans of the main application and the MCP application.

    :param main_lifespan: The lifespan function of the main application.
    :return: A combined lifespan function if MCP is enabled, otherwise the main lifespan function.
    """
    if not app_config.mcp_enabled:
        return main_lifespan

    from app.mcp.mcp_app import mcp_app
    from fastmcp.utilities.lifespan import (
        combine_lifespans as fastmcp_combine_lifespans,
    )

    return fastmcp_combine_lifespans(main_lifespan, mcp_app.lifespan)


def mount_mcp(app: FastAPI):
    """
    Mount the MCP application to the main FastAPI app if MCP is enabled in the configuration.
    """
    if not app_config.mcp_enabled:
        return

    from app.mcp.mcp_app import mcp_app

    app.mount("/engineer", mcp_app)
