"""
用户输入历史数据库模型

用于保存用户的输入数据和已发布版本。
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    Boolean,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class UserInputHistory(Base):
    """用户输入历史"""

    __tablename__ = "user_input_history"
    __table_args__ = (
        Index("idx_user_file_func", "userId", "filePath", "funcName"),
        Index("idx_user_created_at", "userId", "createdAt"),
        UniqueConstraint(
            "userId", "filePath", "funcName", "sessionId", name="uq_user_execution"
        ),
    )

    id = Column(Integer, primary_key=True)
    userId = Column(String(64), nullable=False, comment="用户 ID")
    filePath = Column(String(256), nullable=False, comment="计算文件路径")
    funcName = Column(String(128), nullable=False, comment="函数名称")
    sessionId = Column(String(64), nullable=False, comment="执行会话 ID")

    # 输入数据和步骤
    inputHistory = Column(JSON, default=[], comment="分步输入数据列表")
    currentStep = Column(Integer, default=0, comment="当前执行步骤")
    totalSteps = Column(Integer, default=0, comment="总步骤数")

    # 最终结果
    finalResult = Column(Text, nullable=True, comment="最终 HTML 结果")
    finalResultHash = Column(
        String(64), nullable=True, comment="结果哈希，用于快速比对"
    )

    # 版本控制
    isComplete = Column(Boolean, default=False, comment="是否已完全执行完成")
    isDraft = Column(Boolean, default=True, comment="是否是草稿（未发布）")
    draftVersionId = Column(Integer, nullable=True, comment="关联的草稿版本 ID")

    # 元数据
    parameters = Column(JSON, nullable=True, comment="初始参数")
    executionTime = Column(Integer, nullable=True, comment="执行耗时（毫秒）")
    errorMessage = Column(Text, nullable=True, comment="错误信息")

    # 时间戳
    createdAt = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updatedAt = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )
    completedAt = Column(DateTime, nullable=True, comment="完成时间")

    def __repr__(self):
        return f"<UserInputHistory(user={self.userId}, file={self.filePath}, func={self.funcName}, session={self.sessionId})>"


class PublishedVersion(Base):
    """已发布的版本（快照）"""

    __tablename__ = "published_version"
    __table_args__ = (
        Index("idx_user_published", "userId", "publishedAt"),
        Index("idx_file_version", "filePath", "funcName", "versionNumber"),
    )

    id = Column(Integer, primary_key=True)
    userId = Column(String(64), nullable=False, comment="用户 ID")
    filePath = Column(String(256), nullable=False, comment="计算文件路径")
    funcName = Column(String(128), nullable=False, comment="函数名称")

    # 版本信息
    versionName = Column(String(128), nullable=False, comment="版本名称")
    versionNumber = Column(Integer, default=1, comment="版本号")
    versionDescription = Column(Text, nullable=True, comment="版本描述")

    # 完整的执行快照
    inputHistory = Column(JSON, nullable=False, comment="完整的输入历史")
    finalResult = Column(Text, nullable=False, comment="最终 HTML 结果")
    finalResultHash = Column(String(64), nullable=False, comment="结果哈希")

    # 参数和元数据
    parameters = Column(JSON, nullable=True, comment="初始参数")
    totalSteps = Column(Integer, nullable=False, comment="总步骤数")
    executionTime = Column(Integer, nullable=True, comment="执行耗时（毫秒）")

    # 时间戳
    createdAt = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    publishedAt = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="发布时间"
    )
    createdFromHistoryId = Column(Integer, nullable=True, comment="创建自的历史记录 ID")

    # 统计
    downloadCount = Column(Integer, default=0, comment="下载次数")
    useCount = Column(Integer, default=0, comment="使用次数")
    isPublic = Column(Boolean, default=False, comment="是否公开")

    def __repr__(self):
        return f"<PublishedVersion(user={self.userId}, file={self.filePath}, version={self.versionName})>"


class InputCache(Base):
    """输入缓存（用于快速加载最近的输入）"""

    __tablename__ = "input_cache"
    __table_args__ = (
        Index("idx_cache_user_file", "userId", "filePath", "funcName"),
    )

    id = Column(Integer, primary_key=True)
    userId = Column(String(64), nullable=False, comment="用户 ID")
    filePath = Column(String(256), nullable=False, comment="计算文件路径")
    funcName = Column(String(128), nullable=False, comment="函数名称")

    # 缓存的输入数据
    cachedInput = Column(JSON, nullable=False, comment="最后一次的输入数据快照")
    inputHistoryId = Column(Integer, nullable=False, comment="来自的历史记录 ID")

    # 缓存元数据
    totalSteps = Column(Integer, nullable=False, comment="当时的总步骤数")
    completedSteps = Column(Integer, nullable=False, comment="已完成的步骤数")

    # 时间戳
    createdAt = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updatedAt = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )
    expiresAt = Column(DateTime, nullable=True, comment="过期时间")

    def __repr__(self):
        return f"<InputCache(user={self.userId}, file={self.filePath}, func={self.funcName})>"
