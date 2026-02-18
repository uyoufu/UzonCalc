"""
Service Manager for UzonCalc Desktop Application

管理桌面应用的后台服务，包括启动、停止和状态检查
"""

import os
import sys
import time
import socket
import subprocess
import psutil
from pathlib import Path
from typing import Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceConfig:
    """服务配置类 - 集中管理所有配置参数"""
    
    def __init__(self):
        # 获取项目根目录
        self.desktop_dir = Path(__file__).resolve().parent
        self.api_dir = self.desktop_dir.parent / "api"
        self.api_main = self.api_dir / "main.py"
        
        # API 服务配置
        self.api_host = "localhost"
        self.api_port = 3345
        
        # 服务启动配置
        self.startup_timeout = 30  # 启动超时时间（秒）- 增加到30秒
        self.shutdown_timeout = 5  # 关闭超时时间（秒）
        self.health_check_interval = 0.5  # 健康检查间隔（秒）
        
        # 日志配置
        self.log_dir = self.desktop_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.api_log_file = self.log_dir / "api_service.log"
        
    def validate(self) -> bool:
        """验证配置的有效性"""
        if not self.api_main.exists():
            logger.error(f"API main file not found: {self.api_main}")
            return False
        return True


class PortChecker:
    """端口检查器 - 负责端口相关的检查操作"""
    
    @staticmethod
    def is_port_in_use(host: str, port: int) -> bool:
        """
        检查端口是否被占用
        
        Args:
            host: 主机地址
            port: 端口号
            
        Returns:
            bool: 端口是否被占用
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect((host, port))
                return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                return False
    
    @staticmethod
    def find_process_by_port(port: int) -> Optional[psutil.Process]:
        """
        查找占用指定端口的进程
        
        Args:
            port: 端口号
            
        Returns:
            Optional[psutil.Process]: 占用端口的进程，如果没有则返回 None
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.connections()
                    for conn in connections:
                        if conn.laddr.port == port:
                            return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"Error finding process by port: {e}")
        return None


class ProcessManager:
    """进程管理器 - 负责进程的启动、停止和监控"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.log_file = None
        
    def start_process(self) -> bool:
        """
        启动 API 服务进程
        
        Returns:
            bool: 启动是否成功
        """
        try:
            # 切换到 API 目录
            logger.info(f"Starting API service from: {self.config.api_dir}")
            
            # 构建启动命令
            python_executable = sys.executable
            cmd = [python_executable, str(self.config.api_main)]
            
            # 打开日志文件
            self.log_file = open(self.config.api_log_file, 'w', encoding='utf-8')
            logger.info(f"API service logs will be written to: {self.config.api_log_file}")
            
            # 启动进程（Windows 下隐藏控制台窗口）
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.config.api_dir),
                stdout=self.log_file,
                stderr=subprocess.STDOUT,  # 将 stderr 重定向到 stdout
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            logger.info(f"API service process started with PID: {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start API service: {e}")
            if self.log_file:
                self.log_file.close()
                self.log_file = None
            return False
    
    def stop_process(self) -> bool:
        """
        停止 API 服务进程
        
        Returns:
            bool: 停止是否成功
        """
        if self.process is None:
            logger.warning("No process to stop")
            return True
        
        try:
            logger.info(f"Stopping API service process (PID: {self.process.pid})")
            
            # 尝试优雅关闭
            self.process.terminate()
            
            # 等待进程结束
            try:
                self.process.wait(timeout=self.config.shutdown_timeout)
                logger.info("API service stopped gracefully")
            except subprocess.TimeoutExpired:
                # 如果超时，强制杀死进程
                logger.warning("Process did not terminate gracefully, forcing kill")
                self.process.kill()
                self.process.wait()
                logger.info("API service killed forcefully")
            
            # 关闭日志文件
            if self.log_file:
                self.log_file.close()
                self.log_file = None
            
            self.process = None
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop API service: {e}")
            return False
    
    def is_process_alive(self) -> bool:
        """
        检查进程是否存活
        
        Returns:
            bool: 进程是否存活
        """
        if self.process is None:
            return False
        return self.process.poll() is None


class ServiceManager:
    """
    服务管理器 - 主要的服务管理类
    
    提供统一的接口来管理 API 服务的生命周期
    """
    
    def __init__(self):
        self.config = ServiceConfig()
        self.port_checker = PortChecker()
        self.process_manager = ProcessManager(self.config)
        
        # 验证配置
        if not self.config.validate():
            raise RuntimeError("Invalid service configuration")
    
    def start(self) -> bool:
        """
        启动 API 服务
        
        如果服务已在运行，则先停止再启动
        
        Returns:
            bool: 启动是否成功
        """
        logger.info("=" * 60)
        logger.info("Starting API Service")
        logger.info("=" * 60)
        
        # 检查端口是否被占用
        if self.port_checker.is_port_in_use(self.config.api_host, self.config.api_port):
            logger.info(f"Port {self.config.api_port} is already in use, stopping existing service...")
            self._stop_existing_service()
        
        # 启动新进程
        if not self.process_manager.start_process():
            return False
        
        # 等待服务启动
        if not self._wait_for_service_ready():
            logger.error("Service failed to start within timeout period")
            self.stop()
            return False
        
        logger.info("API Service started successfully")
        logger.info("=" * 60)
        return True
    
    def stop(self) -> bool:
        """
        停止 API 服务
        
        Returns:
            bool: 停止是否成功
        """
        logger.info("=" * 60)
        logger.info("Stopping API Service")
        logger.info("=" * 60)
        
        success = self.process_manager.stop_process()
        
        # 等待端口释放
        self._wait_for_port_release()
        
        if success:
            logger.info("API Service stopped successfully")
        else:
            logger.error("Failed to stop API Service")
        
        logger.info("=" * 60)
        return success
    
    def restart(self) -> bool:
        """
        重启 API 服务
        
        Returns:
            bool: 重启是否成功
        """
        logger.info("Restarting API Service")
        self.stop()
        time.sleep(1)  # 给一点时间让端口完全释放
        return self.start()
    
    def is_running(self) -> bool:
        """
        检查 API 服务是否正在运行
        
        同时检查进程状态和端口状态
        
        Returns:
            bool: 服务是否正在运行
        """
        # 检查进程是否存活
        process_alive = self.process_manager.is_process_alive()
        
        # 检查端口是否可用
        port_in_use = self.port_checker.is_port_in_use(
            self.config.api_host, 
            self.config.api_port
        )
        
        # 两者都为真才认为服务正在运行
        return process_alive and port_in_use
    
    def get_status(self) -> dict:
        """
        获取服务状态信息
        
        Returns:
            dict: 包含详细状态信息的字典
        """
        process_alive = self.process_manager.is_process_alive()
        port_in_use = self.port_checker.is_port_in_use(
            self.config.api_host, 
            self.config.api_port
        )
        
        return {
            "running": process_alive and port_in_use,
            "process_alive": process_alive,
            "port_in_use": port_in_use,
            "pid": self.process_manager.process.pid if self.process_manager.process else None,
            "host": self.config.api_host,
            "port": self.config.api_port,
        }
    
    def cleanup(self):
        """清理资源，确保服务被正确关闭"""
        logger.info("Cleaning up service manager")
        self.stop()
    
    def _stop_existing_service(self):
        """停止已存在的服务"""
        # 先尝试查找并停止占用端口的进程
        existing_process = self.port_checker.find_process_by_port(self.config.api_port)
        if existing_process:
            try:
                logger.info(f"Found existing process (PID: {existing_process.pid}), terminating...")
                existing_process.terminate()
                existing_process.wait(timeout=self.config.shutdown_timeout)
                logger.info("Existing process terminated")
            except psutil.TimeoutExpired:
                logger.warning("Existing process did not terminate, killing...")
                existing_process.kill()
            except Exception as e:
                logger.error(f"Error stopping existing process: {e}")
        
        # 等待端口释放
        self._wait_for_port_release()
    
    def _wait_for_service_ready(self) -> bool:
        """
        等待服务就绪
        
        Returns:
            bool: 服务是否就绪
        """
        logger.info("Waiting for service to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < self.config.startup_timeout:
            # 检查进程是否还活着
            if not self.process_manager.is_process_alive():
                logger.error("Process died unexpectedly")
                self._print_service_log()
                return False
            
            # 检查端口是否可用
            if self.port_checker.is_port_in_use(self.config.api_host, self.config.api_port):
                logger.info("Service is ready")
                return True
            
            time.sleep(self.config.health_check_interval)
        
        # 超时，打印日志帮助诊断
        logger.error("Service startup timeout")
        self._print_service_log()
        return False
    
    def _print_service_log(self):
        """打印服务日志（用于诊断）"""
        try:
            if self.config.api_log_file.exists():
                logger.info("=" * 60)
                logger.info("API Service Log Output:")
                logger.info("=" * 60)
                with open(self.config.api_log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                    # 只打印最后 2000 字符，避免过长
                    if len(log_content) > 2000:
                        log_content = "..." + log_content[-2000:]
                    for line in log_content.splitlines():
                        logger.error(f"  {line}")
                logger.info("=" * 60)
        except Exception as e:
            logger.warning(f"Failed to read service log: {e}")
    
    def _wait_for_port_release(self):
        """等待端口释放"""
        logger.info("Waiting for port to be released...")
        start_time = time.time()
        
        while time.time() - start_time < self.config.shutdown_timeout:
            if not self.port_checker.is_port_in_use(self.config.api_host, self.config.api_port):
                logger.info("Port released")
                return
            time.sleep(0.1)
        
        logger.warning("Port may still be in use after timeout")


# 全局服务管理器实例
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """
    获取全局服务管理器实例（单例模式）
    
    Returns:
        ServiceManager: 服务管理器实例
    """
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager


def start_service() -> bool:
    """
    启动服务的便捷函数
    
    Returns:
        bool: 启动是否成功
    """
    return get_service_manager().start()


def stop_service() -> bool:
    """
    停止服务的便捷函数
    
    Returns:
        bool: 停止是否成功
    """
    return get_service_manager().stop()


def is_service_running() -> bool:
    """
    检查服务是否运行的便捷函数
    
    Returns:
        bool: 服务是否正在运行
    """
    return get_service_manager().is_running()


def get_service_status() -> dict:
    """
    获取服务状态的便捷函数
    
    Returns:
        dict: 服务状态信息
    """
    return get_service_manager().get_status()


if __name__ == "__main__":
    # 用于测试
    manager = ServiceManager()
    
    try:
        # 启动服务
        if manager.start():
            print("Service started successfully")
            
            # 等待一段时间
            time.sleep(5)
            
            # 检查状态
            status = manager.get_status()
            print(f"Service status: {status}")
            
        else:
            print("Failed to start service")
    
    finally:
        # 清理
        manager.cleanup()
