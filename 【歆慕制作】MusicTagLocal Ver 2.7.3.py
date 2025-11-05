import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import os
from pathlib import Path
import logging
from datetime import datetime
import shutil
from mutagen import File
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, TCOM, TCON, COMM, APIC, TPE2, TCOP, TLAN, USLT
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.easyid3 import EasyID3
from mutagen.wave import WAVE
import re
import threading
import sys

class ScrollableFrame(ttk.Frame):
    """可滚动的Frame组件"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 绑定滚动事件
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 创建窗口
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # 配置网格权重
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_frame.bind("<Enter>", self._bind_to_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_from_mousewheel)
        
        # 绑定画布大小变化事件
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _on_canvas_configure(self, event):
        """当画布大小改变时调整内部框架宽度"""
        # 调整内部框架宽度以适应画布
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
        
        # 更新滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _bind_to_mousewheel(self, event):
        """绑定鼠标滚轮事件"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbind_from_mousewheel(self, event):
        """解绑鼠标滚轮事件"""
        self.canvas.unbind_all("<MouseWheel>")
    
    def _on_mousewheel(self, event):
        """鼠标滚轮事件处理"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

class ProgressDialog:
    """进度显示对话框"""
    def __init__(self, parent, title="处理中"):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 确保窗口在屏幕内
        self.window.update_idletasks()
        
        # 计算居中位置
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        window_width = 400
        window_height = 150
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        # 确保窗口不会超出屏幕
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建组件
        self.label = ttk.Label(self.window, text="正在处理，请稍候...")
        self.label.pack(pady=10)
        
        self.progress = ttk.Progressbar(self.window, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=10)
        
        self.detail_label = ttk.Label(self.window, text="")
        self.detail_label.pack(pady=5)
        
        # 开始动画
        self.progress.start()
    
    def update_detail(self, text):
        """更新详细信息"""
        self.detail_label.config(text=text)
        self.window.update()
    
    def close(self):
        """关闭对话框"""
        self.progress.stop()
        self.window.destroy()

class MultiFolderManager:
    """多文件夹管理器"""
    def __init__(self, parent, title, on_update_callback=None):
        self.parent = parent
        self.title = title
        self.on_update_callback = on_update_callback
        self.folders = []
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        
        # 创建按钮和状态标签
        self.button = ttk.Button(self.frame, text=f"管理{title}", command=self.show_manager)
        self.button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(self.frame, text="未选择")
        self.status_label.pack(side=tk.LEFT)
    
    def show_manager(self):
        """显示文件夹管理器窗口"""
        manager_window = tk.Toplevel(self.parent)
        manager_window.title(f"管理{self.title}")
        manager_window.geometry("500x400")
        manager_window.transient(self.parent)
        manager_window.grab_set()
        
        # 确保窗口在屏幕内
        manager_window.update_idletasks()
        
        # 计算居中位置
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        window_width = 500
        window_height = 400
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        # 确保窗口不会超出屏幕
        screen_width = manager_window.winfo_screenwidth()
        screen_height = manager_window.winfo_screenheight()
        
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        manager_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建管理器界面
        ttk.Label(manager_window, text=f"{self.title}文件夹列表:").pack(pady=10)
        
        # 创建列表框和滚动条
        list_frame = ttk.Frame(manager_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 更新列表显示
        self.update_listbox()
        
        # 按钮框架
        button_frame = ttk.Frame(manager_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="添加文件夹", 
                  command=lambda: self.add_folder(manager_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="移除选中", 
                  command=lambda: self.remove_selected(manager_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空所有", 
                  command=lambda: self.clear_all(manager_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", 
                  command=manager_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_folder(self, parent_window):
        """添加文件夹"""
        folder_path = filedialog.askdirectory(title=f"选择{self.title}文件夹")
        if folder_path and folder_path not in self.folders:
            # 显示进度对话框
            progress_dialog = ProgressDialog(parent_window, f"扫描{self.title}文件夹")
            progress_dialog.update_detail(f"正在扫描: {os.path.basename(folder_path)}")
            
            # 在新线程中扫描文件夹
            def scan_folder():
                self.folders.append(folder_path)
                parent_window.after(0, progress_dialog.close)
                parent_window.after(0, self.update_listbox)
                parent_window.after(0, self.update_status)
                if self.on_update_callback:
                    parent_window.after(0, self.on_update_callback)
            
            thread = threading.Thread(target=scan_folder)
            thread.daemon = True
            thread.start()
    
    def remove_selected(self, parent_window):
        """移除选中的文件夹"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.folders.pop(index)
            self.update_listbox()
            self.update_status()
            if self.on_update_callback:
                self.on_update_callback()
    
    def clear_all(self, parent_window):
        """清空所有文件夹"""
        if self.folders:
            if messagebox.askyesno("确认", "确定要清空所有文件夹吗？"):
                self.folders = []
                self.update_listbox()
                self.update_status()
                if self.on_update_callback:
                    self.on_update_callback()
    
    def update_listbox(self):
        """更新列表框显示"""
        if hasattr(self, 'listbox'):
            self.listbox.delete(0, tk.END)
            for folder in self.folders:
                self.listbox.insert(tk.END, folder)
    
    def update_status(self):
        """更新状态标签"""
        count = len(self.folders)
        if count == 0:
            self.status_label.config(text="未选择")
        else:
            self.status_label.config(text=f"已选择 {count} 个")
    
    def get_folders(self):
        """获取所有文件夹路径"""
        return self.folders.copy()
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.frame.grid(**kwargs)

class LogWindow:
    """独立的日志输出窗口"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("处理日志")
        self.window.geometry("800x500")
        self.window.transient(parent)
        
        # 创建文本区域
        self.text_area = scrolledtext.ScrolledText(
            self.window, 
            wrap=tk.WORD, 
            width=80, 
            height=25,
            font=("Consolas", 10)
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 添加清除按钮
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="清除日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存日志", command=self.save_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        # 配置日志处理器
        self.setup_log_handler()
    
    def setup_log_handler(self):
        """设置日志处理器"""
        self.log_handler = LogHandler(self.text_area)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def clear_log(self):
        """清除日志"""
        self.text_area.delete(1.0, tk.END)
    
    def save_log(self):
        """保存日志到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存日志文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_area.get(1.0, tk.END))
                messagebox.showinfo("成功", "日志已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {str(e)}")

class LogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到文本区域"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
        self.text_widget.after(0, append)

class FuzzyMatchDebugWindow:
    """模糊匹配调试窗口"""
    def __init__(self, parent, song_editor):
        self.parent = parent
        self.song_editor = song_editor
        self.window = tk.Toplevel(parent)
        self.window.title("模糊匹配调试")
        self.window.geometry("900x700")
        self.window.transient(parent)
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="匹配参数设置", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 匹配阈值设置
        threshold_frame = ttk.Frame(control_frame)
        threshold_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(threshold_frame, text="匹配阈值:").pack(side=tk.LEFT)
        self.threshold_var = tk.DoubleVar(value=0.6)
        threshold_scale = ttk.Scale(threshold_frame, from_=0.1, to=1.0, variable=self.threshold_var, 
                                   orient=tk.HORIZONTAL, length=200)
        threshold_scale.pack(side=tk.LEFT, padx=(10, 10))
        self.threshold_label = ttk.Label(threshold_frame, text="0.60")
        self.threshold_label.pack(side=tk.LEFT)
        
        # 绑定阈值变化事件
        threshold_scale.configure(command=self.on_threshold_changed)
        
        # 搜索框
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索歌曲:").pack(side=tk.LEFT)
        self.debug_search_var = tk.StringVar()
        self.debug_search_entry = ttk.Entry(search_frame, textvariable=self.debug_search_var, width=30)
        self.debug_search_entry.pack(side=tk.LEFT, padx=(10, 10))
        self.debug_search_entry.bind('<Return>', self.on_debug_search)
        
        ttk.Button(search_frame, text="搜索", command=self.on_debug_search).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(search_frame, text="清除", command=self.clear_debug_search).pack(side=tk.LEFT)
        
        # 按钮框架
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="重新计算匹配", command=self.recalculate_matches).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="应用阈值到主程序", command=self.apply_threshold_to_main).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="导出匹配报告", command=self.export_match_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="关闭", command=self.window.destroy).pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="匹配结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview显示匹配结果
        columns = ["Excel标题", "匹配文件名", "匹配率", "匹配状态", "清理后标题", "清理后文件名"]
        self.debug_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=20)
        
        # 设置列宽
        column_widths = [150, 150, 80, 100, 150, 150]
        for col, width in zip(columns, column_widths):
            self.debug_tree.heading(col, text=col)
            self.debug_tree.column(col, width=width, minwidth=50)
        
        # 配置颜色标签
        self.debug_tree.tag_configure('matched', background='#e8f5e8')  # 浅绿色 - 已匹配
        self.debug_tree.tag_configure('unmatched', background='#f5f5f5')  # 浅灰色 - 未匹配
        self.debug_tree.tag_configure('partial', background='#fff9e6')  # 浅黄色 - 部分匹配
        
        # 添加滚动条
        debug_v_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.debug_tree.yview)
        debug_h_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.debug_tree.xview)
        self.debug_tree.configure(yscrollcommand=debug_v_scrollbar.set, xscrollcommand=debug_h_scrollbar.set)
        
        # 使用pack布局Treeview和滚动条
        debug_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        debug_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.debug_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定双击事件
        self.debug_tree.bind("<Double-1>", self.on_debug_tree_double_click)
        
        # 初始加载数据
        self.recalculate_matches()
    
    def on_threshold_changed(self, value):
        """阈值变化事件"""
        threshold_value = float(value)
        self.threshold_label.config(text=f"{threshold_value:.2f}")
        # 实时重新计算匹配
        self.recalculate_matches()
    
    def on_debug_search(self, event=None):
        """调试搜索"""
        search_term = self.debug_search_var.get().lower()
        self.recalculate_matches(search_term)
    
    def clear_debug_search(self):
        """清除调试搜索"""
        self.debug_search_var.set("")
        self.recalculate_matches()
    
    def recalculate_matches(self, search_term=None):
        """重新计算匹配"""
        if self.song_editor.df is None:
            messagebox.showwarning("警告", "请先加载Excel文件")
            return
        
        # 清空现有数据
        for item in self.debug_tree.get_children():
            self.debug_tree.delete(item)
        
        threshold = self.threshold_var.get()
        match_count = 0
        total_count = 0
        
        for index, row in self.song_editor.df.iterrows():
            title = str(row.get('标题', ''))
            
            # 如果有搜索词，检查是否匹配
            if search_term and search_term not in title.lower():
                continue
                
            total_count += 1
            clean_title = self.song_editor.clean_string_for_matching(title)
            best_match = None
            best_score = 0
            best_filename = ""
            clean_filename = ""
            
            # 查找最佳匹配
            for song in self.song_editor.song_files:
                song_clean_name = self.song_editor.clean_string_for_matching(song['name_only'])
                score = self.song_editor.enhanced_fuzzy_match(clean_title, song_clean_name)
                
                if score > best_score:
                    best_score = score
                    best_match = song
                    clean_filename = song_clean_name
            
            # 确定匹配状态
            status = "未匹配"
            if best_match and best_score >= threshold:
                status = "已匹配"
                match_count += 1
            elif best_match:
                status = f"低于阈值({best_score:.2f})"
            
            values = [
                title,
                os.path.basename(best_match['path']) if best_match else "无匹配",
                f"{best_score:.2f}" if best_match else "0.00",
                status,
                clean_title,
                clean_filename
            ]
            
            # 根据匹配状态设置标签
            tags = ()
            if status == "已匹配":
                tags = ('matched',)
            elif "低于阈值" in status:
                tags = ('partial',)
            else:
                tags = ('unmatched',)
                
            self.debug_tree.insert("", tk.END, values=values, tags=tags)
        
        # 更新窗口标题显示统计信息
        self.window.title(f"模糊匹配调试 - 匹配率: {match_count}/{total_count} ({match_count/max(total_count,1)*100:.1f}%)")
    
    def apply_threshold_to_main(self):
        """将当前阈值应用到主程序并重新运行匹配"""
        # 更新主程序的匹配阈值
        self.song_editor.match_threshold = self.threshold_var.get()
        
        # 显示进度对话框
        progress_dialog = ProgressDialog(self.window, "重新匹配歌曲")
        
        # 在新线程中重新运行匹配
        def run_matching():
            # 重新计算所有匹配
            self.song_editor.match_results = {}
            self.song_editor.match_scores = {}
            
            for index, row in self.song_editor.df.iterrows():
                title = str(row.get('标题', ''))
                matched_file = self.song_editor.find_matched_file_with_threshold(title, self.song_editor.match_threshold)
                
                if matched_file:
                    self.song_editor.match_results[index] = matched_file
                    # 计算匹配率
                    clean_title = self.song_editor.clean_string_for_matching(title)
                    filename = Path(matched_file).stem
                    clean_filename = self.song_editor.clean_string_for_matching(filename)
                    self.song_editor.match_scores[index] = self.song_editor.enhanced_fuzzy_match(clean_title, clean_filename)
            
            # 在主线程中更新UI
            self.window.after(0, progress_dialog.close)
            self.window.after(0, self.song_editor.refresh_matches)
            self.window.after(0, lambda: messagebox.showinfo("成功", f"已应用新阈值 {self.song_editor.match_threshold:.2f} 并重新匹配"))
        
        thread = threading.Thread(target=run_matching)
        thread.daemon = True
        thread.start()
    
    def export_match_report(self):
        """导出匹配报告"""
        if not self.song_editor.df:
            messagebox.showwarning("警告", "没有数据可导出")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="保存匹配报告",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                # 收集所有数据
                data = []
                for item in self.debug_tree.get_children():
                    values = self.debug_tree.item(item)['values']
                    data.append({
                        'Excel标题': values[0],
                        '匹配文件名': values[1],
                        '匹配率': values[2],
                        '匹配状态': values[3],
                        '清理后标题': values[4],
                        '清理后文件名': values[5]
                    })
                
                # 创建DataFrame并保存
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                messagebox.showinfo("成功", f"匹配报告已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出匹配报告失败: {str(e)}")
    
    def on_debug_tree_double_click(self, event):
        """调试树双击事件"""
        item = self.debug_tree.selection()[0] if self.debug_tree.selection() else None
        if not item:
            return
            
        values = self.debug_tree.item(item)['values']
        title = values[0]
        matched_file = values[1]
        match_rate = values[2]
        
        # 显示匹配详情
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"匹配详情 - {title}")
        detail_window.geometry("600x400")
        
        text_area = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD, width=70, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        text_area.insert(tk.END, f"=== 匹配详情 ===\n\n")
        text_area.insert(tk.END, f"Excel标题: {title}\n")
        text_area.insert(tk.END, f"匹配文件名: {matched_file}\n")
        text_area.insert(tk.END, f"匹配率: {match_rate}\n")
        text_area.insert(tk.END, f"清理后标题: {values[4]}\n")
        text_area.insert(tk.END, f"清理后文件名: {values[5]}\n\n")
        
        # 显示所有可能的匹配
        clean_title = values[4]
        text_area.insert(tk.END, f"=== 所有可能的匹配 ===\n\n")
        
        if not self.song_editor.song_files:
            text_area.insert(tk.END, "没有可用的歌曲文件\n")
        else:
            # 按匹配分数排序
            matches_with_scores = []
            for song in self.song_editor.song_files:
                clean_filename = self.song_editor.clean_string_for_matching(song['name_only'])
                score = self.song_editor.enhanced_fuzzy_match(clean_title, clean_filename)
                matches_with_scores.append((song, score))
            
            # 按分数降序排序
            matches_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 显示前10个最佳匹配
            for i, (song, score) in enumerate(matches_with_scores[:10]):
                status = "✅ 当前匹配" if matched_file == os.path.basename(song['path']) else ""
                text_area.insert(tk.END, f"{i+1}. {song['filename']}\n")
                text_area.insert(tk.END, f"   匹配率: {score:.3f} {status}\n")
                text_area.insert(tk.END, f"   路径: {song['path']}\n\n")
        
        text_area.config(state=tk.DISABLED)

class ManualWindow:
    """产品说明书窗口"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("产品说明书 - 歌曲元数据录入软件")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        # 创建文本区域
        self.text_area = scrolledtext.ScrolledText(
            self.window, 
            wrap=tk.WORD, 
            width=80, 
            height=35,
            font=("微软雅黑", 10)
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 添加关闭按钮
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="关闭", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        # 加载说明书内容
        self.load_manual_content()
    
    def load_manual_content(self):
        """加载说明书内容"""
        manual_content = """
歌曲元数据录入软件 v2.7 - 产品说明书

一、软件简介
本软件是一款专业的歌曲元数据管理工具，能够批量处理音频文件的元数据信息，
包括歌曲标题、艺术家、专辑、年份、语种等，并支持歌词和封面图片的导入。

二、主要功能
1. 多文件夹管理：支持同时管理多个歌曲文件夹、歌词文件夹和图片文件夹
2. 智能匹配：通过智能算法自动匹配Excel数据与音频文件
3. 字段映射：灵活配置Excel字段与音频元数据字段的映射关系
4. 批量处理：支持批量写入元数据、歌词和封面图片
5. 匹配调试：提供详细的匹配调试功能，优化匹配效果

三、使用步骤

第一步：文件准备
1. 准备Excel文件，包含歌曲信息（标题、艺术家、专辑、年份、语种等）
2. 准备音频文件文件夹
3. （可选）准备歌词文件文件夹
4. （可选）准备封面图片文件夹

第二步：加载文件
1. 点击"选择Excel文件"加载数据文件
2. 点击"选择输出文件夹"设置处理后的文件保存位置
3. 使用"管理歌曲文件夹"添加音频文件所在文件夹
4. 使用"管理歌词文件夹"添加歌词文件所在文件夹
5. 使用"管理图片文件夹"添加封面图片所在文件夹

第三步：匹配设置
1. 在字段映射区域设置Excel字段与目标字段的对应关系
2. 可以使用"自动匹配"快速建立字段映射
3. 对于特殊字段，可以使用"手动匹配"进行精确设置

第四步：匹配歌曲
1. 点击"自动匹配"进行初步匹配
2. 对于未匹配的歌曲，可以使用"模糊匹配"提高匹配率
3. 对于特殊歌曲，可以双击行进行手动匹配
4. 使用"调试匹配"查看匹配详情和优化匹配效果

第五步：保存结果
1. 在保存设置中选择需要保存的内容（ID3标签、歌词、图片等）
2. 点击"开始保存"按钮处理所有匹配的歌曲
3. 处理完成后查看结果统计和错误日志

四、匹配算法说明

1. 字符串清理
   - 移除括号及其内容
   - 移除版本标记（如remix、cover、demo等）
   - 移除特殊字符和分隔符
   - 转换为小写

2. 匹配策略（按优先级）
   - 原始文件名完全匹配
   - 清理后完全匹配
   - 互相包含关系
   - 增强的模糊匹配（基于LCS算法）
   - 单词匹配（针对英文歌曲）

3. 匹配阈值
   - 高匹配率（>0.9）：绿色显示
   - 中等匹配率（0.7-0.9）：黄色显示
   - 低匹配率（<0.7）：红色显示

五、高级功能

1. 模糊匹配调试
   - 可以调整匹配阈值实时查看匹配效果
   - 显示清理前后的字符串对比
   - 导出详细的匹配报告

2. 右键菜单功能
   - 手动匹配歌曲：为特定歌曲手动选择音频文件
   - 清除匹配：清除已建立的匹配关系
   - 查看匹配详情：显示详细的匹配计算过程

3. 搜索功能
   - 支持按标题、艺术家、专辑等字段搜索
   - 支持字段映射搜索
   - 支持模糊匹配调试搜索

六、支持的文件格式

1. 音频文件：MP3、FLAC、WAV、M4A、AAC、OGG、WMA
2. 歌词文件：LRC、TXT、LYRIC、LRCX
3. 图片文件：JPG、JPEG、PNG、GIF、BMP、TIFF
4. 数据文件：Excel（XLSX）

七、常见问题

1. 匹配率低怎么办？
   - 检查文件名是否包含过多无关信息
   - 尝试调整匹配阈值
   - 使用手动匹配功能

2. 元数据写入失败？
   - 检查文件是否被其他程序占用
   - 检查文件格式是否支持
   - 查看错误日志了解具体原因

3. 如何处理大量文件？
   - 分批处理，避免内存不足
   - 使用多文件夹管理功能分散文件
   - 定期查看处理日志

八、技术支持
如有问题或建议，请联系开发团队或查看详细的使用文档。

祝您使用愉快！
"""
        self.text_area.insert(tk.END, manual_content)
        self.text_area.config(state=tk.DISABLED)

class SongMetadataEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("歌曲元数据录入软件 v2.7 - 增强版")
        self.root.geometry("1300x850")
        
        # 设置图标
        self.set_icon()
        
        # 初始化数据
        self.df = None
        self.song_folders = []
        self.lyrics_folders = []
        self.image_folders = []
        self.output_folder = None
        self.song_files = []
        self.lyrics_files = []
        self.image_files = []
        self.processed_data = []
        self.mapping_rules = {}
        self.match_results = {}
        self.exact_match = False
        self.match_scores = {}
        self.match_threshold = 0.6  # 默认匹配阈值
        
        # 设置日志
        self.setup_logging()
        
        # 创建界面
        self.create_widgets()
        
        # 日志窗口
        self.log_window = None
        # 模糊匹配调试窗口
        self.fuzzy_debug_window = None
        # 产品说明书窗口
        self.manual_window = None
        
    def set_icon(self):
        """设置应用程序图标"""
        try:
            # 尝试从资源文件或当前目录加载图标
            icon_path = self.get_icon_path()
            if icon_path and os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                logging.info(f"成功加载图标: {icon_path}")
            else:
                # 如果没有找到图标文件，使用默认的音乐图标
                self.create_default_icon()
        except Exception as e:
            logging.warning(f"设置图标失败: {str(e)}")
    
    def get_icon_path(self):
        """获取图标文件路径"""
        # 首先检查当前目录
        current_dir = Path(__file__).parent
        possible_paths = [
            current_dir / "icon.ico",
            current_dir / "music_icon.ico",
            current_dir / "assets" / "icon.ico",
            current_dir / "resources" / "icon.ico"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # 如果打包成exe，检查临时目录
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).parent
            exe_paths = [
                exe_dir / "icon.ico",
                exe_dir / "music_icon.ico"
            ]
            for path in exe_paths:
                if path.exists():
                    return str(path)
        
        return None
    
    def create_default_icon(self):
        """创建默认的音乐图标（使用内置图标）"""
        try:
            # 在Windows系统上可以使用内置图标
            if os.name == 'nt':
                self.root.iconbitmap(default='@music.ico')  # 使用系统音乐图标
        except:
            pass  # 如果设置图标失败，忽略错误
        
    def setup_logging(self):
        """设置日志记录"""
        desktop = Path.home() / "Desktop"
        log_file = desktop / "song_metadata_editor.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建可滚动的主框架 - 修复滚动条问题
        self.scrollable_main = ScrollableFrame(main_frame)
        self.scrollable_main.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(self.scrollable_main.scrollable_frame, text="文件操作", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Excel文件选择
        excel_frame = ttk.Frame(file_frame)
        excel_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(excel_frame, text="选择Excel文件", command=self.load_excel).pack(side=tk.LEFT, padx=(0, 10))
        self.file_label = ttk.Label(excel_frame, text="未选择Excel文件")
        self.file_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # 输出文件夹选择
        ttk.Button(excel_frame, text="选择输出文件夹", command=self.load_output_folder).pack(side=tk.LEFT, padx=(0, 10))
        self.output_label = ttk.Label(excel_frame, text="未选择输出文件夹")
        self.output_label.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(excel_frame, text="查看日志", command=self.show_log_window).pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加产品说明书按钮
        ttk.Button(excel_frame, text="产品说明书", command=self.show_manual_window).pack(side=tk.LEFT, padx=(0, 10))
        
        # 多文件夹选择器 - 使用pack布局
        folders_frame = ttk.Frame(file_frame)
        folders_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 歌曲文件夹管理器
        song_folder_label = ttk.Label(folders_frame, text="歌曲文件夹:")
        song_folder_label.pack(side=tk.LEFT, padx=(0, 5))
        self.song_folder_manager = MultiFolderManager(
            folders_frame, 
            "歌曲文件夹",
            on_update_callback=self.on_song_folders_updated
        )
        self.song_folder_manager.pack(side=tk.LEFT, padx=(0, 20))
        
        # 歌词文件夹管理器
        lyrics_folder_label = ttk.Label(folders_frame, text="歌词文件夹:")
        lyrics_folder_label.pack(side=tk.LEFT, padx=(0, 5))
        self.lyrics_folder_manager = MultiFolderManager(
            folders_frame, 
            "歌词文件夹",
            on_update_callback=self.on_lyrics_folders_updated
        )
        self.lyrics_folder_manager.pack(side=tk.LEFT, padx=(0, 20))
        
        # 图片文件夹管理器
        image_folder_label = ttk.Label(folders_frame, text="图片文件夹:")
        image_folder_label.pack(side=tk.LEFT, padx=(0, 5))
        self.image_folder_manager = MultiFolderManager(
            folders_frame, 
            "图片文件夹",
            on_update_callback=self.on_image_folders_updated
        )
        self.image_folder_manager.pack(side=tk.LEFT, padx=(0, 0))
        
        # 数据显示区域
        data_frame = ttk.LabelFrame(self.scrollable_main.scrollable_frame, text="歌曲数据与匹配", padding="10")
        data_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 匹配统计信息
        stats_frame = ttk.Frame(data_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="匹配统计: 成功 0 首, 失败 0 首, 未匹配 0 首")
        self.stats_label.pack(side=tk.LEFT)
        
        # 搜索框
        search_frame = ttk.Frame(data_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 10))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 修改：移除实时搜索，改为回车触发
        self.search_entry.bind('<Return>', self.search_data)
        
        # 添加搜索按钮
        ttk.Button(search_frame, text="搜索", command=self.search_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(search_frame, text="清除", command=self.clear_search).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(search_frame, text="置顶已匹配", command=self.sort_matched_first).pack(side=tk.LEFT)
        
        # 创建Treeview显示数据 - 使用pack布局
        columns = ["选择", "Excel标题", "文件名", "匹配率", "艺术家", "年份", "语种", "所属专辑", "歌词状态", "图片状态", "匹配状态"]
        self.tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=12)
        
        # 设置列宽
        column_widths = [60, 180, 220, 80, 120, 80, 80, 180, 100, 100, 100]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=50)
        
        # 配置颜色标签
        self.tree.tag_configure('matched', background='#e8f5e8')  # 浅绿色 - 已匹配
        self.tree.tag_configure('unmatched', background='#f5f5f5')  # 浅灰色 - 未匹配
        self.tree.tag_configure('partial', background='#fff9e6')  # 浅黄色 - 部分匹配
        self.tree.tag_configure('failed', background='#ffe6e6')  # 浅红色 - 匹配失败
        
        # 添加垂直和水平滚动条 - 使用pack布局
        tree_frame = ttk.Frame(data_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 使用pack布局Treeview和滚动条
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定双击事件用于手动匹配
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        # 绑定右键菜单
        self.tree.bind("<Button-3>", self.show_context_menu)  # 右键点击
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="手动匹配歌曲", command=self.manual_match_from_context)
        self.context_menu.add_command(label="清除匹配", command=self.clear_match_from_context)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="查看匹配详情", command=self.view_match_details)
        
        # 匹配设置区域
        match_frame = ttk.LabelFrame(self.scrollable_main.scrollable_frame, text="匹配设置", padding="10")
        match_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 搜索框
        map_search_frame = ttk.Frame(match_frame)
        map_search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(map_search_frame, text="搜索字段:").pack(side=tk.LEFT, padx=(0, 10))
        self.map_search_var = tk.StringVar()
        self.map_search_entry = ttk.Entry(map_search_frame, textvariable=self.map_search_var, width=30)
        self.map_search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 修改：移除实时搜索，改为回车触发
        self.map_search_entry.bind('<Return>', self.search_mapping)
        
        # 添加搜索按钮
        ttk.Button(map_search_frame, text="搜索", command=self.search_mapping).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(map_search_frame, text="清除", command=self.clear_map_search).pack(side=tk.LEFT, padx=(0, 10))
        
        # 精确匹配选项
        self.exact_match_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(map_search_frame, text="精确匹配", variable=self.exact_match_var, 
                       command=self.toggle_exact_match).pack(side=tk.LEFT, padx=(20, 0))
        
        # 字段映射设置
        ttk.Label(match_frame, text="字段映射规则:").pack(anchor=tk.W)
        
        # 创建字段映射表格的容器框架
        map_tree_frame = ttk.Frame(match_frame)
        map_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 创建字段映射表格
        map_columns = ["Excel字段", "目标字段", "匹配方式"]
        self.map_tree = ttk.Treeview(map_tree_frame, columns=map_columns, show="headings", height=6)
        
        for col in map_columns:
            self.map_tree.heading(col, text=col)
            self.map_tree.column(col, width=150)
        
        # 添加滚动条到映射表格 - 使用pack布局
        map_v_scrollbar = ttk.Scrollbar(map_tree_frame, orient=tk.VERTICAL, command=self.map_tree.yview)
        map_h_scrollbar = ttk.Scrollbar(map_tree_frame, orient=tk.HORIZONTAL, command=self.map_tree.xview)
        self.map_tree.configure(yscrollcommand=map_v_scrollbar.set, xscrollcommand=map_h_scrollbar.set)
        
        # 使用pack布局映射表格和滚动条
        map_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        map_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.map_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 匹配按钮
        button_frame = ttk.Frame(match_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="自动匹配", command=self.auto_match).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="手动匹配", command=self.manual_match).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="模糊匹配", command=self.fuzzy_match).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="刷新匹配", command=self.refresh_matches).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="调试匹配", command=self.debug_matching).pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加模糊匹配调试按钮
        ttk.Button(button_frame, text="模糊匹配调试", command=self.show_fuzzy_debug_window).pack(side=tk.LEFT, padx=(0, 10))
        
        # 操作区域
        action_frame = ttk.LabelFrame(self.scrollable_main.scrollable_frame, text="操作", padding="10")
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 保存设置
        settings_frame = ttk.Frame(action_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="保存类别:").pack(side=tk.LEFT)
        self.save_vars = {}
        
        save_categories = ["ID3标签", "Excel文件", "文本文件"]
        for i, category in enumerate(save_categories):
            var = tk.BooleanVar(value=True)
            self.save_vars[category] = var
            ttk.Checkbutton(settings_frame, text=category, variable=var).pack(side=tk.LEFT, padx=(10, 0))
        
        # 歌词选项
        self.lyrics_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="导入歌词", variable=self.lyrics_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # 图片选项
        self.images_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="导入图片", variable=self.images_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # 备份选项
        self.backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="备份原文件", variable=self.backup_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # 保存按钮和进度条
        ttk.Button(action_frame, text="开始保存", command=self.start_save_process).pack(pady=(0, 10))
        
        # 进度条
        self.progress = ttk.Progressbar(action_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        # 结果统计
        self.result_label = ttk.Label(action_frame, text="准备就绪")
        self.result_label.pack()
        
        # 配置主窗口的网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 存储当前选中的行索引
        self.selected_row_index = None
    
    def show_fuzzy_debug_window(self):
        """显示模糊匹配调试窗口"""
        if self.fuzzy_debug_window is None or not self.fuzzy_debug_window.window.winfo_exists():
            self.fuzzy_debug_window = FuzzyMatchDebugWindow(self.root, self)
        else:
            self.fuzzy_debug_window.window.lift()
    
    def show_manual_window(self):
        """显示产品说明书窗口"""
        if self.manual_window is None or not self.manual_window.window.winfo_exists():
            self.manual_window = ManualWindow(self.root)
        else:
            self.manual_window.window.lift()
    
    def on_song_folders_updated(self):
        """歌曲文件夹更新回调"""
        self.song_folders = self.song_folder_manager.get_folders()
        # 显示进度对话框
        progress_dialog = ProgressDialog(self.root, "扫描歌曲文件")
        
        # 在新线程中扫描文件
        def scan_files():
            self.scan_song_files()
            self.root.after(0, progress_dialog.close)
            self.root.after(0, self.refresh_matches)
            logging.info(f"歌曲文件夹已更新: {len(self.song_folders)} 个文件夹")
        
        thread = threading.Thread(target=scan_files)
        thread.daemon = True
        thread.start()
    
    def on_lyrics_folders_updated(self):
        """歌词文件夹更新回调"""
        self.lyrics_folders = self.lyrics_folder_manager.get_folders()
        # 显示进度对话框
        progress_dialog = ProgressDialog(self.root, "扫描歌词文件")
        
        # 在新线程中扫描文件
        def scan_files():
            self.scan_lyrics_files()
            self.root.after(0, progress_dialog.close)
            self.root.after(0, self.refresh_matches)
            logging.info(f"歌词文件夹已更新: {len(self.lyrics_folders)} 个文件夹")
        
        thread = threading.Thread(target=scan_files)
        thread.daemon = True
        thread.start()
    
    def on_image_folders_updated(self):
        """图片文件夹更新回调"""
        self.image_folders = self.image_folder_manager.get_folders()
        # 显示进度对话框
        progress_dialog = ProgressDialog(self.root, "扫描图片文件")
        
        # 在新线程中扫描文件
        def scan_files():
            self.scan_image_files()
            self.root.after(0, progress_dialog.close)
            self.root.after(0, self.refresh_matches)
            logging.info(f"图片文件夹已更新: {len(self.image_folders)} 个文件夹")
        
        thread = threading.Thread(target=scan_files)
        thread.daemon = True
        thread.start()
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击的行
        item = self.tree.identify_row(event.y)
        if item:
            # 选中该行
            self.tree.selection_set(item)
            # 获取行数据
            values = self.tree.item(item, 'values')
            excel_title = values[1]  # Excel标题在第二列
            
            # 查找对应的行索引
            for index, row in self.df.iterrows():
                if str(row.get('标题', '')) == excel_title:
                    self.selected_row_index = index
                    break
            
            # 在鼠标位置显示菜单
            self.context_menu.post(event.x_root, event.y_root)
    
    def manual_match_from_context(self):
        """从右键菜单手动匹配歌曲"""
        if self.selected_row_index is None:
            messagebox.showwarning("警告", "请先选择一行数据")
            return
            
        # 获取Excel标题
        row = self.df.iloc[self.selected_row_index]
        title = str(row.get('标题', ''))
        
        self.manual_song_match(self.selected_row_index, title)
    
    def clear_match_from_context(self):
        """从右键菜单清除匹配"""
        if self.selected_row_index is None:
            messagebox.showwarning("警告", "请先选择一行数据")
            return
            
        # 清除匹配结果
        if self.selected_row_index in self.match_results:
            del self.match_results[self.selected_row_index]
            if self.selected_row_index in self.match_scores:
                del self.match_scores[self.selected_row_index]
            
            self.refresh_matches()
            messagebox.showinfo("成功", "已清除匹配")
        else:
            messagebox.showinfo("提示", "该行没有匹配记录")
    
    def view_match_details(self):
        """查看匹配详情"""
        if self.selected_row_index is None:
            messagebox.showwarning("警告", "请先选择一行数据")
            return
            
        # 获取Excel标题
        row = self.df.iloc[self.selected_row_index]
        title = str(row.get('标题', ''))
        
        # 创建详情窗口
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"匹配详情 - {title}")
        detail_window.geometry("600x400")
        
        # 创建文本框
        text_area = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD, width=70, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 添加内容
        text_area.insert(tk.END, f"=== 匹配详情 ===\n\n")
        text_area.insert(tk.END, f"Excel标题: {title}\n")
        
        # 清理后的标题
        clean_title = self.clean_string_for_matching(title)
        text_area.insert(tk.END, f"清理后标题: {clean_title}\n\n")
        
        # 当前匹配状态
        if self.selected_row_index in self.match_results:
            matched_file = self.match_results[self.selected_row_index]
            text_area.insert(tk.END, f"✅ 已匹配文件:\n")
            text_area.insert(tk.END, f"   文件名: {os.path.basename(matched_file)}\n")
            text_area.insert(tk.END, f"   完整路径: {matched_file}\n")
            
            # 计算匹配率
            filename = Path(matched_file).stem
            clean_filename = self.clean_string_for_matching(filename)
            match_score = self.match_scores.get(self.selected_row_index, 0)
            text_area.insert(tk.END, f"   匹配率: {match_score:.1%}\n\n")
        else:
            text_area.insert(tk.END, f"❌ 未匹配\n\n")
        
        # 显示所有歌曲文件的匹配情况
        text_area.insert(tk.END, f"=== 所有歌曲文件匹配情况 ===\n\n")
        
        if not self.song_files:
            text_area.insert(tk.END, "没有可用的歌曲文件\n")
        else:
            # 按匹配分数排序
            matches_with_scores = []
            for song in self.song_files:
                clean_filename = self.clean_string_for_matching(song['name_only'])
                score = self.enhanced_fuzzy_match(clean_title, clean_filename)
                matches_with_scores.append((song, score))
            
            # 按分数降序排序
            matches_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 显示前10个最佳匹配
            for i, (song, score) in enumerate(matches_with_scores[:10]):
                status = "✅ 当前匹配" if (self.selected_row_index in self.match_results and 
                                       self.match_results[self.selected_row_index] == song['path']) else ""
                text_area.insert(tk.END, f"{i+1}. {song['filename']}\n")
                text_area.insert(tk.END, f"   匹配率: {score:.1%} {status}\n")
                text_area.insert(tk.END, f"   路径: {song['path']}\n\n")
        
        text_area.config(state=tk.DISABLED)
    
    def update_stats(self):
        """更新匹配统计信息"""
        if self.df is None:
            return
            
        total = len(self.df)
        matched = len(self.match_results)
        unmatched = total - matched
        
        # 计算失败数量（匹配率低于50%的）
        failed = 0
        for index in range(total):
            if index not in self.match_results and self.match_scores.get(index, 0) < 0.5:
                failed += 1
        
        self.stats_label.config(text=f"匹配统计: 成功 {matched} 首, 失败 {failed} 首, 未匹配 {unmatched} 首")
    
    def on_tree_double_click(self, event):
        """处理树形视图的双击事件，用于手动匹配"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
            
        # 获取行数据
        values = self.tree.item(item, 'values')
        excel_title = values[1]  # Excel标题在第二列
        
        # 查找对应的行索引
        for index, row in self.df.iterrows():
            if str(row.get('标题', '')) == excel_title:
                self.selected_row_index = index
                self.manual_song_match(index, excel_title)
                break
    
    def manual_song_match(self, index, title):
        """手动匹配歌曲文件"""
        if not self.song_files:
            messagebox.showwarning("警告", "请先选择歌曲文件夹")
            return
            
        # 创建文件选择对话框
        file_path = filedialog.askopenfilename(
            title=f"为 '{title}' 选择匹配的音频文件",
            filetypes=[
                ("音频文件", "*.mp3 *.flac *.wav *.m4a *.aac *.ogg *.wma"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            # 更新匹配结果
            self.match_results[index] = file_path
            
            # 计算匹配率
            clean_title = self.clean_string_for_matching(title)
            filename = Path(file_path).stem
            clean_filename = self.clean_string_for_matching(filename)
            match_score = self.enhanced_fuzzy_match(clean_title, clean_filename)
            self.match_scores[index] = match_score
            
            # 刷新显示
            self.refresh_matches()
            messagebox.showinfo("成功", f"已手动匹配: {title} -> {os.path.basename(file_path)}")
    
    def clean_string_for_matching(self, s):
        """清理字符串用于匹配 - 增强版本，特别优化中文处理"""
        if not s:
            return ""
        
        # 保存原始字符串用于调试
        original = s
        
        # 首先处理常见的括号和特殊字符
        # 移除各种括号及其内容（中文括号、英文括号、方括号等）
        s = re.sub(r'[【】\[\]\(\)（）《》「」]', '', s)
        
        # 移除常见的修饰词和版本标记 - 使用非贪婪匹配
        patterns_to_remove = [
            r'\s*（.*?）', r'\s*\(.*?\)',           # 括号内容
            r'\s*翻自.*?$', r'\s*cover.*?$',       # 翻唱标记
            r'\s*feat\..*?$', r'\s*ft\..*?$',      # 合作标记
            r'\s*prod\..*?$', r'\s*remix.*?$',     # 制作标记
            r'\s*ver\..*?$', r'\s*version.*?$',    # 版本标记
            r'\s*original.*?$', r'\s*原版.*?$',     # 原版标记
            r'\s*demo.*?$', r'\s*试听.*?$',         # demo标记
            r'\s*pv.*?$', r'\s*mv.*?$',            # PV/MV标记
            r'\s*动漫.*?$', r'\s*anime.*?$',        # 动漫相关
            r'\s*电视剧.*?$', r'\s*tv.*?$',         # 电视剧相关
            r'\s*游戏.*?$', r'\s*game.*?$',         # 游戏相关
            r'\s*电影.*?$', r'\s*movie.*?$',        # 电影相关
            r'\s*官方.*?$', r'\s*offical.*?$',      # 官方版本
            r'\s*正式版.*?$', r'\s*正式.*?$',        # 正式版
            r'\s*完整版.*?$', r'\s*完整.*?$',        # 完整版
        ]
        
        for pattern in patterns_to_remove:
            s = re.sub(pattern, '', s, flags=re.IGNORECASE)
        
        # 移除特殊字符，但保留中文字符
        # 只移除真正的分隔符，不移除中文字符间的连接符
        s = re.sub(r'[\-_\s\.\，\。\！\？\、]', '', s)
        
        # 转换为小写
        s = s.lower()
        
        # 记录清理过程用于调试
        if original != s:
            logging.debug(f"字符串清理: '{original}' -> '{s}'")
        
        return s

    def enhanced_fuzzy_match(self, s1, s2):
        """增强的模糊匹配算法，特别优化中文处理"""
        if not s1 or not s2:
            return 0
            
        # 如果完全相等，直接返回1.0
        if s1 == s2:
            return 1.0
        
        # 计算最长公共子序列长度
        def lcs_length(x, y):
            m, n = len(x), len(y)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if x[i - 1] == y[j - 1]:
                        dp[i][j] = dp[i - 1][j - 1] + 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
            return dp[m][n]
        
        lcs_len = lcs_length(s1, s2)
        similarity = 2.0 * lcs_len / (len(s1) + len(s2))
        
        # 添加前缀匹配加分
        prefix_len = 0
        min_len = min(len(s1), len(s2))
        for i in range(min_len):
            if s1[i] == s2[i]:
                prefix_len += 1
            else:
                break
        
        prefix_bonus = prefix_len / min_len * 0.3  # 前缀匹配最多加0.3分
        
        # 添加中文特定匹配策略
        # 如果字符串包含中文字符，使用更宽松的匹配策略
        def contains_chinese(text):
            return re.search(r'[\u4e00-\u9fff]', text)
        
        if contains_chinese(s1) and contains_chinese(s2):
            # 对于中文，相似度要求可以适当降低
            chinese_bonus = 0.1
        else:
            chinese_bonus = 0
        
        final_score = min(similarity + prefix_bonus + chinese_bonus, 1.0)
        
        # 记录匹配详情用于调试
        logging.debug(f"模糊匹配: '{s1}' vs '{s2}' -> 相似度: {final_score:.3f} "
                      f"(LCS: {similarity:.3f}, 前缀: {prefix_bonus:.3f}, 中文加成: {chinese_bonus:.3f})")
        
        return final_score

    def find_matched_file(self, title):
        """根据标题查找匹配的歌曲文件 - 使用默认阈值"""
        return self.find_matched_file_with_threshold(title, self.match_threshold)

    def find_matched_file_with_threshold(self, title, threshold):
        """根据标题和阈值查找匹配的歌曲文件"""
        if not self.song_files:
            return None
            
        # 清理标题用于匹配
        clean_title = self.clean_string_for_matching(title)
        
        # 记录匹配过程用于调试
        debug_matches = []
        best_match = None
        best_score = 0
        
        logging.info(f"开始匹配歌曲: '{title}' (清理后: '{clean_title}')")
        
        for song in self.song_files:
            original_filename = song['name_only']
            clean_filename = self.clean_string_for_matching(original_filename)
            
            # 跳过空字符串
            if not clean_title or not clean_filename:
                continue
                
            # 多种匹配策略，按优先级排序
            
            # 1. 原始文件名完全匹配（最高优先级）
            if title == original_filename:
                logging.info(f"🎯 原始文件名完全匹配: '{title}' -> '{song['filename']}'")
                return song['path']
            
            # 2. 清理后完全相等
            if clean_title == clean_filename:
                logging.info(f"🎯 清理后完全匹配: '{title}' -> '{song['filename']}'")
                return song['path']
            
            # 3. 互相包含关系
            if clean_title in clean_filename or clean_filename in clean_title:
                logging.info(f"✅ 包含匹配: '{title}' -> '{song['filename']}'")
                return song['path']
            
            # 4. 增强的模糊匹配
            similarity = self.enhanced_fuzzy_match(clean_title, clean_filename)
            if similarity > threshold:  # 使用传入的阈值
                logging.info(f"✅ 模糊匹配: '{title}' -> '{song['filename']}' (相似度: {similarity:.2f})")
                return song['path']
            
            # 5. 单词匹配（针对英文歌曲）
            if self.word_based_match(clean_title, clean_filename):
                logging.info(f"✅ 单词匹配: '{title}' -> '{song['filename']}'")
                return song['path']
                
            # 记录可能的匹配用于调试
            if similarity > best_score:
                best_score = similarity
                best_match = song['path']
            
            if similarity > 0.3:  # 记录相似度超过30%的匹配
                debug_matches.append((song['filename'], similarity))
        
        # 如果没有找到直接匹配，记录调试信息
        if debug_matches:
            debug_matches.sort(key=lambda x: x[1], reverse=True)
            logging.info(f"标题 '{title}' 的潜在匹配 (前5个):")
            for i, (filename, score) in enumerate(debug_matches[:5]):
                logging.info(f"  {i+1}. {filename} (相似度: {score:.2f})")
        
        # 返回最佳匹配（即使分数不高）
        if best_match and best_score > 0.3:
            logging.info(f"⚠️  使用最佳匹配: '{title}' -> '{os.path.basename(best_match)}' (相似度: {best_score:.2f})")
            return best_match
        else:
            logging.warning(f"❌ 未找到匹配: '{title}'")
            return None

    def word_based_match(self, s1, s2):
        """基于单词的匹配，特别适用于英文歌曲"""
        # 如果字符串很短，不适用单词匹配
        if len(s1) < 3 or len(s2) < 3:
            return False
        
        # 提取主要单词（移除常见冠词、介词等）
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        def extract_key_words(s):
            # 简单的单词分割（针对连续字母）
            words = re.findall(r'[a-zA-Z]{2,}', s)
            return [word for word in words if word.lower() not in common_words]
        
        words1 = extract_key_words(s1)
        words2 = extract_key_words(s2)
        
        # 如果都有关键词，检查是否有重叠
        if words1 and words2:
            set1 = set(words1)
            set2 = set(words2)
            
            # 如果有共同的关键词，认为匹配
            if set1 & set2:
                return True
            
            # 检查是否有相似的关键词
            for w1 in words1:
                for w2 in words2:
                    if self.enhanced_fuzzy_match(w1, w2) > 0.8:
                        return True
        
        return False
        
    def get_row_status(self, excel_title, matched_file, lyrics_status, image_status, match_score):
        """根据匹配状态确定行的颜色标签"""
        if matched_file:
            if match_score > 0.9:
                return 'matched'  # 高匹配率 - 绿色
            elif match_score > 0.7:
                return 'partial'  # 中等匹配率 - 黄色
            else:
                return 'failed'   # 低匹配率 - 红色
        else:
            return 'unmatched'  # 未匹配 - 灰色
        
    def show_log_window(self):
        """显示日志窗口"""
        if self.log_window is None or not self.log_window.window.winfo_exists():
            self.log_window = LogWindow(self.root)
        else:
            self.log_window.window.lift()
    
    def load_excel(self):
        """加载Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                self.file_label.config(text=f"已加载: {os.path.basename(file_path)}")
                self.display_data()
                self.setup_field_mapping()
                self.refresh_matches()
                logging.info(f"成功加载Excel文件: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"加载Excel文件失败: {str(e)}")
                logging.error(f"加载Excel文件失败: {str(e)}")
    
    def load_output_folder(self):
        """选择输出文件夹"""
        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        
        if folder_path:
            self.output_folder = folder_path
            self.output_label.config(text=f"已选择: {os.path.basename(folder_path)}")
            logging.info(f"成功选择输出文件夹: {folder_path}")
    
    def scan_song_files(self):
        """扫描所有歌曲文件夹中的音频文件"""
        self.song_files = []
        audio_extensions = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.wma'}
        
        for song_folder in self.song_folders:
            if not os.path.exists(song_folder):
                logging.warning(f"歌曲文件夹不存在: {song_folder}")
                continue
                
            for root, dirs, files in os.walk(song_folder):
                for file in files:
                    if Path(file).suffix.lower() in audio_extensions:
                        full_path = os.path.join(root, file)
                        self.song_files.append({
                            'path': full_path,
                            'filename': file,
                            'name_only': Path(file).stem,
                            'relative_path': os.path.relpath(full_path, song_folder),
                            'source_folder': song_folder
                        })
        
        logging.info(f"从 {len(self.song_folders)} 个文件夹扫描到 {len(self.song_files)} 个音频文件")
    
    def scan_lyrics_files(self):
        """扫描所有歌词文件夹中的歌词文件"""
        self.lyrics_files = []
        lyrics_extensions = {'.lrc', '.txt', '.lyric', '.lrcx'}
        
        for lyrics_folder in self.lyrics_folders:
            if not os.path.exists(lyrics_folder):
                logging.warning(f"歌词文件夹不存在: {lyrics_folder}")
                continue
                
            for root, dirs, files in os.walk(lyrics_folder):
                for file in files:
                    if Path(file).suffix.lower() in lyrics_extensions:
                        full_path = os.path.join(root, file)
                        self.lyrics_files.append({
                            'path': full_path,
                            'filename': file,
                            'name_only': Path(file).stem,
                            'source_folder': lyrics_folder
                        })
        
        logging.info(f"从 {len(self.lyrics_folders)} 个文件夹扫描到 {len(self.lyrics_files)} 个歌词文件")
    
    def scan_image_files(self):
        """扫描所有图片文件夹中的图片文件"""
        self.image_files = []
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        
        for image_folder in self.image_folders:
            if not os.path.exists(image_folder):
                logging.warning(f"图片文件夹不存在: {image_folder}")
                continue
                
            for root, dirs, files in os.walk(image_folder):
                for file in files:
                    if Path(file).suffix.lower() in image_extensions:
                        full_path = os.path.join(root, file)
                        self.image_files.append({
                            'path': full_path,
                            'filename': file,
                            'name_only': Path(file).stem,
                            'source_folder': image_folder
                        })
        
        logging.info(f"从 {len(self.image_folders)} 个文件夹扫描到 {len(self.image_files)} 个图片文件")
    
    def display_data(self):
        """显示数据到Treeview"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.df is not None:
            # 先添加已匹配的歌曲
            matched_items = []
            unmatched_items = []
            
            for index, row in self.df.iterrows():
                # 只显示部分关键字段
                excel_title = str(row.get('标题', ''))
                matched_file = self.match_results.get(index) if index in self.match_results else self.find_matched_file(excel_title)
                lyrics_status = self.get_lyrics_status(excel_title)
                image_status = self.get_image_status(excel_title)
                
                # 计算匹配率
                match_score = self.match_scores.get(index, 0)
                match_rate = f"{match_score:.1%}" if matched_file else "0%"
                
                values = [
                    "✓",  # 选择状态
                    excel_title,
                    os.path.basename(matched_file) if matched_file else "未匹配",
                    match_rate,
                    str(row.get('艺术家', '')),
                    str(row.get('年份', '')),
                    str(row.get('语种', '')),
                    str(row.get('所属专辑', '')),
                    lyrics_status,
                    image_status,
                    "已匹配" if matched_file else "未匹配"
                ]
                
                # 根据匹配状态确定行的颜色
                row_tag = self.get_row_status(excel_title, matched_file, lyrics_status, image_status, match_score)
                
                if matched_file:
                    matched_items.append((index, values, row_tag))
                else:
                    unmatched_items.append((index, values, row_tag))
                
                # 存储匹配结果
                if matched_file:
                    self.match_results[index] = matched_file
            
            # 先添加已匹配的项目，再添加未匹配的项目
            for index, values, tag in matched_items:
                item_id = self.tree.insert("", tk.END, values=values, tags=(tag,))
            
            for index, values, tag in unmatched_items:
                item_id = self.tree.insert("", tk.END, values=values, tags=(tag,))
            
            # 更新统计信息
            self.update_stats()
    
    def sort_matched_first(self):
        """将已匹配的歌曲置顶"""
        self.display_data()
    
    def search_data(self, event=None):
        """搜索歌曲数据"""
        search_term = self.search_var.get().lower()
        
        # 如果搜索词为空，显示所有数据
        if not search_term:
            self.display_data()
            return
        
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.df is not None:
            matched_items = []
            unmatched_items = []
            
            for index, row in self.df.iterrows():
                # 检查是否匹配搜索条件
                match_found = False
                for col in ['标题', '艺术家', '专辑', '年份', '语种']:
                    if search_term in str(row.get(col, '')).lower():
                        match_found = True
                        break
                
                if match_found:
                    excel_title = str(row.get('标题', ''))
                    matched_file = self.match_results.get(index) if index in self.match_results else self.find_matched_file(excel_title)
                    lyrics_status = self.get_lyrics_status(excel_title)
                    image_status = self.get_image_status(excel_title)
                    
                    # 计算匹配率
                    match_score = self.match_scores.get(index, 0)
                    match_rate = f"{match_score:.1%}" if matched_file else "0%"
                    
                    values = [
                        "✓",  # 选择状态
                        excel_title,
                        os.path.basename(matched_file) if matched_file else "未匹配",
                        match_rate,
                        str(row.get('艺术家', '')),
                        str(row.get('年份', '')),
                        str(row.get('语种', '')),
                        str(row.get('所属专辑', '')),
                        lyrics_status,
                        image_status,
                        "已匹配" if matched_file else "未匹配"
                    ]
                    
                    # 根据匹配状态确定行的颜色
                    row_tag = self.get_row_status(excel_title, matched_file, lyrics_status, image_status, match_score)
                    
                    if matched_file:
                        matched_items.append((index, values, row_tag))
                    else:
                        unmatched_items.append((index, values, row_tag))
            
            # 先添加已匹配的项目，再添加未匹配的项目
            for index, values, tag in matched_items:
                self.tree.insert("", tk.END, values=values, tags=(tag,))
                
            for index, values, tag in unmatched_items:
                self.tree.insert("", tk.END, values=values, tags=(tag,))
                
            # 更新统计信息
            self.update_stats()
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set("")
        self.display_data()
    
    def search_mapping(self, event=None):
        """搜索字段映射"""
        search_term = self.map_search_var.get().lower()
        
        # 如果搜索词为空，显示所有映射
        if not search_term:
            self.setup_field_mapping()
            return
        
        # 清空现有映射
        for item in self.map_tree.get_children():
            self.map_tree.delete(item)
        
        if self.df is not None:
            excel_columns = self.df.columns.tolist()
            for excel_col in excel_columns:
                if search_term in excel_col.lower():
                    if excel_col in self.mapping_rules:
                        target_field = self.mapping_rules[excel_col]
                        self.map_tree.insert("", tk.END, values=[excel_col, target_field, "自动"])
                    else:
                        self.map_tree.insert("", tk.END, values=[excel_col, "未匹配", "手动"])
    
    def clear_map_search(self):
        """清除字段映射搜索"""
        self.map_search_var.set("")
        self.setup_field_mapping()
    
    def toggle_exact_match(self):
        """切换精确匹配模式"""
        self.exact_match = self.exact_match_var.get()
        logging.info(f"精确匹配模式: {'开启' if self.exact_match else '关闭'}")
        self.refresh_matches()
    
    def get_lyrics_status(self, title):
        """获取歌词文件状态"""
        if not self.lyrics_files:
            return "无歌词文件夹"
            
        # 清理标题用于匹配
        clean_title = self.clean_string_for_matching(title)
        
        for lyrics in self.lyrics_files:
            clean_filename = self.clean_string_for_matching(lyrics['name_only'])
            
            # 根据精确匹配设置选择匹配策略
            if self.exact_match:
                # 精确匹配
                if clean_title == clean_filename:
                    return "歌词已匹配"
            else:
                # 多种匹配策略
                if clean_title == clean_filename:
                    return "歌词已匹配"
                elif clean_title in clean_filename or clean_filename in clean_title:
                    return "歌词已匹配"
                elif self.enhanced_fuzzy_match(clean_title, clean_filename) > 0.7:
                    return "歌词已匹配"
                elif self.word_based_match(clean_title, clean_filename):
                    return "歌词已匹配"
                
        return "歌词未匹配"
    
    def get_image_status(self, title):
        """获取图片文件状态"""
        if not self.image_files:
            return "无图片文件夹"
            
        # 清理标题用于匹配
        clean_title = self.clean_string_for_matching(title)
        
        for image in self.image_files:
            clean_filename = self.clean_string_for_matching(image['name_only'])
            
            # 根据精确匹配设置选择匹配策略
            if self.exact_match:
                # 精确匹配
                if clean_title == clean_filename:
                    return "图片已匹配"
            else:
                # 多种匹配策略
                if clean_title == clean_filename:
                    return "图片已匹配"
                elif clean_title in clean_filename or clean_filename in clean_title:
                    return "图片已匹配"
                elif self.enhanced_fuzzy_match(clean_title, clean_filename) > 0.7:
                    return "图片已匹配"
                elif self.word_based_match(clean_title, clean_filename):
                    return "图片已匹配"
                
        return "图片未匹配"
    
    def find_lyrics_file(self, title):
        """根据标题查找匹配的歌词文件"""
        if not self.lyrics_files:
            return None
            
        # 清理标题用于匹配
        clean_title = self.clean_string_for_matching(title)
        
        for lyrics in self.lyrics_files:
            clean_filename = self.clean_string_for_matching(lyrics['name_only'])
            
            # 根据精确匹配设置选择匹配策略
            if self.exact_match:
                # 精确匹配
                if clean_title == clean_filename:
                    return lyrics['path']
            else:
                # 多种匹配策略
                if clean_title == clean_filename:
                    return lyrics['path']
                elif clean_title in clean_filename or clean_filename in clean_title:
                    return lyrics['path']
                elif self.enhanced_fuzzy_match(clean_title, clean_filename) > 0.7:
                    return lyrics['path']
                elif self.word_based_match(clean_title, clean_filename):
                    return lyrics['path']
                
        return None
    
    def find_image_files(self, title, row=None):
        """根据标题查找匹配的图片文件，优先使用Excel中指定的图片路径"""
        images = []
        
        # 首先检查Excel行中是否有直接指定的图片路径
        if row is not None:
            # 检查常见的图片字段
            image_fields = ['封面', '图片', '封面图片', '封面路径', '图片路径']
            for field in image_fields:
                if field in row and pd.notna(row[field]):
                    image_path = str(row[field])
                    # 处理多个图片路径（用分号分隔）
                    image_paths = [path.strip() for path in image_path.split(';')]
                    for path in image_paths:
                        if os.path.exists(path):
                            images.append(path)
                            logging.info(f"从Excel字段 '{field}' 找到图片: {path}")
                        else:
                            # 如果路径不存在，尝试在图片文件夹中查找
                            for image_folder in self.image_folders:
                                filename_only = os.path.basename(path)
                                full_path = os.path.join(image_folder, filename_only)
                                if os.path.exists(full_path):
                                    images.append(full_path)
                                    logging.info(f"从图片文件夹找到Excel指定的图片: {full_path}")
                                    break
                            else:
                                logging.warning(f"Excel中指定的图片文件不存在: {path}")
        
        # 如果Excel中没有指定图片，或者指定的图片不存在，则通过文件名匹配
        if not images and self.image_files:
            # 清理标题用于匹配
            clean_title = self.clean_string_for_matching(title)
            
            for image in self.image_files:
                clean_filename = self.clean_string_for_matching(image['name_only'])
                
                # 根据精确匹配设置选择匹配策略
                if self.exact_match:
                    # 精确匹配
                    if clean_title == clean_filename:
                        images.append(image['path'])
                else:
                    # 多种匹配策略
                    if clean_title == clean_filename:
                        images.append(image['path'])
                    elif clean_title in clean_filename or clean_filename in clean_title:
                        images.append(image['path'])
                    elif self.enhanced_fuzzy_match(clean_title, clean_filename) > 0.7:
                        images.append(image['path'])
                    elif self.word_based_match(clean_title, clean_filename):
                        images.append(image['path'])
        
        # 去重
        return list(set(images))
    
    def refresh_matches(self):
        """刷新匹配结果，添加调试信息"""
        if self.df is not None:
            # 重新计算所有匹配
            self.match_results = {}
            self.match_scores = {}
            
            for index, row in self.df.iterrows():
                title = str(row.get('标题', ''))
                matched_file = self.find_matched_file(title)
                
                if matched_file:
                    self.match_results[index] = matched_file
                    # 计算匹配率
                    clean_title = self.clean_string_for_matching(title)
                    filename = Path(matched_file).stem
                    clean_filename = self.clean_string_for_matching(filename)
                    self.match_scores[index] = self.enhanced_fuzzy_match(clean_title, clean_filename)
            
            # 统计匹配情况
            total = len(self.df)
            matched = len(self.match_results)
            
            logging.info(f"匹配统计: {matched}/{total} 首歌曲匹配成功 ({matched/total*100:.1f}%)")
            self.display_data()
    
    def setup_field_mapping(self):
        """设置字段映射"""
        if self.df is not None:
            # 清空现有映射
            for item in self.map_tree.get_children():
                self.map_tree.delete(item)
            
            # 标准字段列表
            standard_fields = ["标题", "艺术家", "专辑", "年份", "语种", "歌词", "作词", "作曲", "封面", 
                              "注释", "出品", "版权", "QQ音乐", "网易云音乐", "酷狗音乐", "5sing", "酷我音乐"]
            
            # 自动匹配字段
            excel_columns = self.df.columns.tolist()
            
            for excel_col in excel_columns:
                matched = False
                for std_field in standard_fields:
                    if std_field in excel_col or excel_col in std_field:
                        self.map_tree.insert("", tk.END, values=[excel_col, std_field, "自动"])
                        self.mapping_rules[excel_col] = std_field
                        matched = True
                        break
                
                if not matched:
                    self.map_tree.insert("", tk.END, values=[excel_col, "未匹配", "手动"])
    
    def auto_match(self):
        """自动匹配字段"""
        if self.df is not None:
            for item in self.map_tree.get_children():
                values = self.map_tree.item(item)['values']
                excel_field = values[0]
                
                # 简单的自动匹配逻辑
                if "标题" in excel_field or "歌曲" in excel_field or "歌名" in excel_field:
                    self.map_tree.set(item, column=1, value="标题")
                    self.mapping_rules[excel_field] = "标题"
                elif "艺术家" in excel_field or "歌手" in excel_field or "演唱" in excel_field:
                    self.map_tree.set(item, column=1, value="艺术家")
                    self.mapping_rules[excel_field] = "艺术家"
                elif "专辑" in excel_field or "唱片" in excel_field:
                    self.map_tree.set(item, column=1, value="专辑")
                    self.mapping_rules[excel_field] = "专辑"
                elif "年份" in excel_field or "年代" in excel_field:
                    self.map_tree.set(item, column=1, value="年份")
                    self.mapping_rules[excel_field] = "年份"
                elif "语种" in excel_field or "语言" in excel_field:
                    self.map_tree.set(item, column=1, value="语种")
                    self.mapping_rules[excel_field] = "语种"
                elif "歌词" in excel_field:
                    self.map_tree.set(item, column=1, value="歌词")
                    self.mapping_rules[excel_field] = "歌词"
                elif "作词" in excel_field:
                    self.map_tree.set(item, column=1, value="作词")
                    self.mapping_rules[excel_field] = "作词"
                elif "作曲" in excel_field:
                    self.map_tree.set(item, column=1, value="作曲")
                    self.mapping_rules[excel_field] = "作曲"
                elif "封面" in excel_field or "图片" in excel_field:
                    self.map_tree.set(item, column=1, value="封面")
                    self.mapping_rules[excel_field] = "封面"
            
            messagebox.showinfo("提示", "自动匹配完成")
    
    def manual_match(self):
        """手动匹配字段"""
        selected = self.map_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个字段进行手动匹配")
            return
        
        item = selected[0]
        values = self.map_tree.item(item)['values']
        excel_field = values[0]
        
        # 创建手动匹配对话框
        self.create_manual_match_dialog(excel_field, item)
    
    def create_manual_match_dialog(self, excel_field, tree_item):
        """创建手动匹配对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("手动字段匹配")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Excel字段: {excel_field}").pack(pady=10)
        ttk.Label(dialog, text="选择目标字段:").pack(pady=5)
        
        # 目标字段选择
        target_var = tk.StringVar()
        standard_fields = ["标题", "艺术家", "专辑", "年份", "语种", "歌词", "作词", "作曲", "出品", 
                          "版权", "封面", "注释", "QQ音乐", "网易云音乐", "酷狗音乐", "5sing", "酷我音乐"]
        
        combo = ttk.Combobox(dialog, textvariable=target_var, values=standard_fields, state="readonly")
        combo.pack(pady=5)
        combo.set("选择字段")
        
        def confirm_match():
            target_field = target_var.get()
            if target_field and target_field != "选择字段":
                self.map_tree.set(tree_item, column=1, value=target_field)
                self.map_tree.set(tree_item, column=2, value="手动")
                self.mapping_rules[excel_field] = target_field
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "请选择一个目标字段")
        
        ttk.Button(dialog, text="确认", command=confirm_match).pack(pady=10)
    
    def fuzzy_match(self):
        """模糊匹配歌曲文件"""
        if self.df is None or not self.song_files:
            messagebox.showwarning("警告", "请先加载Excel文件和歌曲文件夹")
            return
            
        # 执行模糊匹配
        match_count = 0
        for index, row in self.df.iterrows():
            title = str(row.get('标题', ''))
            if index not in self.match_results:
                matched_file = self.find_matched_file(title)
                if matched_file:
                    self.match_results[index] = matched_file
                    # 计算匹配率
                    clean_title = self.clean_string_for_matching(title)
                    filename = Path(matched_file).stem
                    clean_filename = self.clean_string_for_matching(filename)
                    self.match_scores[index] = self.enhanced_fuzzy_match(clean_title, clean_filename)
                    match_count += 1
        
        self.refresh_matches()
        messagebox.showinfo("提示", f"模糊匹配完成，新增 {match_count} 个匹配")
        logging.info(f"模糊匹配完成，新增 {match_count} 个匹配")
    
    def debug_matching(self):
        """调试匹配问题"""
        if self.df is None:
            messagebox.showwarning("警告", "请先加载Excel文件")
            return
        
        debug_window = tk.Toplevel(self.root)
        debug_window.title("匹配调试")
        debug_window.geometry("800x600")
        
        text_area = scrolledtext.ScrolledText(debug_window, wrap=tk.WORD, width=80, height=30)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 分析每个标题的匹配情况
        text_area.insert(tk.END, "=== 匹配调试报告 ===\n\n")
        
        for index, row in self.df.iterrows():
            title = str(row.get('标题', ''))
            clean_title = self.clean_string_for_matching(title)
            
            text_area.insert(tk.END, f"标题: {title}\n")
            text_area.insert(tk.END, f"清理后: {clean_title}\n")
            
            matched_file = self.find_matched_file(title)
            if matched_file:
                text_area.insert(tk.END, f"状态: ✅ 匹配成功\n")
                text_area.insert(tk.END, f"匹配文件: {os.path.basename(matched_file)}\n")
                text_area.insert(tk.END, f"匹配率: {self.match_scores.get(index, 0):.1%}\n")
            else:
                text_area.insert(tk.END, f"状态: ❌ 匹配失败\n")
                
                # 显示最接近的匹配
                if self.song_files:
                    best_match = None
                    best_score = 0
                    
                    for song in self.song_files:
                        clean_filename = self.clean_string_for_matching(song['name_only'])
                        score = self.enhanced_fuzzy_match(clean_title, clean_filename)
                        if score > best_score:
                            best_score = score
                            best_match = song
                    
                    if best_match and best_score > 0.3:
                        text_area.insert(tk.END, f"最接近匹配: {best_match['filename']} (相似度: {best_score:.2f})\n")
            
            text_area.insert(tk.END, "-" * 50 + "\n")
        
        text_area.see(tk.END)
    
    def start_save_process(self):
        """开始保存过程（在新线程中运行）"""
        if self.df is None:
            messagebox.showwarning("警告", "请先加载Excel文件")
            return
            
        if not self.song_files:
            messagebox.showwarning("警告", "请先选择歌曲文件夹")
            return
            
        if not self.output_folder:
            messagebox.showwarning("警告", "请先选择输出文件夹")
            return
        
        # 在新线程中运行保存过程
        thread = threading.Thread(target=self.save_data)
        thread.daemon = True
        thread.start()
    
    def save_data(self):
        """保存数据到音频文件"""
        # 显示进度对话框
        progress_dialog = ProgressDialog(self.root, "保存元数据")
        
        # 处理数据
        success_count = 0
        fail_count = 0
        skip_count = 0
        failed_songs = []
        
        total_items = len(self.match_results)
        self.progress['maximum'] = total_items
        self.progress['value'] = 0
        
        for i, (index, file_path) in enumerate(self.match_results.items()):
            try:
                # 更新进度
                progress_dialog.update_detail(f"处理第 {i+1}/{total_items} 首歌曲...")
                
                # 获取Excel行数据
                row = self.df.iloc[index]
                
                # 应用映射规则处理数据
                metadata = {}
                for excel_field, value in row.items():
                    if pd.notna(value) and excel_field in self.mapping_rules:
                        target_field = self.mapping_rules[excel_field]
                        metadata[target_field] = str(value)
                
                # 查找歌词文件
                if self.lyrics_var.get() and self.lyrics_files:
                    title = str(row.get('标题', ''))
                    lyrics_file = self.find_lyrics_file(title)
                    if lyrics_file:
                        try:
                            with open(lyrics_file, 'r', encoding='utf-8') as f:
                                lyrics_content = f.read()
                                metadata['歌词'] = lyrics_content
                                logging.info(f"成功导入歌词: {lyrics_file}")
                        except Exception as e:
                            logging.warning(f"读取歌词文件失败 {lyrics_file}: {str(e)}")
                
                # 查找图片文件 - 优先使用Excel中指定的图片路径
                images = []
                if self.images_var.get():
                    title = str(row.get('标题', ''))
                    images = self.find_image_files(title, row)
                    if images:
                        logging.info(f"找到 {len(images)} 张图片: {', '.join([os.path.basename(img) for img in images])}")
                
                # 确定输出路径
                if self.output_folder:
                    # 保持原始文件夹结构
                    for song in self.song_files:
                        if song['path'] == file_path:
                            # 使用源文件夹名称来保持结构
                            source_folder_name = os.path.basename(song['source_folder'])
                            relative_path = song.get('relative_path', os.path.basename(file_path))
                            output_path = os.path.join(self.output_folder, source_folder_name, relative_path)
                            
                            # 确保输出目录存在
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            
                            # 复制原始文件到输出目录
                            shutil.copy2(file_path, output_path)
                            
                            # 写入元数据到输出文件
                            self.write_metadata(output_path, metadata, images)
                            break
                
                success_count += 1
                song_title = metadata.get('标题', f"第{index+1}首")
                logging.info(f"成功处理歌曲: {song_title}")
                
            except Exception as e:
                fail_count += 1
                song_title = row.get('标题', f"第{index+1}首")
                failed_songs.append(f"{song_title} - {str(e)}")
                logging.error(f"处理歌曲失败 {song_title}: {str(e)}")
            
            # 更新进度条
            self.progress['value'] = success_count + fail_count
        
        # 关闭进度对话框
        self.root.after(0, progress_dialog.close)
        
        # 在主线程中更新UI
        self.root.after(0, self.show_save_result, success_count, fail_count, skip_count, failed_songs)
    
    def show_save_result(self, success_count, fail_count, skip_count, failed_songs):
        """显示保存结果"""
        # 显示结果
        result_text = f"处理完成: 成功{success_count}首, 失败{fail_count}首, 跳过{skip_count}首"
        self.result_label.config(text=result_text)
        
        # 保存错误日志到桌面
        if failed_songs:
            self.save_error_log(failed_songs, success_count, fail_count, skip_count)
            
            # 显示错误详情
            error_msg = f"失败的歌曲:\n" + "\n".join(failed_songs[:10])  # 只显示前10个
            if len(failed_songs) > 10:
                error_msg += f"\n... 还有{len(failed_songs)-10}个失败项，详见错误日志"
                
            messagebox.showwarning("处理结果", f"{result_text}\n\n失败的歌曲已保存到桌面错误日志文件")
        else:
            messagebox.showinfo("处理结果", result_text)
    
    def write_metadata(self, file_path, metadata, images=None):
        """写入元数据到音频文件"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.mp3':
                self.write_mp3_metadata(file_path, metadata, images)
            elif file_ext == '.flac':
                self.write_flac_metadata(file_path, metadata, images)
            elif file_ext in ['.m4a', '.mp4']:
                self.write_mp4_metadata(file_path, metadata, images)
            elif file_ext == '.wav':
                self.write_wav_metadata(file_path, metadata, images)
            elif file_ext == '.aac':
                self.write_aac_metadata(file_path, metadata, images)
            else:
                # 对于其他格式，使用mutagen通用方法
                audio = File(file_path, easy=True)
                if audio is not None:
                    self.write_generic_metadata(audio, metadata)
                    audio.save()
                else:
                    raise Exception(f"不支持的音频格式: {file_ext}")
        except Exception as e:
            raise Exception(f"写入元数据失败: {str(e)}")
    
    def write_mp3_metadata(self, file_path, metadata, images=None):
        """写入MP3文件的ID3标签"""
        try:
            # 尝试使用EasyID3简化操作
            try:
                audio = EasyID3(file_path)
            except:
                audio = EasyID3()
            
            # 设置常用标签
            if '标题' in metadata:
                audio['title'] = metadata['标题']
            if '艺术家' in metadata:
                audio['artist'] = metadata['艺术家']
            if '专辑' in metadata:
                audio['album'] = metadata['专辑']
            if '年份' in metadata:
                audio['date'] = metadata['年份']
            if '作曲' in metadata:
                audio['composer'] = metadata['作曲']
            if '语种' in metadata:
                audio['language'] = metadata['语种']
            if '注释' in metadata:
                audio['comment'] = metadata['注释']
            if '出品' in metadata:
                audio['organization'] = metadata['出品']
            if '版权' in metadata:
                audio['copyright'] = metadata['版权']
            
            audio.save(file_path)
            
            # 写入歌词（需要标准ID3标签）
            if '歌词' in metadata:
                self.write_mp3_lyrics(file_path, metadata['歌词'])
            
            # 写入图片
            if images:
                self.write_mp3_images(file_path, images)
            
        except Exception as e:
            # 如果EasyID3失败，回退到标准ID3
            try:
                audio = MP3(file_path, ID3=ID3)
            except:
                audio = MP3(file_path)
                
            if audio.tags is None:
                audio.add_tags()
                
            tags = audio.tags
            
            # 设置常用ID3标签
            if '标题' in metadata:
                tags.add(TIT2(encoding=3, text=metadata['标题']))
            if '艺术家' in metadata:
                tags.add(TPE1(encoding=3, text=metadata['艺术家']))
            if '专辑' in metadata:
                tags.add(TALB(encoding=3, text=metadata['专辑']))
            if '年份' in metadata:
                tags.add(TYER(encoding=3, text=metadata['年份']))
            if '作曲' in metadata:
                tags.add(TCOM(encoding=3, text=metadata['作曲']))
            if '语种' in metadata:
                tags.add(TCON(encoding=3, text=metadata['语种']))
            if '注释' in metadata:
                tags.add(COMM(encoding=3, text=metadata['注释']))
            if '出品' in metadata:
                tags.add(TPE2(encoding=3, text=metadata['出品']))
            if '版权' in metadata:
                tags.add(TCOP(encoding=3, text=metadata['版权']))
            
            # 写入歌词
            if '歌词' in metadata:
                tags.add(USLT(encoding=3, lang='eng', desc='', text=metadata['歌词']))
            
            # 写入图片
            if images:
                self.write_mp3_images(file_path, images)
            
            audio.save()
    
    def write_mp3_lyrics(self, file_path, lyrics):
        """专门写入MP3歌词"""
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            
            # 添加歌词帧
            audio.tags.add(USLT(encoding=3, lang='eng', desc='', text=lyrics))
            audio.save()
        except Exception as e:
            logging.warning(f"写入MP3歌词失败: {str(e)}")
    
    def write_mp3_images(self, file_path, images):
        """写入MP3图片"""
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            
            # 添加图片帧
            for i, image_path in enumerate(images):
                try:
                    with open(image_path, 'rb') as img:
                        image_data = img.read()
                    
                    # 确定图片类型
                    if image_path.lower().endswith('.png'):
                        mime_type = 'image/png'
                    else:
                        mime_type = 'image/jpeg'
                    
                    # 确定图片描述和类型
                    if i == 0:
                        desc = 'Cover (front)'
                        pic_type = 3  # 3 = front cover
                    elif i == 1:
                        desc = 'Cover (back)'
                        pic_type = 4  # 4 = back cover
                    else:
                        desc = f'Other Image {i-1}'
                        pic_type = 0  # 0 = other
                    
                    # 添加APIC帧
                    audio.tags.add(APIC(
                        encoding=3,
                        mime=mime_type,
                        type=pic_type,
                        desc=desc,
                        data=image_data
                    ))
                    logging.info(f"成功添加图片: {os.path.basename(image_path)} 作为 {desc}")
                except Exception as e:
                    logging.warning(f"添加图片失败 {image_path}: {str(e)}")
            
            audio.save()
        except Exception as e:
            logging.warning(f"写入MP3图片失败: {str(e)}")
    
    def write_flac_metadata(self, file_path, metadata, images=None):
        """写入FLAC文件的元数据"""
        audio = FLAC(file_path)
        
        # FLAC使用VORBIS_COMMENT格式
        if '标题' in metadata:
            audio['title'] = metadata['标题']
        if '艺术家' in metadata:
            audio['artist'] = metadata['艺术家']
        if '专辑' in metadata:
            audio['album'] = metadata['专辑']
        if '年份' in metadata:
            audio['date'] = metadata['年份']
        if '作曲' in metadata:
            audio['composer'] = metadata['作曲']
        if '语种'in metadata:
            audio['genre'] = metadata['语种']
        if '注释' in metadata:
            audio['comment'] = metadata['注释']
        if '出品' in metadata:
            audio['organization'] = metadata['出品']
        if '版权' in metadata:
            audio['copyright'] = metadata['版权']
        if '歌词' in metadata:
            audio['lyrics'] = metadata['歌词']
        
        # 写入图片
        if images:
            for i, image_path in enumerate(images):
                try:
                    with open(image_path, 'rb') as img:
                        image_data = img.read()
                    
                    # 确定图片类型
                    if image_path.lower().endswith('.png'):
                        mime_type = 'image/png'
                    else:
                        mime_type = 'image/jpeg'
                    
                    # 确定图片类型
                    if i == 0:
                        pic_type = 3  # 3 = front cover
                    elif i == 1:
                        pic_type = 4  # 4 = back cover
                    else:
                        pic_type = 0  # 0 = other
                    
                    # 添加图片
                    picture = FLAC.Picture()
                    picture.type = pic_type
                    picture.mime = mime_type
                    picture.desc = f"Image {i+1}"
                    picture.data = image_data
                    
                    audio.add_picture(picture)
                    logging.info(f"成功添加图片: {os.path.basename(image_path)}")
                except Exception as e:
                    logging.warning(f"添加图片失败 {image_path}: {str(e)}")
        
        audio.save()
    
    def write_mp4_metadata(self, file_path, metadata, images=None):
        """写入MP4/M4A文件的元数据"""
        audio = MP4(file_path)
        
        # MP4使用特定的标签名
        if '标题' in metadata:
            audio['\xa9nam'] = [metadata['标题']]
        if '艺术家' in metadata:
            audio['\xa9ART'] = [metadata['艺术家']]
        if '专辑' in metadata:
            audio['\xa9alb'] = [metadata['专辑']]
        if '年份' in metadata:
            audio['\xa9day'] = [metadata['年份']]
        if '作曲' in metadata:
            audio['\xa9wrt'] = [metadata['作曲']]
        if '语种' in metadata:
            audio['\xa9gen'] = [metadata['语种']]
        if '注释' in metadata:
            audio['\xa9cmt'] = [metadata['注释']]
        if '出品' in metadata:
            audio['\xa9org'] = [metadata['出品']]
        if '版权' in metadata:
            audio['cprt'] = [metadata['版权']]
        if '歌词' in metadata:
            audio['\xa9lyr'] = [metadata['歌词']]
        
        # MP4格式通常只支持一张封面图片，使用第一张图片
        if images and len(images) > 0:
            try:
                with open(images[0], 'rb') as img:
                    image_data = img.read()
                audio["covr"] = [image_data]
                logging.info(f"成功添加封面图片: {os.path.basename(images[0])}")
            except Exception as e:
                logging.warning(f"添加封面图片失败 {images[0]}: {str(e)}")
        
        audio.save()
    
    def write_wav_metadata(self, file_path, metadata, images=None):
        """写入WAV文件的元数据"""
        audio = WAVE(file_path)
        
        # WAV文件通常使用ID3标签
        if audio.tags is None:
            audio.add_tags()
            
        tags = audio.tags
        
        # 设置常用ID3标签
        if '标题' in metadata:
            tags.add(TIT2(encoding=3, text=metadata['标题']))
        if '艺术家' in metadata:
            tags.add(TPE1(encoding=3, text=metadata['艺术家']))
        if '专辑' in metadata:
            tags.add(TALB(encoding=3, text=metadata['专辑']))
        if '年份' in metadata:
            tags.add(TYER(encoding=3, text=metadata['年份']))
        if '作曲' in metadata:
            tags.add(TCOM(encoding=3, text=metadata['作曲']))
        if '语种' in metadata:
            tags.add(TCON(encoding=3, text=metadata['语种']))
        if '注释' in metadata:
            tags.add(COMM(encoding=3, text=metadata['注释']))
        if '出品' in metadata:
            tags.add(TPE2(encoding=3, text=metadata['出品']))
        if '版权' in metadata:
            tags.add(TCOP(encoding=3, text=metadata['版权']))
        if '歌词' in metadata:
            tags.add(USLT(encoding=3, lang='eng', desc='', text=metadata['歌词']))
        
        # 写入图片
        if images:
            self.write_mp3_images(file_path, images)
        
        audio.save()
    
    def write_aac_metadata(self, file_path, metadata, images=None):
        """写入AAC文件的元数据"""
        # AAC文件通常使用MP4容器，所以使用MP4处理方法
        try:
            self.write_mp4_metadata(file_path, metadata, images)
        except:
            # 如果失败，尝试通用方法
            audio = File(file_path, easy=True)
            if audio is not None:
                self.write_generic_metadata(audio, metadata)
                audio.save()
            else:
                raise Exception("无法处理AAC文件")
    
    def write_generic_metadata(self, audio, metadata):
        """写入通用元数据"""
        if '标题' in metadata:
            audio['title'] = metadata['标题']
        if '艺术家' in metadata:
            audio['artist'] = metadata['艺术家']
        if '专辑' in metadata:
            audio['album'] = metadata['专辑']
        if '年份' in metadata:
            audio['date'] = metadata['年份']
        if '作曲' in metadata:
            audio['composer'] = metadata['作曲']
        if '语种' in metadata:
            audio['genre'] = metadata['语种']
        if '注释' in metadata:
            audio['comment'] = metadata['注释']
        if '歌词' in metadata:
            audio['lyrics'] = metadata['歌词']
    
    def save_error_log(self, failed_songs, success_count, fail_count, skip_count):
        """保存错误日志到桌面"""
        try:
            desktop = Path.home() / "Desktop"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = desktop / f"歌曲元数据处理错误_{timestamp}.txt"
            
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write("歌曲元数据处理错误报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"处理结果: 成功{success_count}首, 失败{fail_count}首, 跳过{skip_count}首\n\n")
                f.write("失败的歌曲列表:\n")
                f.write("-" * 30 + "\n")
                for i, song in enumerate(failed_songs, 1):
                    f.write(f"{i}. {song}\n")
            
            logging.info(f"错误日志已保存到: {error_file}")
        except Exception as e:
            logging.error(f"保存错误日志失败: {str(e)}")

def main():
    root = tk.Tk()
    app = SongMetadataEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
