#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PowerShell GUI界面层
使用CustomTkinter实现单窗口多标签页设计，每个PowerShell会话对应一个标签页
"""

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional, Callable
import customtkinter as ctk
import logging
from datetime import datetime
import queue
import time


class PowerShellTerminalTab:
    """PowerShell终端标签页"""
    
    def __init__(self, session_id: str, working_dir: str = None):
        self.session_id = session_id
        self.working_dir = working_dir or "C:\\"
        self.tab_frame = None
        self.text_area = None
        self.input_entry = None
        self.command_callback = None
        self.close_callback = None
        self.logger = logging.getLogger(f"{__name__}.{session_id}")
        
    def create_tab_content(self, parent_frame):
        """创建标签页内容"""
        # 主框架 - 现代化深色风格
        main_frame = ctk.CTkFrame(
            parent_frame,
            fg_color=("#f5f5f5", "#2d2d2d"),  # 终端背景
            corner_radius=8
        )
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # 顶部信息框架 - 现代化样式
        info_frame = ctk.CTkFrame(
            main_frame,
            fg_color=("#e0e0e0", "#3a3a3a"),  # 信息栏背景
            corner_radius=6,
            height=40
        )
        info_frame.pack(fill="x", pady=(8, 12), padx=8)

        # 会话信息标签 - 调整字体大小
        info_label = ctk.CTkLabel(
            info_frame,
            text=f"会话: {self.session_id[:8]}... | 工作目录: {self.working_dir}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color=("#404040", "#cccccc")  # 深灰/浅灰文字
        )
        info_label.pack(side="left", padx=(15, 0), pady=8)

        # 关闭按钮 - 移除加粗
        close_button = ctk.CTkButton(
            info_frame,
            text="✕",
            width=32,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="normal"),
            fg_color="transparent",
            text_color=("#666666", "#999999"),  # 灰色文字
            hover_color=("#ff4444", "#ff4444"),  # 悬停时红色背景
            border_width=1,
            border_color=("#cccccc", "#555555"),  # 边框颜色
            corner_radius=6,
            command=self._on_close_tab
        )
        close_button.pack(side="right", padx=(0, 15), pady=6)
        
        # 输出显示区域 - 统一字体
        self.text_area = ctk.CTkTextbox(
            main_frame,
            height=380,
            font=ctk.CTkFont(family="Consolas", size=13, weight="normal"),
            wrap="word",
            fg_color=("#ffffff", "#1e1e1e"),  # 白色/深黑背景
            text_color=("#2d2d2d", "#f0f0f0"),  # 深色/浅色文字
            border_width=1,
            border_color=("#d0d0d0", "#404040"),  # 边框颜色
            corner_radius=6
        )
        self.text_area.pack(fill="both", expand=True, pady=(0, 12), padx=8)
        
        # 输入框架 - 现代化样式
        input_frame = ctk.CTkFrame(
            main_frame,
            fg_color=("#e8e8e8", "#333333"),  # 输入区背景
            corner_radius=6,
            height=50
        )
        input_frame.pack(fill="x", pady=(0, 8), padx=8)
        
        # 命令输入框 - 统一字体，移除图标
        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="输入PowerShell命令...",
            font=ctk.CTkFont(family="Consolas", size=13, weight="normal"),
            height=36,
            fg_color=("#ffffff", "#2a2a2a"),  # 输入框背景
            text_color=("#2d2d2d", "#f0f0f0"),  # 输入文字颜色
            placeholder_text_color=("#888888", "#666666"),  # 占位符颜色
            border_width=1,
            border_color=("#c0c0c0", "#505050"),  # 边框颜色
            corner_radius=6
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(12, 10), pady=7)
        
        # 执行按钮 - 移除加粗和图标
        execute_btn = ctk.CTkButton(
            input_frame,
            text="执行",
            command=self._on_execute_command,
            width=70,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            fg_color=("#0078d4", "#0078d4"),  # 蓝色背景
            hover_color=("#106ebe", "#106ebe"),  # 悬停颜色
            text_color=("#ffffff", "#ffffff"),  # 白色文字
            corner_radius=6
        )
        execute_btn.pack(side="right", padx=(0, 12), pady=7)
        
        # 绑定回车键
        self.input_entry.bind("<Return>", lambda e: self._on_execute_command())
        
        # 初始化输出 - 调整字体大小
        self._append_output(f"PowerShell 终端已启动\n会话ID: {self.session_id}\n工作目录: {self.working_dir}\n" + "="*50 + "\n")
        
        self.tab_frame = main_frame
        return main_frame
    
    def _on_execute_command(self):
        """执行命令回调"""
        command = self.input_entry.get().strip()
        if not command:
            return
        
        # 显示命令
        self._append_output(f"PS> {command}\n")
        
        # 清空输入框
        self.input_entry.delete(0, "end")
        
        # 调用命令回调
        if self.command_callback:
            self.command_callback(self.session_id, command)
    
    def _append_output(self, text: str):
        """追加输出文本"""
        if self.text_area:
            self.text_area.insert("end", text)
            self.text_area.see("end")
    
    def append_output(self, text: str):
        """外部调用的追加输出方法"""
        if self.tab_frame and self.text_area:
            # 确保在主线程中执行
            self.tab_frame.after(0, lambda: self._append_output(text))
    
    def set_command_callback(self, callback: Callable[[str, str], None]):
        """设置命令执行回调"""
        self.command_callback = callback

    def set_close_callback(self, callback: Callable[[str], None]):
        """设置关闭标签页回调"""
        self.close_callback = callback

    def _on_close_tab(self):
        """关闭标签页回调"""
        if self.close_callback:
            self.close_callback(self.session_id)
    
    def clear_output(self):
        """清空输出"""
        if self.text_area:
            self.text_area.delete("1.0", "end")
            self._append_output(f"输出已清空 - {datetime.now().strftime('%H:%M:%S')}\n" + "="*50 + "\n")


class PowerShellGUIManager:
    """PowerShell GUI管理器 - 单窗口多标签页设计，独立线程运行"""

    def __init__(self):
        self.main_window = None
        self.tab_view = None
        self.terminal_tabs: Dict[str, PowerShellTerminalTab] = {}
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)

        # 命令队列，用于线程间通信
        self.command_queue = queue.Queue()
        self.gui_thread = None
        self.is_running = False
        self.user_command_callback = None  # 用户命令执行回调

        # 设置CustomTkinter主题 - 现代化夜间风格
        ctk.set_appearance_mode("dark")  # 强制夜间模式
        ctk.set_default_color_theme("dark-blue")  # 深蓝色主题

        # 启动GUI线程
        self._start_gui_thread()

    def _start_gui_thread(self):
        """启动GUI线程"""
        if not self.gui_thread or not self.gui_thread.is_alive():
            self.gui_thread = threading.Thread(target=self._run_gui_loop, daemon=False)
            self.gui_thread.start()
            self.logger.info("GUI线程已启动")

    def _run_gui_loop(self):
        """在独立线程中运行GUI循环"""
        try:
            self.is_running = True
            self.initialize_main_window()

            # 启动命令处理定时器
            self._process_commands()

            # 运行主循环
            self.main_window.mainloop()

        except Exception as e:
            self.logger.error(f"GUI线程运行错误: {e}")
        finally:
            self.is_running = False

    def _process_commands(self):
        """处理命令队列"""
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                self._execute_command(command)
        except queue.Empty:
            pass
        except Exception as e:
            self.logger.error(f"处理命令时出错: {e}")

        # 每100ms检查一次命令队列
        if self.main_window and self.is_running:
            self.main_window.after(100, self._process_commands)

    def _execute_command(self, command):
        """执行GUI命令"""
        try:
            cmd_type = command.get("type")
            if cmd_type == "show_window":
                self._do_show_window()
            elif cmd_type == "add_tab":
                self._do_add_tab(command.get("session_id"), command.get("working_dir"))
            elif cmd_type == "remove_tab":
                self._do_remove_tab(command.get("session_id"))
            elif cmd_type == "close_tab_user":
                self._do_close_tab_user(command.get("session_id"))
            elif cmd_type == "update_output":
                self._do_update_output(command.get("session_id"), command.get("text"))
            elif cmd_type == "show_confirmation":
                # 确认对话框需要同步处理
                pass
        except Exception as e:
            self.logger.error(f"执行GUI命令失败: {e}")

    def update_terminal_output(self, session_id: str, text: str):
        """更新终端输出（通过命令队列）"""
        try:
            self.command_queue.put({
                "type": "update_output",
                "session_id": session_id,
                "text": text
            })
        except Exception as e:
            self.logger.error(f"发送更新输出命令失败: {e}")

    def _do_update_output(self, session_id: str, text: str):
        """实际更新输出的操作"""
        try:
            if session_id in self.terminal_tabs:
                terminal = self.terminal_tabs[session_id]
                terminal._append_output(text)
        except Exception as e:
            self.logger.error(f"更新终端输出失败: {e}")

    def initialize_main_window(self):
        """初始化主窗口"""
        if self.is_initialized:
            return
        
        # 创建主窗口 - 现代化夜间风格
        self.main_window = ctk.CTk()
        self.main_window.title("PowerShell MCP Manager")
        self.main_window.geometry("1000x700")

        # 设置窗口图标和样式
        self.main_window.configure(fg_color=("#f0f0f0", "#1a1a1a"))  # 浅色/深色背景
        
        # 创建主框架 - 现代化深色风格
        main_frame = ctk.CTkFrame(
            self.main_window,
            fg_color=("#e8e8e8", "#2b2b2b"),  # 浅灰/深灰背景
            corner_radius=10
        )
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        

        
        # 创建标签页视图 - 现代化深色风格
        self.tab_view = ctk.CTkTabview(
            main_frame,
            fg_color=("#d4d4d4", "#3c3c3c"),  # 标签页背景
            segmented_button_fg_color=("#c0c0c0", "#4a4a4a"),  # 标签按钮背景
            segmented_button_selected_color=("#0078d4", "#0078d4"),  # 选中标签颜色
            segmented_button_selected_hover_color=("#106ebe", "#106ebe"),  # 选中标签悬停
            text_color=("#2b2b2b", "#ffffff"),  # 标签文字颜色
            corner_radius=8
        )
        self.tab_view.pack(fill="both", expand=True, padx=5, pady=(10, 5))
        
        # 添加欢迎标签页
        welcome_tab = self.tab_view.add("欢迎")
        self._create_welcome_content(welcome_tab)
        
        self.is_initialized = True
        self.logger.info("PowerShell GUI Manager initialized")
    
    def _create_welcome_content(self, tab_frame):
        """创建欢迎页面内容"""
        welcome_frame = ctk.CTkFrame(
            tab_frame,
            fg_color=("#f8f8f8", "#2a2a2a"),  # 欢迎页背景
            corner_radius=10
        )
        welcome_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 欢迎信息
        welcome_text = """
🎯 PowerShell MCP 管理器

✨ 功能特性：
• 多会话管理：每个PowerShell会话对应一个标签页
• 实时交互：支持用户手动输入命令
• AI协作：AI可以通过MCP协议控制PowerShell
• 用户控制：AI查看输出需要用户确认

📋 使用说明：
1. AI调用ps_run命令时会自动创建新的终端标签页
2. 您可以在任意标签页中手动输入PowerShell命令
3. AI请求查看输出时会弹出确认对话框
4. 使用ps_close命令或手动关闭标签页来结束会话

🚀 开始使用：
等待AI调用PowerShell命令，或者手动创建新会话
        """
        
        info_label = ctk.CTkLabel(
            welcome_frame,
            text=welcome_text,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color=("#404040", "#e0e0e0"),  # 深灰/浅灰文字
            justify="left"
        )
        info_label.pack(pady=30)
    
    def show_main_window(self):
        """显示主窗口（通过命令队列）"""
        try:
            self.command_queue.put({"type": "show_window"})
        except Exception as e:
            self.logger.error(f"发送显示窗口命令失败: {e}")

    def _do_show_window(self):
        """实际显示窗口的操作"""
        try:
            if self.main_window:
                self.main_window.deiconify()
                self.main_window.lift()
                self.main_window.focus()
        except Exception as e:
            self.logger.error(f"显示主窗口失败: {e}")
    
    def add_terminal_tab(self, session_id: str, working_dir: str = None) -> PowerShellTerminalTab:
        """添加终端标签页（通过命令队列）"""
        try:
            self.command_queue.put({
                "type": "add_tab",
                "session_id": session_id,
                "working_dir": working_dir
            })
            self.logger.info(f"发送添加标签页命令: {session_id}")

            # 等待标签页创建完成（最多等待5秒）
            import time
            for _ in range(50):  # 50 * 0.1 = 5秒
                if session_id in self.terminal_tabs:
                    return self.terminal_tabs[session_id]
                time.sleep(0.1)

            self.logger.warning(f"标签页创建超时: {session_id}")
            return None
        except Exception as e:
            self.logger.error(f"发送添加标签页命令失败: {e}")
            return None

    def _do_add_tab(self, session_id: str, working_dir: str = None):
        """实际添加标签页的操作"""
        try:
            # 创建终端标签页
            terminal_tab = PowerShellTerminalTab(session_id, working_dir)

            # 设置命令回调
            terminal_tab.set_command_callback(self._handle_user_command)

            # 设置关闭回调
            terminal_tab.set_close_callback(self._handle_close_tab)

            # 添加到标签页视图
            tab_name = f"终端-{session_id[:8]}"
            tab_frame = self.tab_view.add(tab_name)
            terminal_tab.create_tab_content(tab_frame)

            # 存储引用
            self.terminal_tabs[session_id] = terminal_tab

            # 切换到新标签页
            self.tab_view.set(tab_name)

            self.logger.info(f"Added terminal tab for session: {session_id}")
        except Exception as e:
            self.logger.error(f"添加终端标签页失败: {e}")
    
    def get_terminal_tab(self, session_id: str) -> Optional[PowerShellTerminalTab]:
        """获取终端标签页"""
        return self.terminal_tabs.get(session_id)
    
    def remove_terminal_tab(self, session_id: str):
        """移除终端标签页（通过命令队列）"""
        try:
            self.command_queue.put({
                "type": "remove_tab",
                "session_id": session_id
            })
        except Exception as e:
            self.logger.error(f"发送移除标签页命令失败: {e}")

    def _do_remove_tab(self, session_id: str):
        """实际移除标签页的操作"""
        if session_id in self.terminal_tabs:
            # 删除标签页
            tab_name = f"终端-{session_id[:8]}"
            try:
                self.tab_view.delete(tab_name)
            except Exception as e:
                self.logger.warning(f"删除标签页失败: {e}")

            # 移除引用
            del self.terminal_tabs[session_id]
            self.logger.info(f"Removed terminal tab for session: {session_id}")

    def _do_close_tab_user(self, session_id: str):
        """处理用户关闭标签页的操作"""
        try:
            # 先移除GUI标签页
            self._do_remove_tab(session_id)

            # 通知PowerShell服务关闭会话
            # 这里需要调用PowerShell服务的关闭方法
            # 由于GUI不直接访问PowerShell服务，我们通过日志记录这个操作
            # 实际的会话关闭需要通过MCP工具ps_close来完成
            self.logger.info(f"用户关闭标签页，会话 {session_id} 需要通过ps_close工具关闭")

        except Exception as e:
            self.logger.error(f"用户关闭标签页失败: {e}")

    def show_confirmation_dialog(self, session_id: str, message: str) -> bool:
        """显示用户确认对话框"""
        try:
            # 如果在GUI线程中，直接显示
            if threading.current_thread() == self.gui_thread:
                return self._do_show_confirmation(session_id, message)

            # 否则使用队列通信（这里需要同步等待结果）
            result_queue = queue.Queue()

            def show_dialog():
                try:
                    result = self._do_show_confirmation(session_id, message)
                    result_queue.put(result)
                except Exception as e:
                    self.logger.error(f"确认对话框显示失败: {e}")
                    result_queue.put(False)

            # 在GUI线程中执行
            if self.main_window:
                self.main_window.after(0, show_dialog)

                # 等待结果（最多等待30秒）
                try:
                    return result_queue.get(timeout=30)
                except queue.Empty:
                    return False

            return False
        except Exception as e:
            self.logger.error(f"确认对话框处理失败: {e}")
            return False

    def _do_show_confirmation(self, session_id: str, message: str) -> bool:
        """实际显示确认对话框"""
        try:
            # 确保主窗口可见
            if self.main_window:
                self.main_window.deiconify()
                self.main_window.lift()
                self.main_window.focus()

            # 显示确认对话框
            result = messagebox.askyesno(
                "用户确认",
                f"会话 {session_id[:8]}...\n\n{message}",
                parent=self.main_window
            )

            return result
        except Exception as e:
            self.logger.error(f"确认对话框显示失败: {e}")
            return False
    
    def _handle_user_command(self, session_id: str, command: str):
        """处理用户手动输入的命令"""
        self.logger.info(f"用户在会话 {session_id} 中输入命令: {command}")

        # 通过回调函数执行用户命令
        if self.user_command_callback:
            try:
                # 在新线程中执行异步命令，避免阻塞GUI
                import threading

                def execute_command():
                    try:
                        import asyncio
                        # 创建新的事件循环
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(self.user_command_callback(session_id, command))
                        loop.close()

                        # 在主线程中更新GUI显示结果
                        def update_gui():
                            if result and result.get("success"):
                                output_text = result.get("output", "")
                                if output_text:
                                    self.update_terminal_output(session_id, f"{output_text}\n")
                            else:
                                error_msg = result.get("error", "命令执行失败") if result else "命令执行失败"
                                self.update_terminal_output(session_id, f"错误: {error_msg}\n")

                        # 使用after方法在主线程中更新GUI
                        if self.main_window:
                            self.main_window.after(0, update_gui)

                    except Exception as e:
                        self.logger.error(f"执行用户命令失败: {e}")
                        # 在主线程中显示错误
                        def show_error():
                            self.update_terminal_output(session_id, f"错误: {str(e)}\n")
                        if self.main_window:
                            self.main_window.after(0, show_error)

                # 启动执行线程
                thread = threading.Thread(target=execute_command, daemon=True)
                thread.start()

            except Exception as e:
                self.logger.error(f"启动用户命令执行失败: {e}")
                self.update_terminal_output(session_id, f"错误: {str(e)}\n")
    
    def set_user_command_callback(self, callback):
        """设置用户命令执行回调"""
        self.user_command_callback = callback
        self.logger.info("用户命令回调已设置")

    def _handle_close_tab(self, session_id: str):
        """处理用户点击关闭标签页"""
        try:
            self.logger.info(f"用户请求关闭会话: {session_id}")

            # 通过命令队列发送关闭命令
            self.command_queue.put({
                "type": "close_tab_user",
                "session_id": session_id
            })
        except Exception as e:
            self.logger.error(f"处理关闭标签页失败: {e}")

    def run_main_loop(self):
        """运行主循环"""
        if self.main_window:
            self.main_window.mainloop()


# 全局GUI管理器实例
_gui_manager = None


def get_gui_manager() -> PowerShellGUIManager:
    """获取GUI管理器实例（单例模式）"""
    global _gui_manager
    if _gui_manager is None:
        _gui_manager = PowerShellGUIManager()
    return _gui_manager
