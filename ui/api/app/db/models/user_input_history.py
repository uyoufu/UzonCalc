"""
用户输入历史数据库模型

用于保存用户的输入数据和已发布版本。
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class UserInputHistory(Base):
    """用户输入历史"""
    __tablename__ = 'user_input_history'
    __table_args__ = (
        Index('idx_user_file_func', 'user_id', 'file_path', 'func_name'),
        Index('idx_user_created_at', 'user_id', 'created_at'),
        UniqueConstraint('user_id', 'file_path', 'func_name', 'session_id', name='uq_user_execution'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False, comment='用户 ID')
    file_path = Column(String(256), nullable=False, comment='计算文件路径')
    func_name = Column(String(128), nullable=False, comment='函数名称')
    session_id = Column(String(64), nullable=False, comment='执行会话 ID')
    
    # 输入数据和步骤
    input_history = Column(JSON, default=[], comment='分步输入数据列表')
    current_step = Column(Integer, default=0, comment='当前执行步骤')
    total_steps = Column(Integer, default=0, comment='总步骤数')
    
    # 最终结果
    final_result = Column(Text, nullable=True, comment='最终 HTML 结果')
    final_result_hash = Column(String(64), nullable=True, comment='结果哈希，用于快速比对')
    
    # 版本控制
    is_complete = Column(Boolean, default=False, comment='是否已完全执行完成')
    is_draft = Column(Boolean, default=True, comment='是否是草稿（未发布）')
    draft_version_id = Column(Integer, nullable=True, comment='关联的草稿版本 ID')
    
    # 元数据
    parameters = Column(JSON, nullable=True, comment='初始参数')
    execution_time = Column(Integer, nullable=True, comment='执行耗时（毫秒）')
    error_message = Column(Text, nullable=True, comment='错误信息')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='更新时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    
    def __repr__(self):
        return f"<UserInputHistory(user={self.user_id}, file={self.file_path}, func={self.func_name}, session={self.session_id})>"


class PublishedVersion(Base):
    """已发布的版本（快照）"""
    __tablename__ = 'published_version'
    __table_args__ = (
        Index('idx_user_published', 'user_id', 'published_at'),
        Index('idx_file_version', 'file_path', 'func_name', 'version_number'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False, comment='用户 ID')
    file_path = Column(String(256), nullable=False, comment='计算文件路径')
    func_name = Column(String(128), nullable=False, comment='函数名称')
    
    # 版本信息
    version_name = Column(String(128), nullable=False, comment='版本名称')
    version_number = Column(Integer, default=1, comment='版本号')
    version_description = Column(Text, nullable=True, comment='版本描述')
    
    # 完整的执行快照
    input_history = Column(JSON, nullable=False, comment='完整的输入历史')
    final_result = Column(Text, nullable=False, comment='最终 HTML 结果')
    final_result_hash = Column(String(64), nullable=False, comment='结果哈希')
    
    # 参数和元数据
    parameters = Column(JSON, nullable=True, comment='初始参数')
    total_steps = Column(Integer, nullable=False, comment='总步骤数')
    execution_time = Column(Integer, nullable=True, comment='执行耗时（毫秒）')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='发布时间')
    created_from_history_id = Column(Integer, nullable=True, comment='创建自的历史记录 ID')
    
    # 统计
    download_count = Column(Integer, default=0, comment='下载次数')
    use_count = Column(Integer, default=0, comment='使用次数')
    is_public = Column(Boolean, default=False, comment='是否公开')
    
    def __repr__(self):
        return f"<PublishedVersion(user={self.user_id}, file={self.file_path}, version={self.version_name})>"


class InputCache(Base):
    """输入缓存（用于快速加载最近的输入）"""
    __tablename__ = 'input_cache'
    __table_args__ = (
        Index('idx_cache_user_file', 'user_id', 'file_path', 'func_name'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False, comment='用户 ID')
    file_path = Column(String(256), nullable=False, comment='计算文件路径')
    func_name = Column(String(128), nullable=False, comment='函数名称')
    
    # 缓存的输入数据
    cached_input = Column(JSON, nullable=False, comment='最后一次的输入数据快照')
    input_history_id = Column(Integer, nullable=False, comment='来自的历史记录 ID')
    
    # 缓存元数据
    total_steps = Column(Integer, nullable=False, comment='当时的总步骤数')
    completed_steps = Column(Integer, nullable=False, comment='已完成的步骤数')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='更新时间')
    expires_at = Column(DateTime, nullable=True, comment='过期时间')
    
    def __repr__(self):
        return f"<InputCache(user={self.user_id}, file={self.file_path}, func={self.func_name})>"
