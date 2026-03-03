"""
MCP (Model Context Protocol) DTO 定义
规范版本: 2025-06-18
参考: https://modelcontextprotocol.io/specification/2025-06-18
"""

from typing import Any, Literal

from pydantic import Field

from app.controller.dto_base import BaseDTO


# ---------------------------------------------------------------------------
# 通用注解类型
# ---------------------------------------------------------------------------


class Annotations(BaseDTO):
    """通用注解，用于 Resource、Content 等对象"""

    audience: list[Literal["user", "assistant"]] | None = Field(
        default=None,
        description="内容的目标受众，可选值为 'user' 和 'assistant'",
    )
    priority: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="内容的重要性，0.0 最低，1.0 最高",
    )
    lastModified: str | None = Field(
        default=None,
        description="最后修改时间，ISO 8601 格式，例如 '2025-01-12T15:00:58Z'",
    )


# ---------------------------------------------------------------------------
# Tool（工具）相关类型
# ---------------------------------------------------------------------------


class ToolAnnotations(BaseDTO):
    """工具行为注解，用于向客户端描述工具的副作用等特性"""

    title: str | None = Field(default=None, description="工具的显示标题")
    readOnlyHint: bool | None = Field(
        default=None,
        description="为 True 时表示工具不会修改环境（只读）",
    )
    destructiveHint: bool | None = Field(
        default=None,
        description="为 True 时表示工具可能执行破坏性操作（如删除数据），默认为 True",
    )
    idempotentHint: bool | None = Field(
        default=None,
        description="为 True 时表示使用相同参数重复调用结果相同，默认为 False",
    )
    openWorldHint: bool | None = Field(
        default=None,
        description="为 True 时表示工具可能与外部实体交互，默认为 True",
    )


class ToolInputSchema(BaseDTO):
    """工具输入参数的 JSON Schema（object 类型）"""

    type: Literal["object"] = "object"
    properties: dict[str, Any] | None = Field(
        default=None,
        description="参数属性定义，key 为参数名，value 为对应的 JSON Schema",
    )
    required: list[str] | None = Field(
        default=None,
        description="必填参数名称列表",
    )


class ToolInfoDTO(BaseDTO):
    """工具定义（对应 MCP Tool 类型）"""

    name: str = Field(description="工具的唯一标识符")
    title: str | None = Field(default=None, description="用于展示的可读标题")
    description: str | None = Field(default=None, description="工具功能的可读描述")
    inputSchema: ToolInputSchema = Field(
        default_factory=ToolInputSchema,
        description="工具输入参数的 JSON Schema",
    )
    outputSchema: dict[str, Any] | None = Field(
        default=None,
        description="工具输出的 JSON Schema（可选）",
    )
    annotations: ToolAnnotations | None = Field(
        default=None,
        description="描述工具行为的可选注解，客户端不应无条件信任",
    )


# ---------------------------------------------------------------------------
# Tool Result 内容类型
# ---------------------------------------------------------------------------


class TextContent(BaseDTO):
    """文本内容"""

    type: Literal["text"] = "text"
    text: str
    annotations: Annotations | None = None


class ImageContent(BaseDTO):
    """图片内容（Base64 编码）"""

    type: Literal["image"] = "image"
    data: str = Field(description="Base64 编码的图片数据")
    mimeType: str = Field(description="图片 MIME 类型，例如 'image/png'")
    annotations: Annotations | None = None


class AudioContent(BaseDTO):
    """音频内容（Base64 编码）"""

    type: Literal["audio"] = "audio"
    data: str = Field(description="Base64 编码的音频数据")
    mimeType: str = Field(description="音频 MIME 类型，例如 'audio/wav'")
    annotations: Annotations | None = None


class ResourceLink(BaseDTO):
    """资源链接，指向一个可订阅/读取的 Resource URI"""

    type: Literal["resource_link"] = "resource_link"
    uri: str = Field(description="资源的 URI")
    name: str | None = Field(default=None, description="资源名称")
    description: str | None = Field(default=None, description="资源描述")
    mimeType: str | None = Field(default=None, description="资源 MIME 类型")
    annotations: Annotations | None = None


class EmbeddedResourceContent(BaseDTO):
    """内嵌资源的具体内容（文本或二进制）"""

    uri: str
    mimeType: str | None = None
    text: str | None = Field(default=None, description="文本内容（文本资源）")
    blob: str | None = Field(default=None, description="Base64 编码的二进制内容（二进制资源）")
    annotations: Annotations | None = None


class EmbeddedResource(BaseDTO):
    """内嵌资源，将 Resource 作为内容嵌入到工具结果中"""

    type: Literal["resource"] = "resource"
    resource: EmbeddedResourceContent
    annotations: Annotations | None = None


# 工具结果内容联合类型
ToolContent = TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource


# ---------------------------------------------------------------------------
# Tool 调用请求/响应 DTO
# ---------------------------------------------------------------------------


class ToolExecuteReqDTO(BaseDTO):
    """执行工具请求 DTO（对应 tools/call 请求中的 params）"""

    name: str = Field(description="要调用的工具名称")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="工具的调用参数，key 为参数名，value 为参数值",
    )


class ToolExecuteResDTO(BaseDTO):
    """执行工具响应 DTO（对应 tools/call 响应中的 result）"""

    content: list[ToolContent] = Field(
        default_factory=list,
        description="工具返回的内容列表，支持文本、图片、音频、资源链接等类型",
    )
    structuredContent: dict[str, Any] | None = Field(
        default=None,
        description="结构化输出（JSON 对象，需与 outputSchema 匹配）",
    )
    isError: bool = Field(
        default=False,
        description="为 True 时表示工具执行过程中发生错误",
    )


class ToolListResDTO(BaseDTO):
    """工具列表响应 DTO（对应 tools/list 响应中的 result）"""

    tools: list[ToolInfoDTO] = Field(default_factory=list)
    nextCursor: str | None = Field(default=None, description="分页游标")


# ---------------------------------------------------------------------------
# Resource（资源）相关类型
# ---------------------------------------------------------------------------


class ResourceDTO(BaseDTO):
    """Resource 定义（对应 MCP Resource 类型）"""

    uri: str = Field(description="资源的唯一 URI 标识符")
    name: str = Field(description="资源名称")
    title: str | None = Field(default=None, description="用于展示的可读标题")
    description: str | None = Field(default=None, description="资源描述")
    mimeType: str | None = Field(default=None, description="资源 MIME 类型")
    size: int | None = Field(default=None, description="资源大小（字节）")
    annotations: Annotations | None = None


class ResourceTemplateDTO(BaseDTO):
    """Resource Template 定义，使用 URI 模板描述参数化资源"""

    uriTemplate: str = Field(description="URI 模板，遵循 RFC 6570")
    name: str = Field(description="模板名称")
    title: str | None = Field(default=None, description="用于展示的可读标题")
    description: str | None = Field(default=None, description="模板描述")
    mimeType: str | None = Field(default=None, description="资源 MIME 类型")
    annotations: Annotations | None = None


class ResourceContentsDTO(BaseDTO):
    """Resource 内容（文本或二进制二选一）"""

    uri: str
    mimeType: str | None = None
    text: str | None = Field(default=None, description="文本内容（文本资源使用）")
    blob: str | None = Field(default=None, description="Base64 编码的二进制内容（二进制资源使用）")


class ResourceReadResDTO(BaseDTO):
    """读取资源响应 DTO（对应 resources/read 响应中的 result）"""

    contents: list[ResourceContentsDTO] = Field(default_factory=list)


class ResourceListResDTO(BaseDTO):
    """资源列表响应 DTO（对应 resources/list 响应中的 result）"""

    resources: list[ResourceDTO] = Field(default_factory=list)
    nextCursor: str | None = Field(default=None, description="分页游标")


class ResourceTemplateListResDTO(BaseDTO):
    """资源模板列表响应 DTO（对应 resources/templates/list 响应中的 result）"""

    resourceTemplates: list[ResourceTemplateDTO] = Field(default_factory=list)
    nextCursor: str | None = Field(default=None, description="分页游标")


# ---------------------------------------------------------------------------
# Prompt（提示词）相关类型
# ---------------------------------------------------------------------------


class PromptArgument(BaseDTO):
    """Prompt 参数定义"""

    name: str = Field(description="参数名称")
    description: str | None = Field(default=None, description="参数描述")
    required: bool | None = Field(default=None, description="是否为必填参数")


class PromptInfoDTO(BaseDTO):
    """Prompt 定义（对应 MCP Prompt 类型）"""

    name: str = Field(description="Prompt 的唯一标识符")
    title: str | None = Field(default=None, description="用于展示的可读标题")
    description: str | None = Field(default=None, description="Prompt 的描述")
    arguments: list[PromptArgument] | None = Field(
        default=None,
        description="Prompt 支持的参数列表",
    )


class PromptMessageContent(BaseDTO):
    """Prompt 消息内容（文本或嵌入资源）"""

    type: Literal["text", "image", "audio", "resource"]
    text: str | None = None
    data: str | None = Field(default=None, description="Base64 编码的图片/音频数据")
    mimeType: str | None = None
    resource: EmbeddedResourceContent | None = None


class PromptMessageDTO(BaseDTO):
    """Prompt 消息（角色 + 内容）"""

    role: Literal["user", "assistant"] = Field(description="消息角色")
    content: PromptMessageContent = Field(description="消息内容")


class PromptGetReqDTO(BaseDTO):
    """获取 Prompt 请求 DTO（对应 prompts/get 请求中的 params）"""

    name: str = Field(description="Prompt 名称")
    arguments: dict[str, str] | None = Field(
        default=None,
        description="传入 Prompt 的参数，key 为参数名，value 为字符串值",
    )


class PromptGetResDTO(BaseDTO):
    """获取 Prompt 响应 DTO（对应 prompts/get 响应中的 result）"""

    description: str | None = Field(default=None, description="Prompt 描述")
    messages: list[PromptMessageDTO] = Field(
        default_factory=list,
        description="生成的消息列表",
    )


class PromptListResDTO(BaseDTO):
    """Prompt 列表响应 DTO（对应 prompts/list 响应中的 result）"""

    prompts: list[PromptInfoDTO] = Field(default_factory=list)
    nextCursor: str | None = Field(default=None, description="分页游标")
