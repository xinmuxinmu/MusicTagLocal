import sys
import os
import pandas as pd
import logging
from datetime import datetime
import shutil
from pathlib import Path
import re
import threading
import time
import json
import unicodedata
from difflib import SequenceMatcher

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QProgressBar,
                            QTabWidget, QGroupBox, QCheckBox, QLineEdit, QComboBox,
                            QMessageBox, QFileDialog, QScrollArea, QTextEdit, QSplitter,
                            QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
                            QHeaderView, QMenu, QAction, QInputDialog, QTableWidget,
                            QTableWidgetItem, QAbstractItemView, QSpinBox, QDoubleSpinBox,
                            QProgressDialog, QToolBar, QStatusBar, QToolButton, QStyleFactory,
                            QStyle, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QMetaObject, Q_ARG, QSettings, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush, QPixmap, QFontDatabase

# 导入原有的业务逻辑类
from mutagen import File
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, TCOM, TCON, COMM, APIC, TPE2, TCOP, TLAN, USLT
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.easyid3 import EasyID3
from mutagen.wave import WAVE
from mutagen.asf import ASF  # 添加对AAC/WMA文件的支持

class ThemeManager:
    """主题管理器"""
    def __init__(self):
        self.themes = {
            "默认浅色": {
                "primary": "#2c3e50",
                "secondary": "#34495e", 
                "accent": "#3498db",
                "background": "#ecf0f1",
                "surface": "#ffffff",
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c"
            },
            "深色模式": {
                "primary": "#3498db",
                "secondary": "#2c3e50", 
                "accent": "#e74c3c",
                "background": "#1a1a1a",
                "surface": "#2d2d2d",
                "text": "#ecf0f1",
                "text_secondary": "#bdc3c7",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c"
            },
            "蓝色主题": {
                "primary": "#2980b9",
                "secondary": "#3498db",
                "accent": "#e74c3c",
                "background": "#f5f7fa",
                "surface": "#ffffff",
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d",
                "success": "#27ae60", 
                "warning": "#f39c12",
                "error": "#e74c3c"
            },
            "绿色主题": {
                "primary": "#27ae60",
                "secondary": "#2ecc71",
                "accent": "#e67e22",
                "background": "#f0f8f0",
                "surface": "#ffffff",
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c"
            },
            "紫色主题": {
                "primary": "#8e44ad",
                "secondary": "#9b59b6", 
                "accent": "#e74c3c",
                "background": "#f8f5fc",
                "surface": "#ffffff",
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c"
            },
            "橙色主题": {
                "primary": "#d35400",
                "secondary": "#e67e22",
                "accent": "#3498db",
                "background": "#fef9f3",
                "surface": "#ffffff", 
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c"
            },
            "粉色主题": {
                "primary": "#e84393",
                "secondary": "#fd79a8",
                "accent": "#3498db",
                "background": "#fff5f9",
                "surface": "#ffffff",
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c"
            },
            "青色主题": {
                "primary": "#00b894",
                "secondary": "#00cec9",
                "accent": "#e74c3c",
                "background": "#f0fffd",
                "surface": "#ffffff",
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c"
            }
        }
        
    def get_theme(self, theme_name):
        """获取主题配置"""
        return self.themes.get(theme_name, self.themes["默认浅色"])
    
    def apply_theme(self, app, theme_name):
        """应用主题到应用程序"""
        theme = self.get_theme(theme_name)
        
        # 设置应用程序样式表
        stylesheet = f"""
        QMainWindow, QDialog {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}
        
        QWidget {{
            background-color: {theme['background']};
            color: {theme['text']};
            font-family: "Microsoft YaHei", "Segoe UI";
        }}
        
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {theme['secondary']};
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
            background-color: {theme['surface']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {theme['primary']};
        }}
        
        QPushButton {{
            background-color: {theme['primary']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {theme['secondary']};
        }}
        
        QPushButton:pressed {{
            background-color: {theme['accent']};
        }}
        
        QPushButton:disabled {{
            background-color: #bdc3c7;
            color: #7f8c8d;
        }}
        
        QTreeWidget, QListWidget, QTextEdit, QLineEdit, QComboBox {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 4px;
        }}
        
        QTreeWidget::item:selected, QListWidget::item:selected {{
            background-color: {theme['accent']};
            color: white;
        }}
        
        QTreeWidget::item:hover, QListWidget::item:hover {{
            background-color: {theme['secondary']}20;
        }}
        
        QHeaderView::section {{
            background-color: {theme['primary']};
            color: white;
            padding: 6px;
            border: none;
            font-weight: bold;
        }}
        
        QProgressBar {{
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            text-align: center;
            background-color: {theme['surface']};
        }}
        
        QProgressBar::chunk {{
            background-color: {theme['success']};
            border-radius: 3px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid #bdc3c7;
            background-color: {theme['surface']};
        }}
        
        QTabBar::tab {{
            background-color: {theme['secondary']};
            color: white;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme['primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {theme['accent']};
        }}
        
        QCheckBox, QRadioButton {{
            color: {theme['text']};
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {theme['success']};
            border: 1px solid {theme['success']};
        }}
        
        QMenu {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid #bdc3c7;
        }}
        
        QMenu::item:selected {{
            background-color: {theme['accent']};
            color: white;
        }}
        
        QToolBar {{
            background-color: {theme['primary']};
            border: none;
            spacing: 5px;
        }}
        
        QToolButton {{
            background-color: transparent;
            color: white;
            border: none;
            padding: 6px;
            border-radius: 4px;
        }}
        
        QToolButton:hover {{
            background-color: {theme['secondary']};
        }}
        
        QStatusBar {{
            background-color: {theme['primary']};
            color: white;
        }}
        """
        
        app.setStyleSheet(stylesheet)
        
        # 设置调色板
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(theme['background']))
        palette.setColor(QPalette.WindowText, QColor(theme['text']))
        palette.setColor(QPalette.Base, QColor(theme['surface']))
        palette.setColor(QPalette.AlternateBase, QColor(theme['background']))
        palette.setColor(QPalette.ToolTipBase, QColor(theme['surface']))
        palette.setColor(QPalette.ToolTipText, QColor(theme['text']))
        palette.setColor(QPalette.Text, QColor(theme['text']))
        palette.setColor(QPalette.Button, QColor(theme['primary']))
        palette.setColor(QPalette.ButtonText, QColor("white"))
        palette.setColor(QPalette.BrightText, QColor("red"))
        palette.setColor(QPalette.Link, QColor(theme['accent']))
        palette.setColor(QPalette.Highlight, QColor(theme['accent']))
        palette.setColor(QPalette.HighlightedText, QColor("white"))
        
        app.setPalette(palette)

class TextProcessor:
    """增强的文本处理工具类，支持多语言和特殊符号"""
    
    @staticmethod
    def normalize_text(text):
        """标准化文本，处理特殊符号和多语言字符"""
        if not isinstance(text, str):
            return ""
        
        # Unicode标准化（NFKC形式，兼容性分解并组合）
        normalized = unicodedata.normalize('NFKC', text)
        
        # 保留广泛的字符集：字母、数字、空格、常见标点符号、中日韩文字等
        # 使用更宽泛的正则表达式，保留Unicode字符
        pattern = r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u3130-\u318f\u1100-\u11ff\u3200-\u32ff\u3300-\u33ff\uff00-\uffef\u3000-\u303f\u2000-\u206f\u2010-\u201f\u0021-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]'
        
        cleaned = re.sub(pattern, '', normalized, flags=re.UNICODE)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    @staticmethod
    def clean_for_matching(text):
        """用于匹配的文本清理，保留更多字符"""
        if not isinstance(text, str):
            return ""
        
        # 保留字母、数字、空格、常见标点符号以及Unicode字符（包括中日韩）
        pattern = r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u3130-\u318f\u1100-\u11ff\u3200-\u32ff\u3300-\u33ff\uff00-\uffef\u3000-\u303f\u2000-\u206f\u2010-\u201f\u0021-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e\-\.\(\)\（\）\【\】\『\』\《\》\「\」\｛\｝\〈\〉]'
        
        cleaned = re.sub(pattern, '', text, flags=re.UNICODE)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().lower()
    
    @staticmethod
    def remove_punctuation(text):
        """移除标点符号，用于精确匹配"""
        if not isinstance(text, str):
            return ""
        
        # 移除所有标点符号，保留字母、数字、空格和Unicode字符
        pattern = r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u3130-\u318f\u1100-\u11ff\u3200-\u32ff\u3300-\u33ff\uff00-\uffef]'
        
        cleaned = re.sub(pattern, '', text, flags=re.UNICODE)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().lower()
    
    @staticmethod
    def enhanced_similarity(s1, s2):
        """增强的相似度计算，支持多语言"""
        if not s1 or not s2:
            return 0.0
            
        if s1 == s2:
            return 1.0
            
        # 使用SequenceMatcher计算相似度
        return SequenceMatcher(None, s1, s2).ratio()
    
    @staticmethod
    def multi_language_clean(text):
        """多语言文本清理"""
        if not text:
            return ""
            
        # 保留多语言字符
        text = str(text)
        # 保留中文、日文、韩文、英文、数字、空格和基本标点
        pattern = r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u3130-\u318f\u1100-\u11ff\u3200-\u32ff\u3300-\u33ff\uff00-\uffef\u3000-\u303f\u2000-\u206f\u0021-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e\-\.\(\)]'
        cleaned = re.sub(pattern, '', text, flags=re.UNICODE)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().lower()

class WorkerThread(QThread):
    """工作线程基类"""
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._is_running = True
    
    def stop(self):
        self._is_running = False

class ScanFilesThread(WorkerThread):
    """扫描文件线程"""
    def __init__(self, folders, file_extensions, file_type):
        super().__init__()
        self.folders = folders
        self.file_extensions = file_extensions
        self.file_type = file_type
    
    def run(self):
        try:
            files = []
            total_folders = len(self.folders)
            
            for folder_index, folder in enumerate(self.folders):
                if not self._is_running:
                    break
                    
                if not os.path.exists(folder):
                    continue
                
                self.progress_updated.emit(folder_index + 1, total_folders, f"扫描文件夹: {os.path.basename(folder)}")
                
                for root, dirs, walk_files in os.walk(folder):
                    if not self._is_running:
                        break
                        
                    for file in walk_files:
                        if Path(file).suffix.lower() in self.file_extensions:
                            full_path = os.path.join(root, file)
                            files.append({
                                'path': full_path,
                                'filename': file,
                                'name_only': Path(file).stem,
                                'relative_path': os.path.relpath(full_path, folder),
                                'source_folder': folder
                            })
            
            self.progress_updated.emit(total_folders, total_folders, f"扫描完成，找到 {len(files)} 个{self.file_type}文件")
            self.files_result = files
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"扫描{self.file_type}文件失败: {str(e)}")

class MatchSongsThread(WorkerThread):
    """匹配歌曲线程 - 支持多语言"""
    def __init__(self, df, song_files, match_threshold, text_processor):
        super().__init__()
        self.df = df
        self.song_files = song_files
        self.match_threshold = match_threshold
        self.text_processor = text_processor
    
    def run(self):
        try:
            match_results = {}
            match_scores = {}
            total_records = len(self.df)
            
            for i, (index, row) in enumerate(self.df.iterrows()):
                if not self._is_running:
                    break
                
                if i % 10 == 0:  # 每10条更新一次进度
                    self.progress_updated.emit(i + 1, total_records, f"匹配歌曲: {i + 1}/{total_records}")
                
                title = str(row.get('标题', ''))
                matched_file = self.find_matched_file_with_threshold(title)
                
                if matched_file:
                    match_results[index] = matched_file
                    clean_title = self.text_processor.multi_language_clean(title)
                    filename = Path(matched_file).stem
                    clean_filename = self.text_processor.multi_language_clean(filename)
                    match_scores[index] = self.text_processor.enhanced_similarity(clean_title, clean_filename)
            
            self.progress_updated.emit(total_records, total_records, f"匹配完成: {len(match_results)}/{total_records}")
            self.match_results = match_results
            self.match_scores = match_scores
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"匹配歌曲失败: {str(e)}")
    
    def find_matched_file_with_threshold(self, title):
        """根据标题和阈值查找匹配的歌曲文件"""
        if not self.song_files:
            return None
            
        clean_title = self.text_processor.multi_language_clean(title)
        best_match = None
        best_score = 0
        
        for song in self.song_files:
            if not self._is_running:
                break
                
            original_filename = song['name_only']
            clean_filename = self.text_processor.multi_language_clean(original_filename)
            
            if not clean_title or not clean_filename:
                continue
                
            # 多种匹配策略
            if title == original_filename:
                return song['path']
            
            if clean_title == clean_filename:
                return song['path']
            
            if clean_title in clean_filename or clean_filename in clean_title:
                return song['path']
            
            similarity = self.text_processor.enhanced_similarity(clean_title, clean_filename)
            if similarity > self.match_threshold:
                return song['path']
            
            if self.word_based_match(clean_title, clean_filename):
                return song['path']
                
            if similarity > best_score:
                best_score = similarity
                best_match = song['path']
        
        if best_match and best_score > 0.3:
            return best_match
        else:
            return None

    def word_based_match(self, s1, s2):
        """基于单词的匹配"""
        if len(s1) < 3 or len(s2) < 3:
            return False
        
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        def extract_key_words(s):
            words = re.findall(r'[a-zA-Z\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]{2,}', s)
            return [word for word in words if word.lower() not in common_words]
        
        words1 = extract_key_words(s1)
        words2 = extract_key_words(s2)
        
        if words1 and words2:
            set1 = set(words1)
            set2 = set(words2)
            
            if set1 & set2:
                return True
            
            for w1 in words1:
                for w2 in words2:
                    if self.text_processor.enhanced_similarity(w1, w2) > 0.8:
                        return True
        
        return False

class SaveDataThread(WorkerThread):
    """保存数据线程 - 修复版本"""
    def __init__(self, match_results, df, mapping_rules, output_folder, song_files, 
                 lyrics_files, image_files, lyrics_var, images_var, backup_var, text_processor):
        super().__init__()
        self.match_results = match_results
        self.df = df
        self.mapping_rules = mapping_rules
        self.output_folder = output_folder
        self.song_files = song_files
        self.lyrics_files = lyrics_files
        self.image_files = image_files
        self.lyrics_var = lyrics_var
        self.images_var = images_var
        self.backup_var = backup_var
        self.text_processor = text_processor
        
        # 保存结果统计
        self.success_count = 0
        self.fail_count = 0
        self.failed_songs = []
    
    def run(self):
        try:
            total_items = len(self.match_results)
            
            for i, (index, file_path) in enumerate(self.match_results.items()):
                if not self._is_running:
                    break
                
                if i % 5 == 0:  # 每5条更新一次进度
                    self.progress_updated.emit(i + 1, total_items, f"处理歌曲: {i + 1}/{total_items}")
                
                try:
                    # 跳过备份文件
                    if file_path.endswith('.backup'):
                        logging.info(f"跳过备份文件: {file_path}")
                        continue
                        
                    # 跳过系统文件
                    if os.path.basename(file_path).lower() == 'desktop.ini':
                        logging.info(f"跳过系统文件: {file_path}")
                        continue
                    
                    row = self.df.iloc[index]
                    
                    # 验证源文件是否存在且可访问
                    if not self.validate_source_file(file_path):
                        raise Exception(f"源文件无法访问: {file_path}")
                    
                    metadata = {}
                    for excel_field, value in row.items():
                        if pd.notna(value) and excel_field in self.mapping_rules:
                            target_field = self.mapping_rules[excel_field]
                            metadata[target_field] = str(value)
                    
                    # 查找歌词文件
                    if self.lyrics_var and self.lyrics_files:
                        title = str(row.get('标题', ''))
                        lyrics_file = self.find_lyrics_file(title)
                        if lyrics_file:
                            try:
                                with open(lyrics_file, 'r', encoding='utf-8') as f:
                                    lyrics_content = f.read()
                                    metadata['歌词'] = lyrics_content
                            except Exception as e:
                                logging.warning(f"读取歌词文件失败: {lyrics_file}, 错误: {str(e)}")
                    
                    # 查找图片文件
                    images = []
                    if self.images_var and self.image_files:
                        title = str(row.get('标题', ''))
                        images = self.find_image_files(title, row)
                    
                    # 确定输出路径
                    if self.output_folder:
                        output_path = self.get_output_path(file_path)
                        
                        if not output_path:
                            raise Exception(f"无法确定输出路径: {file_path}")
                        
                        # 创建输出目录
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        
                        if self.backup_var:
                            # 创建备份
                            backup_path = output_path + ".backup"
                            if not os.path.exists(backup_path):
                                self.safe_copy_file(file_path, backup_path)
                        
                        # 复制文件到输出路径
                        self.safe_copy_file(file_path, output_path)
                        
                        # 写入元数据
                        self.write_metadata(output_path, metadata, images)
                    
                    self.success_count += 1
                    
                except Exception as e:
                    self.fail_count += 1
                    row = self.df.iloc[index]
                    song_title = row.get('标题', f"第{index+1}首")
                    self.failed_songs.append(f"{song_title} - {str(e)}")
                    logging.error(f"处理歌曲失败: {file_path}, 错误: {str(e)}")
            
            self.progress_updated.emit(total_items, total_items, f"处理完成: 成功{self.success_count}, 失败{self.fail_count}")
            self.results = {
                'success_count': self.success_count,
                'fail_count': self.fail_count,
                'failed_songs': self.failed_songs
            }
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"保存数据失败: {str(e)}")
    
    def validate_source_file(self, file_path):
        """验证源文件是否可访问"""
        try:
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return False
            
            if not os.path.isfile(file_path):
                logging.error(f"不是文件: {file_path}")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logging.error(f"文件为空: {file_path}")
                return False
            
            # 尝试读取文件头
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if len(header) < 8:
                    logging.error(f"文件过小: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"验证文件失败 {file_path}: {str(e)}")
            return False
    
    def get_output_path(self, file_path):
        """获取输出路径"""
        try:
            # 在song_files中查找匹配的文件
            for song in self.song_files:
                if song['path'] == file_path:
                    source_folder_name = os.path.basename(song['source_folder'])
                    relative_path = song.get('relative_path', os.path.basename(file_path))
                    
                    # 清理路径中的非法字符
                    source_folder_name = self.sanitize_filename(source_folder_name)
                    relative_path = self.sanitize_filepath(relative_path)
                    
                    output_path = os.path.join(self.output_folder, source_folder_name, relative_path)
                    return output_path
            
            # 如果没有找到匹配，使用默认路径
            filename = os.path.basename(file_path)
            filename = self.sanitize_filename(filename)
            output_path = os.path.join(self.output_folder, "未分类", filename)
            return output_path
            
        except Exception as e:
            logging.error(f"获取输出路径失败 {file_path}: {str(e)}")
            return None
    
    def safe_copy_file(self, src, dst):
        """安全的文件复制方法"""
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            # 如果目标文件已存在，先删除
            if os.path.exists(dst):
                os.remove(dst)
            
            # 复制文件
            shutil.copy2(src, dst)
            
            # 验证复制是否成功
            if not os.path.exists(dst):
                raise Exception("复制后目标文件不存在")
            
            src_size = os.path.getsize(src)
            dst_size = os.path.getsize(dst)
            
            if src_size != dst_size:
                raise Exception(f"文件大小不匹配: 源文件 {src_size} bytes, 目标文件 {dst_size} bytes")
            
            logging.info(f"成功复制文件: {src} -> {dst}")
            
        except Exception as e:
            raise Exception(f"文件复制失败: {str(e)}")
    
    def sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        # Windows 文件名非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 移除首尾空格和点
        filename = filename.strip(' .')
        
        # 确保文件名不为空
        if not filename:
            filename = "未命名文件"
        
        return filename
    
    def sanitize_filepath(self, filepath):
        """清理文件路径"""
        # 分割路径和文件名
        dirname = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        
        # 清理文件名
        clean_filename = self.sanitize_filename(filename)
        
        # 清理目录名
        if dirname:
            clean_dirname = self.sanitize_filename(dirname)
            return os.path.join(clean_dirname, clean_filename)
        else:
            return clean_filename
    
    def find_lyrics_file(self, title):
        """查找歌词文件"""
        if not self.lyrics_files:
            return None
            
        clean_title = self.text_processor.multi_language_clean(title)
        
        for lyrics in self.lyrics_files:
            clean_filename = self.text_processor.multi_language_clean(lyrics['name_only'])
            
            if clean_title == clean_filename:
                return lyrics['path']
            elif clean_title in clean_filename or clean_filename in clean_title:
                return lyrics['path']
            elif self.text_processor.enhanced_similarity(clean_title, clean_filename) > 0.7:
                return lyrics['path']
                
        return None
    
    def find_image_files(self, title, row=None):
        """查找图片文件"""
        images = []
        
        if row is not None:
            image_fields = ['封面', '图片', '封面图片', '封面路径', '图片路径']
            for field in image_fields:
                if field in row and pd.notna(row[field]):
                    image_path = str(row[field])
                    image_paths = [path.strip() for path in image_path.split(';')]
                    for path in image_paths:
                        if os.path.exists(path):
                            images.append(path)
                        else:
                            # 检查图片文件夹
                            for image_folder in [img['source_folder'] for img in self.image_files]:
                                filename_only = os.path.basename(path)
                                full_path = os.path.join(image_folder, filename_only)
                                if os.path.exists(full_path):
                                    images.append(full_path)
                                    break
        
        if not images and self.image_files:
            clean_title = self.text_processor.multi_language_clean(title)
            
            for image in self.image_files:
                clean_filename = self.text_processor.multi_language_clean(image['name_only'])
                
                if clean_title == clean_filename:
                    images.append(image['path'])
                elif clean_title in clean_filename or clean_filename in clean_title:
                    images.append(image['path'])
                elif self.text_processor.enhanced_similarity(clean_title, clean_filename) > 0.7:
                    images.append(image['path'])
        
        return list(set(images))
    
    def write_metadata(self, file_path, metadata, images=None):
        """增强的元数据写入方法，支持格式自动检测"""
        # 首先验证文件是否存在和可访问
        if not os.path.exists(file_path):
            raise Exception(f"文件不存在: {file_path}")
        
        if os.path.getsize(file_path) == 0:
            raise Exception(f"文件为空: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        try:
            # 首先尝试根据扩展名处理
            if file_ext == '.mp3':
                self.write_mp3_metadata(file_path, metadata, images)
            elif file_ext == '.flac':
                self.write_flac_metadata(file_path, metadata, images)
            elif file_ext in ['.m4a', '.mp4']:
                self.write_mp4_metadata(file_path, metadata, images)
            elif file_ext == '.wav':
                self.write_wav_metadata(file_path, metadata, images)
            elif file_ext in ['.aac', '.wma']:
                self.write_aac_metadata(file_path, metadata, images)
            else:
                # 对于未知扩展名，尝试自动检测
                self.write_generic_metadata(file_path, metadata, images)
                
        except Exception as e:
            # 如果标准方法失败，尝试格式自动检测和恢复
            logging.warning(f"标准方法失败，尝试格式恢复: {str(e)}")
            try:
                self.try_format_recovery(file_path, metadata, images)
            except Exception as recovery_error:
                # 记录详细的错误信息用于调试
                file_info = f"路径: {file_path}, 大小: {os.path.getsize(file_path)}, 扩展名: {file_ext}"
                logging.error(f"元数据写入失败 - {file_info}, 错误: {str(recovery_error)}")
                raise Exception(f"写入元数据失败: {str(recovery_error)}")
    
    def try_format_recovery(self, file_path, metadata, images=None):
        """尝试格式恢复"""
        try:
            # 读取文件头信息进行格式检测
            with open(file_path, 'rb') as f:
                header = f.read(12)  # 读取文件头
            
            # 简单的文件格式检测
            if header.startswith(b'ID3'):
                logging.info("检测到MP3文件头，尝试MP3格式")
                self.write_mp3_metadata(file_path, metadata, images)
            elif header.startswith(b'fLaC'):
                logging.info("检测到FLAC文件头，尝试FLAC格式")
                self.write_flac_metadata(file_path, metadata, images)
            elif header.startswith(b'ftyp'):
                logging.info("检测到MP4文件头，尝试MP4格式")
                self.write_mp4_metadata(file_path, metadata, images)
            elif header.startswith(b'RIFF'):
                logging.info("检测到WAV文件头，尝试WAV格式")
                self.write_wav_metadata(file_path, metadata, images)
            else:
                # 最后尝试通用方法
                logging.info("无法识别文件头，使用通用方法")
                self.write_generic_metadata(file_path, metadata, images)
                
        except Exception as e:
            raise Exception(f"格式恢复失败: {str(e)}")
    
    def write_mp3_metadata(self, file_path, metadata, images=None):
        """写入MP3文件的ID3标签"""
        try:
            # 首先尝试使用EasyID3
            try:
                audio = EasyID3(file_path)
            except:
                audio = EasyID3()
            
            # MP3字段映射
            mp3_mapping = {
                '标题': 'title',
                '艺术家': 'artist', 
                '专辑': 'album',
                '年份': 'date',
                '流派': 'genre',
                '作曲家': 'composer',
                '作词': 'lyricist',
                '编曲': 'arranger',
                '唱片公司': 'organization',
                '版权': 'copyright',
                '编码': 'encodedby',
                '语言': 'language',
                'BPM': 'bpm',
                'ISRC': 'isrc',
                '唱片集艺术家': 'albumartist',
                '光盘编号': 'discnumber',
                '音轨编号': 'tracknumber',
                '评论': 'comment',
            }
            
            for field, value in metadata.items():
                if field in mp3_mapping:
                    try:
                        audio[mp3_mapping[field]] = str(value)
                    except Exception as e:
                        logging.warning(f"设置MP3字段失败: {field}={value}, 错误: {str(e)}")
            
            audio.save()
            
            # 处理歌词 - 使用ID3标签
            if '歌词' in metadata:
                self.write_mp3_lyrics(file_path, metadata['歌词'])
                
            # 处理图片
            if images:
                self.write_mp3_images(file_path, images)
                
        except Exception as e:
            logging.warning(f"使用EasyID3失败，尝试使用ID3: {str(e)}")
            self.write_mp3_id3(file_path, metadata, images)
    
    def write_mp3_id3(self, file_path, metadata, images=None):
        """使用原始ID3标签写入MP3元数据"""
        try:
            try:
                audio = MP3(file_path, ID3=ID3)
            except:
                audio = MP3(file_path)
                
            if audio.tags is None:
                audio.add_tags()
                
            tags = audio.tags
            
            # ID3字段映射
            id3_mapping = {
                '标题': TIT2,
                '艺术家': TPE1,
                '专辑': TALB,
                '年份': TYER,
                '作曲家': TCOM,
                '流派': TCON,
                '评论': lambda x: COMM(encoding=3, lang='eng', desc='', text=x),
                '歌词': lambda x: USLT(encoding=3, lang='eng', desc='', text=x),
                '唱片公司': TPE2,
                '版权': TCOP,
                '语言': TLAN
            }
            
            for field, value in metadata.items():
                if field in id3_mapping:
                    try:
                        if field == '歌词':
                            # 特殊处理歌词
                            tags.delall('USLT')
                            tags.add(USLT(encoding=3, lang='eng', desc='', text=str(value)))
                        elif field in ['评论']:
                            tags.delall('COMM')
                            tags.add(id3_mapping[field](str(value)))
                        else:
                            tags.delall(id3_mapping[field].__name__)
                            tags.add(id3_mapping[field](encoding=3, text=str(value)))
                    except Exception as e:
                        logging.warning(f"设置ID3字段失败: {field}={value}, 错误: {str(e)}")
            
            # 处理图片
            if images:
                self.write_mp3_images(file_path, images, tags)
                
            audio.save()
            
        except Exception as e:
            logging.error(f"ID3写入也失败: {str(e)}")
            raise Exception(f"MP3元数据写入失败: {str(e)}")
    
    def write_mp3_lyrics(self, file_path, lyrics_text):
        """专门写入MP3歌词"""
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
                
            # 清除现有的歌词帧
            audio.tags.delall('USLT')
            
            # 添加新的歌词帧
            uslt_frame = USLT(encoding=3, lang='eng', desc='', text=lyrics_text)
            audio.tags.add(uslt_frame)
            
            audio.save()
        except Exception as e:
            logging.warning(f"写入MP3歌词失败: {str(e)}")
    
    def write_flac_metadata(self, file_path, metadata, images=None):
        """写入FLAC文件的元数据"""
        try:
            audio = FLAC(file_path)
        except Exception as e:
            raise Exception(f"无法打开FLAC文件: {str(e)}")
        
        try:
            # FLAC使用VORBIS_COMMENT，字段名不区分大小写，但通常使用大写
            field_mapping = {
                '标题': 'TITLE',
                '艺术家': 'ARTIST',
                '专辑': 'ALBUM', 
                '年份': 'DATE',
                '歌词': 'LYRICS',
                '作词': 'LYRICIST',
                '作曲': 'COMPOSER',
                '出品': 'ORGANIZATION',
                '版权': 'COPYRIGHT',
                '语种': 'LANGUAGE',
                '所属专辑': 'ALBUM',
                '流派': 'GENRE',
                '编曲': 'ARRANGER',
                '唱片公司': 'LABEL',
                '编码': 'ENCODEDBY',
                'BPM': 'BPM',
                'ISRC': 'ISRC',
                '唱片集艺术家': 'ALBUMARTIST',
                '光盘编号': 'DISCNUMBER',
                '音轨编号': 'TRACKNUMBER',
                '评论': 'COMMENT',
                '注释': 'COMMENT'
            }
            
            for field, value in metadata.items():
                try:
                    # 映射字段名
                    mapped_field = field_mapping.get(field, field.upper())
                    # FLAC支持重复字段，所以直接添加
                    audio[mapped_field] = str(value)
                except Exception as e:
                    logging.warning(f"设置FLAC字段失败: {field}={value}, 错误: {str(e)}")
            
            # 处理图片
            if images:
                self.write_flac_images(file_path, images, audio)
            
            audio.save()
            
        except Exception as e:
            raise Exception(f"保存FLAC元数据失败: {str(e)}")
    
    def write_mp4_metadata(self, file_path, metadata, images=None):
        """写入MP4/M4A文件的元数据"""
        try:
            audio = MP4(file_path)
        except Exception as e:
            raise Exception(f"无法打开MP4文件: {str(e)}")
        
        # MP4字段映射
        mp4_mapping = {
            '标题': '\xa9nam',
            '艺术家': '\xa9ART',
            '专辑': '\xa9alb',
            '年份': '\xa9day',
            '作曲家': '\xa9wrt',
            '歌词': '\xa9lyr',
            '评论': '\xa9cmt',
            '流派': '\xa9gen',
            '版权': 'cprt',
            '编码': '\xa9too',
            '唱片公司': '----:com.apple.iTunes:LABEL',
            'ISRC': '----:com.apple.iTunes:ISRC',
            'BPM': '----:com.apple.iTunes:BPM',
            '唱片集艺术家': 'aART',
            '光盘编号': 'disk',
            '音轨编号': 'trkn'
        }
        
        for field, value in metadata.items():
            if field in mp4_mapping:
                try:
                    audio[mp4_mapping[field]] = [str(value)]
                except Exception as e:
                    logging.warning(f"设置MP4字段失败: {field}={value}, 错误: {str(e)}")
        
        try:
            audio.save()
        except Exception as e:
            raise Exception(f"保存MP4元数据失败: {str(e)}")
    
    def write_wav_metadata(self, file_path, metadata, images=None):
        """写入WAV文件的元数据"""
        try:
            audio = WAVE(file_path)
        except Exception as e:
            raise Exception(f"无法打开WAV文件: {str(e)}")
        
        if audio.tags is None:
            audio.add_tags()
            
        tags = audio.tags
        
        # WAV使用ID3标签
        id3_mapping = {
            '标题': TIT2,
            '艺术家': TPE1,
            '专辑': TALB,
            '年份': TYER,
            '作曲家': TCOM,
            '流派': TCON,
            '评论': COMM,
            '歌词': USLT,
            '唱片公司': TPE2,
            '版权': TCOP,
            '语言': TLAN
        }
        
        for field, value in metadata.items():
            if field in id3_mapping:
                try:
                    tags.add(id3_mapping[field](encoding=3, text=str(value)))
                except Exception as e:
                    logging.warning(f"设置WAV字段失败: {field}={value}, 错误: {str(e)}")
        
        try:
            audio.save()
        except Exception as e:
            raise Exception(f"保存WAV元数据失败: {str(e)}")
    
    def write_aac_metadata(self, file_path, metadata, images=None):
        """写入AAC/WMA文件的元数据 - 增强版本"""
        try:
            # 首先尝试使用ASF打开
            try:
                audio = ASF(file_path)
                
                # ASF字段映射
                asf_mapping = {
                    '标题': 'Title',
                    '艺术家': 'Author', 
                    '专辑': 'Album',
                    '年份': 'Year',
                    '歌词': 'Lyrics',
                    '评论': 'Comment',
                    '流派': 'Genre',
                    '版权': 'Copyright',
                    '编码': 'EncodedBy'
                }
                
                for field, value in metadata.items():
                    if field in asf_mapping:
                        try:
                            audio[asf_mapping[field]] = [str(value)]
                        except Exception as e:
                            logging.warning(f"设置AAC/WMA字段失败: {field}={value}, 错误: {str(e)}")
                
                audio.save()
                return
                
            except Exception as asf_error:
                # 如果不是ASF文件，尝试其他格式
                logging.warning(f"文件不是ASF格式，尝试其他格式: {str(asf_error)}")
                
                # 尝试使用通用文件检测
                audio = File(file_path)
                if audio is None:
                    raise Exception("无法识别的音频格式")
                    
                # 根据实际检测到的类型进行处理
                file_type = type(audio).__name__.lower()
                logging.info(f"检测到文件实际格式: {file_type}")
                
                if 'mp3' in file_type:
                    self.write_mp3_metadata(file_path, metadata, images)
                elif 'flac' in file_type:
                    self.write_flac_metadata(file_path, metadata, images)
                elif 'mp4' in file_type:
                    self.write_mp4_metadata(file_path, metadata, images)
                elif 'id3' in file_type:
                    self.write_mp3_metadata(file_path, metadata, images)
                else:
                    # 最后尝试通用方法
                    self.write_generic_metadata(file_path, metadata, images)
                    
        except Exception as e:
            # 如果所有方法都失败，记录详细信息
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            logging.error(f"处理文件失败: {file_path}, 大小: {file_size} bytes, 错误: {str(e)}")
            raise Exception(f"无法处理AAC/WMA文件: {str(e)}")
    
    def write_generic_metadata(self, file_path, metadata, images=None):
        """通用元数据写入方法"""
        try:
            audio = File(file_path)
            if audio is None:
                raise Exception("无法识别的音频格式")
                
            # 尝试直接设置字段
            for field, value in metadata.items():
                try:
                    # 尝试常见的字段名映射
                    if field == '标题':
                        audio['title'] = str(value)
                    elif field == '艺术家':
                        audio['artist'] = str(value)
                    elif field == '专辑':
                        audio['album'] = str(value)
                    elif field == '年份':
                        audio['date'] = str(value)
                    elif field == '歌词':
                        audio['lyrics'] = str(value)
                    else:
                        audio[field] = str(value)
                except:
                    # 如果直接设置失败，尝试其他方法
                    try:
                        if hasattr(audio, 'tags'):
                            audio.tags[field] = str(value)
                    except:
                        logging.warning(f"无法设置字段 {field}")
            
            audio.save()
        except Exception as e:
            raise Exception(f"通用元数据写入失败: {str(e)}")

    def write_mp3_images(self, file_path, images, tags=None):
        """写入MP3图片"""
        try:
            if not images:
                return
                
            if tags is None:
                audio = MP3(file_path, ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
                tags = audio.tags
            
            # 只使用第一张图片
            image_path = images[0]
            if os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    image_data = img_file.read()
                
                # 删除现有的图片帧
                tags.delall('APIC')
                
                # 确定MIME类型
                if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                    mime_type = 'image/jpeg'
                elif image_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                else:
                    mime_type = 'image/jpeg'  # 默认
                
                # 添加新的图片帧
                apic_frame = APIC(
                    encoding=3,
                    mime=mime_type,
                    type=3,  # 封面图片
                    desc='Cover',
                    data=image_data
                )
                tags.add(apic_frame)
                
                if tags is not audio.tags:  # 如果不是外部传入的tags，需要保存
                    audio.save()
        except Exception as e:
            logging.warning(f"写入MP3图片失败: {str(e)}")

    def write_flac_images(self, file_path, images, audio=None):
        """写入FLAC图片"""
        try:
            if not images:
                return
                
            if audio is None:
                audio = FLAC(file_path)
            
            # 只使用第一张图片
            image_path = images[0]
            if os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    image_data = img_file.read()
                
                # 删除现有的图片
                audio.clear_pictures()
                
                # 添加新图片
                from mutagen.flac import Picture
                picture = Picture()
                picture.type = 3  # 封面图片
                if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                    picture.mime = 'image/jpeg'
                elif image_path.lower().endswith('.png'):
                    picture.mime = 'image/png'
                else:
                    picture.mime = 'image/jpeg'  # 默认
                picture.desc = 'Cover'
                picture.data = image_data
                
                audio.add_picture(picture)
        except Exception as e:
            logging.warning(f"写入FLAC图片失败: {str(e)}")

class ProgressDialog(QDialog):
    """非阻塞进度显示对话框"""
    def __init__(self, parent=None, title="处理中", can_cancel=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(False)
        self.setFixedSize(400, 120)
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel("正在处理，请稍候...")
        layout.addWidget(self.label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
        
        self.detail_label = QLabel("")
        layout.addWidget(self.detail_label)
        
        if can_cancel:
            self.cancel_button = QPushButton("取消")
            self.cancel_button.clicked.connect(self.reject)
            layout.addWidget(self.cancel_button)
        
        self.center_on_parent()
    
    def center_on_parent(self):
        """在父窗口中心显示"""
        if self.parent():
            parent_rect = self.parent().frameGeometry()
            self.move(parent_rect.center() - self.rect().center())
    
    def update_progress(self, current, total, message=""):
        """更新进度信息"""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        else:
            self.progress_bar.setRange(0, 0)
        
        if message:
            self.detail_label.setText(message)
        
        QApplication.processEvents()

class MultiFolderManager(QWidget):
    """多文件夹管理器"""
    folderUpdated = pyqtSignal()
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.folders = []
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QPushButton(f"管理{self.title}")
        self.button.clicked.connect(self.show_manager)
        layout.addWidget(self.button)
        
        self.status_label = QLabel("未选择")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def show_manager(self):
        """显示文件夹管理器窗口"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"管理{self.title}")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"{self.title}文件夹列表:"))
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        self.update_list_widget()
        
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加文件夹")
        add_btn.clicked.connect(lambda: self.add_folder(dialog))
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("移除选中")
        remove_btn.clicked.connect(lambda: self.remove_selected(dialog))
        button_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("清空所有")
        clear_btn.clicked.connect(lambda: self.clear_all(dialog))
        button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def add_folder(self, parent_dialog):
        """添加文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            parent_dialog, f"选择{self.title}文件夹"
        )
        
        if folder_path and folder_path not in self.folders:
            self.folders.append(folder_path)
            self.update_list_widget()
            self.update_status()
            self.folderUpdated.emit()
    
    def remove_selected(self, parent_dialog):
        """移除选中的文件夹"""
        current_item = self.list_widget.currentItem()
        if current_item:
            index = self.list_widget.row(current_item)
            self.folders.pop(index)
            self.update_list_widget()
            self.update_status()
            self.folderUpdated.emit()
    
    def clear_all(self, parent_dialog):
        """清空所有文件夹"""
        if self.folders:
            reply = QMessageBox.question(
                parent_dialog, "确认", "确定要清空所有文件夹吗？"
            )
            if reply == QMessageBox.Yes:
                self.folders = []
                self.update_list_widget()
                self.update_status()
                self.folderUpdated.emit()
    
    def update_list_widget(self):
        """更新列表显示"""
        self.list_widget.clear()
        for folder in self.folders:
            self.list_widget.addItem(folder)
    
    def update_status(self):
        """更新状态标签"""
        count = len(self.folders)
        if count == 0:
            self.status_label.setText("未选择")
        else:
            self.status_label.setText(f"已选择 {count} 个")
    
    def get_folders(self):
        """获取所有文件夹路径"""
        return self.folders.copy()

class ManualMatchDialog(QDialog):
    """人工匹配对话框"""
    def __init__(self, title, song_files, text_processor, parent=None):
        super().__init__(parent)
        self.title = title
        self.song_files = song_files
        self.text_processor = text_processor
        self.selected_file = None
        
        self.setWindowTitle(f"人工匹配 - {title}")
        self.resize(800, 600)
        
        self.init_ui()
        self.populate_song_list()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题信息
        info_label = QLabel(f"为歌曲《{self.title}》选择匹配的音频文件：")
        layout.addWidget(info_label)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_songs)
        search_layout.addWidget(self.search_edit)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # 歌曲列表
        self.song_list = QListWidget()
        self.song_list.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.song_list)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        select_btn = QPushButton("选择")
        select_btn.clicked.connect(self.accept_selection)
        button_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def populate_song_list(self):
        """填充歌曲列表"""
        self.song_list.clear()
        
        clean_title = self.text_processor.multi_language_clean(self.title)
        
        # 计算相似度并排序
        songs_with_scores = []
        for song in self.song_files:
            clean_filename = self.text_processor.multi_language_clean(song['name_only'])
            similarity = self.text_processor.enhanced_similarity(clean_title, clean_filename)
            songs_with_scores.append((song, similarity))
        
        # 按相似度降序排序
        songs_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        for song, similarity in songs_with_scores:
            item_text = f"{song['filename']} (相似度: {similarity:.1%}) - {song['path']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, song['path'])
            self.song_list.addItem(item)
    
    def filter_songs(self):
        """过滤歌曲列表"""
        search_term = self.search_edit.text().lower()
        
        for i in range(self.song_list.count()):
            item = self.song_list.item(i)
            item_text = item.text().lower()
            item.setHidden(search_term not in item_text)
    
    def accept_selection(self):
        """接受选择"""
        current_item = self.song_list.currentItem()
        if current_item:
            self.selected_file = current_item.data(Qt.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "警告", "请先选择一个文件")

class LogWindow(QDialog):
    """独立的日志输出窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("处理日志")
        self.resize(800, 500)
        
        self.init_ui()
        self.setup_log_handler()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("清除日志")
        clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("保存日志")
        save_btn.clicked.connect(self.save_log)
        button_layout.addWidget(save_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_log_handler(self):
        """设置日志处理器"""
        self.log_handler = LogHandler(self.text_edit)
        self.log_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(self.log_handler)
    
    def clear_log(self):
        """清除日志"""
        self.text_edit.clear()
    
    def save_log(self):
        """保存日志到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "成功", "日志已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存日志失败: {str(e)}")

class LogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到文本区域"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.append(msg)
            # 自动滚动到底部
            scrollbar = self.text_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        QTimer.singleShot(0, append)

class ManualWindow(QDialog):
    """产品说明书窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("产品说明书 - 歌曲元数据录入软件")
        self.resize(800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        text_edit = QTextEdit()
        text_edit.setFont(QFont("微软雅黑", 10))
        text_edit.setReadOnly(True)
        
        manual_content = """
歌曲元数据录入软件 v3.0 - 产品说明书

一、软件简介
本软件是一款专业的歌曲元数据管理工具，能够批量处理音频文件的元数据信息，
包括歌曲标题、艺术家、专辑、年份、语种等，并支持歌词和封面图片的导入。

二、主要功能
1. 多文件夹管理：支持同时管理多个歌曲文件夹、歌词文件夹和图片文件夹
2. 智能匹配：通过智能算法自动匹配Excel数据与音频文件
3. 字段映射：灵活配置Excel字段与音频元数据字段的映射关系
4. 批量处理：支持批量写入元数据、歌词和封面图片
5. 人工匹配：提供人工匹配功能，确保匹配准确性
6. 多语言支持：支持中文、日文、韩文、英文等多种语言
7. 主题切换：提供多种界面主题选择

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
2. 可以使用"自动匹配字段"快速建立字段映射
3. 对于特殊字段，可以使用"手动匹配字段"进行精确设置

第四步：匹配歌曲
1. 点击"自动匹配歌曲"进行初步匹配
2. 对于未匹配的歌曲，可以使用"人工匹配歌曲"进行精确匹配
3. 对于特殊歌曲，可以双击行或使用右键菜单进行人工匹配
4. 调整匹配阈值以优化匹配效果

第五步：保存结果
1. 在保存设置中选择需要保存的内容（歌词、图片等）
2. 点击"开始保存"按钮处理所有匹配的歌曲
3. 处理完成后查看结果统计和错误日志

四、注意事项
1. 确保Excel文件格式正确，包含必要的歌曲信息
2. 音频文件支持格式：MP3、FLAC、WAV、M4A、AAC、OGG、WMA
3. 歌词文件支持格式：LRC、TXT、LYRIC、LRCX
4. 图片文件支持格式：JPG、JPEG、PNG、GIF、BMP、TIFF
5. 处理前建议备份原始文件

五、常见问题
1. 匹配率低：尝试调整匹配阈值，或使用人工匹配
2. 元数据写入失败：检查文件权限和格式支持
3. 歌词/图片未导入：检查文件命名是否与歌曲标题匹配
4. 程序运行缓慢：减少同时处理的文件夹数量

如有问题，请查看日志文件或联系技术支持。
"""
        text_edit.setText(manual_content)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

class SongMetadataEditorPyQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("歌曲元数据录入软件 v3.0 - 多语言增强版")
        self.resize(1300, 850)
        
        # 初始化数据
        self.df = None
        self.song_folders = []
        self.lyrics_folders = []
        self.image_folders = []
        self.output_folder = None
        self.song_files = []
        self.lyrics_files = []
        self.image_files = []
        self.mapping_rules = {}
        self.match_results = {}
        self.match_scores = {}
        self.match_threshold = 0.6
        self.selected_row_index = None
        
        # 工具类
        self.text_processor = TextProcessor()
        self.theme_manager = ThemeManager()
        
        # 工作线程
        self.current_thread = None
        self.progress_dialog = None
        
        # 设置日志
        self.setup_logging()
        
        # 创建界面
        self.init_ui()
        
        # 窗口引用
        self.log_window = None
        self.manual_window = None
    
    def setup_logging(self):
        """设置日志记录"""
        desktop = Path.home() / "Desktop"
        log_file = desktop / "song_metadata_editor.log"
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().addHandler(file_handler)
        logging.getLogger().propagate = False
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 文件操作标签页
        file_tab = self.create_file_tab()
        tab_widget.addTab(file_tab, "文件操作")
        
        # 匹配设置标签页
        match_tab = self.create_match_tab()
        tab_widget.addTab(match_tab, "匹配设置")
        
        # 数据显示标签页
        data_tab = self.create_data_tab()
        tab_widget.addTab(data_tab, "歌曲数据")
        
        # 应用默认主题
        self.apply_theme("默认浅色")
    
    def create_file_tab(self):
        """创建文件操作标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件选择区域
        file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout(file_group)
        
        # Excel文件选择
        excel_layout = QHBoxLayout()
        excel_btn = QPushButton("选择Excel文件")
        excel_btn.clicked.connect(self.load_excel)
        excel_layout.addWidget(excel_btn)
        
        self.file_label = QLabel("未选择Excel文件")
        excel_layout.addWidget(self.file_label)
        
        # 输出文件夹选择
        output_btn = QPushButton("选择输出文件夹")
        output_btn.clicked.connect(self.load_output_folder)
        excel_layout.addWidget(output_btn)
        
        self.output_label = QLabel("未选择输出文件夹")
        excel_layout.addWidget(self.output_label)
        
        # 验证按钮
        validate_btn = QPushButton("验证文件")
        validate_btn.clicked.connect(self.validate_matched_files)
        excel_layout.addWidget(validate_btn)
        
        # 日志按钮
        log_btn = QPushButton("查看日志")
        log_btn.clicked.connect(self.show_log_window)
        excel_layout.addWidget(log_btn)
        
        # 说明书按钮
        manual_btn = QPushButton("产品说明书")
        manual_btn.clicked.connect(self.show_manual_window)
        excel_layout.addWidget(manual_btn)
        
        # 主题选择
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.themes.keys())
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        theme_layout.addWidget(self.theme_combo)
        
        excel_layout.addLayout(theme_layout)
        excel_layout.addStretch()
        file_layout.addLayout(excel_layout)
        
        # 多文件夹管理器
        folders_layout = QHBoxLayout()
        
        # 歌曲文件夹
        folders_layout.addWidget(QLabel("歌曲文件夹:"))
        self.song_folder_manager = MultiFolderManager("歌曲文件夹")
        self.song_folder_manager.folderUpdated.connect(self.on_song_folders_updated)
        folders_layout.addWidget(self.song_folder_manager)
        
        # 歌词文件夹
        folders_layout.addWidget(QLabel("歌词文件夹:"))
        self.lyrics_folder_manager = MultiFolderManager("歌词文件夹")
        self.lyrics_folder_manager.folderUpdated.connect(self.on_lyrics_folders_updated)
        folders_layout.addWidget(self.lyrics_folder_manager)
        
        # 图片文件夹
        folders_layout.addWidget(QLabel("图片文件夹:"))
        self.image_folder_manager = MultiFolderManager("图片文件夹")
        self.image_folder_manager.folderUpdated.connect(self.on_image_folders_updated)
        folders_layout.addWidget(self.image_folder_manager)
        
        folders_layout.addStretch()
        file_layout.addLayout(folders_layout)
        
        layout.addWidget(file_group)
        
        # 保存设置区域
        save_group = QGroupBox("保存设置")
        save_layout = QHBoxLayout(save_group)
        
        self.lyrics_var = QCheckBox("导入歌词")
        self.lyrics_var.setChecked(True)
        save_layout.addWidget(self.lyrics_var)
        
        self.images_var = QCheckBox("导入图片")
        self.images_var.setChecked(True)
        save_layout.addWidget(self.images_var)
        
        self.backup_var = QCheckBox("备份原文件")
        self.backup_var.setChecked(True)
        save_layout.addWidget(self.backup_var)
        
        save_layout.addStretch()
        layout.addWidget(save_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("开始保存")
        self.save_btn.clicked.connect(self.start_save_process)
        button_layout.addWidget(self.save_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 状态标签
        self.result_label = QLabel("准备就绪")
        layout.addWidget(self.result_label)
        
        layout.addStretch()
        
        return widget

    def create_match_tab(self):
        """创建匹配设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 匹配参数设置
        params_group = QGroupBox("匹配参数设置")
        params_layout = QVBoxLayout(params_group)
        
        # 匹配阈值
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("匹配阈值:"))
        
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1.0)
        self.threshold_spin.setValue(0.6)
        self.threshold_spin.setSingleStep(0.05)
        threshold_layout.addWidget(self.threshold_spin)
        
        threshold_layout.addStretch()
        params_layout.addLayout(threshold_layout)
        
        layout.addWidget(params_group)
        
        # 字段映射区域
        mapping_group = QGroupBox("字段映射规则")
        mapping_layout = QVBoxLayout(mapping_group)
        
        self.map_tree = QTreeWidget()
        self.map_tree.setHeaderLabels(["Excel字段", "目标字段", "匹配方式"])
        self.map_tree.setColumnWidth(0, 200)
        self.map_tree.setColumnWidth(1, 150)
        self.map_tree.setColumnWidth(2, 100)
        mapping_layout.addWidget(self.map_tree)
        
        # 映射操作按钮
        map_btn_layout = QHBoxLayout()
        
        auto_match_btn = QPushButton("自动匹配字段")
        auto_match_btn.clicked.connect(self.auto_match_fields)
        map_btn_layout.addWidget(auto_match_btn)
        
        manual_match_btn = QPushButton("手动匹配字段")
        manual_match_btn.clicked.connect(self.manual_match_fields)
        map_btn_layout.addWidget(manual_match_btn)
        
        map_btn_layout.addStretch()
        mapping_layout.addLayout(map_btn_layout)
        
        layout.addWidget(mapping_group)
        
        # 匹配操作区域
        match_ops_group = QGroupBox("匹配操作")
        match_ops_layout = QHBoxLayout(match_ops_group)
        
        auto_match_songs_btn = QPushButton("自动匹配歌曲")
        auto_match_songs_btn.clicked.connect(self.auto_match_songs)
        match_ops_layout.addWidget(auto_match_songs_btn)
        
        manual_match_songs_btn = QPushButton("人工匹配歌曲")
        manual_match_songs_btn.clicked.connect(self.manual_match_songs)
        match_ops_layout.addWidget(manual_match_songs_btn)
        
        clear_matches_btn = QPushButton("清除所有匹配")
        clear_matches_btn.clicked.connect(self.clear_all_matches)
        match_ops_layout.addWidget(clear_matches_btn)
        
        match_ops_layout.addStretch()
        layout.addWidget(match_ops_group)
        
        layout.addStretch()
        
        return widget

    def create_data_tab(self):
        """创建数据显示标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("匹配统计: 成功 0 首, 失败 0 首, 未匹配 0 首")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入标题、艺术家等进行搜索...")
        self.search_edit.textChanged.connect(self.search_data)
        search_layout.addWidget(self.search_edit)
        
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # 数据表格
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels([
            "选择", "Excel标题", "文件名", "匹配率", "艺术家", "年份", 
            "语种", "所属专辑", "歌词状态", "图片状态", "匹配状态"
        ])
        
        # 设置列宽
        header = self.tree_widget.header()
        for i in range(11):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # 绑定双击事件
        self.tree_widget.itemDoubleClicked.connect(self.on_tree_double_click)
        
        # 绑定右键菜单
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.tree_widget)
        
        return widget

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        # 保存选中的行索引
        excel_title = item.text(1)
        for index, row in self.df.iterrows():
            if str(row.get('标题', '')) == excel_title:
                self.selected_row_index = index
                break
        
        menu = QMenu(self)
        
        manual_match_action = QAction("人工匹配歌曲", self)
        manual_match_action.triggered.connect(self.manual_match_from_context)
        menu.addAction(manual_match_action)
        
        clear_match_action = QAction("清除匹配", self)
        clear_match_action.triggered.connect(self.clear_match_from_context)
        menu.addAction(clear_match_action)
        
        menu.addSeparator()
        
        view_details_action = QAction("查看匹配详情", self)
        view_details_action.triggered.connect(self.view_match_details)
        menu.addAction(view_details_action)
        
        menu.exec_(self.tree_widget.mapToGlobal(position))
    
    def manual_match_from_context(self):
        """从右键菜单人工匹配歌曲"""
        if self.selected_row_index is None:
            QMessageBox.warning(self, "警告", "请先选择一行数据")
            return
            
        row = self.df.iloc[self.selected_row_index]
        title = str(row.get('标题', ''))
        self.show_manual_match_dialog(self.selected_row_index, title)
    
    def clear_match_from_context(self):
        """从右键菜单清除匹配"""
        if self.selected_row_index is None:
            QMessageBox.warning(self, "警告", "请先选择一行数据")
            return
            
        if self.selected_row_index in self.match_results:
            del self.match_results[self.selected_row_index]
            if self.selected_row_index in self.match_scores:
                del self.match_scores[self.selected_row_index]
            
            self.refresh_matches()
            QMessageBox.information(self, "成功", "已清除匹配")
        else:
            QMessageBox.information(self, "提示", "该行没有匹配记录")
    
    def view_match_details(self):
        """查看匹配详情"""
        if self.selected_row_index is None:
            QMessageBox.warning(self, "警告", "请先选择一行数据")
            return
            
        row = self.df.iloc[self.selected_row_index]
        title = str(row.get('标题', ''))
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"匹配详情 - {title}")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        text_edit.append(f"=== 匹配详情 ===\n\n")
        text_edit.append(f"Excel标题: {title}\n")
        
        clean_title = self.text_processor.multi_language_clean(title)
        text_edit.append(f"清理后标题: {clean_title}\n\n")
        
        if self.selected_row_index in self.match_results:
            matched_file = self.match_results[self.selected_row_index]
            text_edit.append(f"✅ 已匹配文件:\n")
            text_edit.append(f"   文件名: {os.path.basename(matched_file)}\n")
            text_edit.append(f"   完整路径: {matched_file}\n")
            
            match_score = self.match_scores.get(self.selected_row_index, 0)
            text_edit.append(f"   匹配率: {match_score:.1%}\n\n")
        else:
            text_edit.append(f"❌ 未匹配\n\n")
        
        text_edit.append(f"=== 所有歌曲文件匹配情况 ===\n\n")
        
        if not self.song_files:
            text_edit.append("没有可用的歌曲文件\n")
        else:
            matches_with_scores = []
            for song in self.song_files:
                clean_filename = self.text_processor.multi_language_clean(song['name_only'])
                score = self.text_processor.enhanced_similarity(clean_title, clean_filename)
                matches_with_scores.append((song, score))
            
            matches_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            for i, (song, score) in enumerate(matches_with_scores[:10]):
                status = "✅ 当前匹配" if (self.selected_row_index in self.match_results and 
                                       self.match_results[self.selected_row_index] == song['path']) else ""
                text_edit.append(f"{i+1}. {song['filename']}\n")
                text_edit.append(f"   匹配率: {score:.1%} {status}\n")
                text_edit.append(f"   路径: {song['path']}\n\n")
        
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def on_tree_double_click(self, item, column):
        """处理树形视图的双击事件"""
        excel_title = item.text(1)
        
        for index, row in self.df.iterrows():
            if str(row.get('标题', '')) == excel_title:
                self.selected_row_index = index
                self.show_manual_match_dialog(index, excel_title)
                break
    
    def show_manual_match_dialog(self, index, title):
        """显示人工匹配对话框"""
        if not self.song_files:
            QMessageBox.warning(self, "警告", "请先选择歌曲文件夹")
            return
            
        dialog = ManualMatchDialog(title, self.song_files, self.text_processor, self)
        if dialog.exec_() == QDialog.Accepted:
            self.match_results[index] = dialog.selected_file
            
            clean_title = self.text_processor.multi_language_clean(title)
            filename = Path(dialog.selected_file).stem
            clean_filename = self.text_processor.multi_language_clean(filename)
            match_score = self.text_processor.enhanced_similarity(clean_title, clean_filename)
            self.match_scores[index] = match_score
            
            self.refresh_matches()
            QMessageBox.information(self, "成功", 
                                  f"已人工匹配: {title} -> {os.path.basename(dialog.selected_file)}")

    def show_log_window(self):
        """显示日志窗口"""
        if self.log_window is None:
            self.log_window = LogWindow(self)
        self.log_window.show()
        self.log_window.raise_()

    def show_manual_window(self):
        """显示产品说明书窗口"""
        if self.manual_window is None:
            self.manual_window = ManualWindow(self)
        self.manual_window.show()
        self.manual_window.raise_()

    def apply_theme(self, theme_name):
        """应用主题"""
        self.theme_manager.apply_theme(QApplication.instance(), theme_name)

    def show_progress_dialog(self, title="处理中", can_cancel=True):
        """显示进度对话框"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        self.progress_dialog = ProgressDialog(self, title, can_cancel)
        if can_cancel:
            self.progress_dialog.rejected.connect(self.cancel_current_operation)
        self.progress_dialog.show()

    def close_progress_dialog(self):
        """关闭进度对话框"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def cancel_current_operation(self):
        """取消当前操作"""
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()
            self.current_thread.wait(1000)
            self.result_label.setText("操作已取消")
            logging.info("用户取消了当前操作")

    def on_song_folders_updated(self):
        """歌曲文件夹更新回调"""
        self.song_folders = self.song_folder_manager.get_folders()
        self.scan_song_files()

    def on_lyrics_folders_updated(self):
        """歌词文件夹更新回调"""
        self.lyrics_folders = self.lyrics_folder_manager.get_folders()
        self.scan_lyrics_files()

    def on_image_folders_updated(self):
        """图片文件夹更新回调"""
        self.image_folders = self.image_folder_manager.get_folders()
        self.scan_image_files()

    def scan_song_files(self):
        """扫描歌曲文件"""
        if not self.song_folders:
            return
        
        self.show_progress_dialog("扫描歌曲文件", True)
        
        self.current_thread = ScanFilesThread(
            self.song_folders, 
            {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.wma'},
            "歌曲"
        )
        self.current_thread.progress_updated.connect(self.on_scan_progress_updated)
        self.current_thread.finished.connect(self.on_song_files_scanned)
        self.current_thread.error_occurred.connect(self.on_scan_error)
        self.current_thread.start()

    def scan_lyrics_files(self):
        """扫描歌词文件"""
        if not self.lyrics_folders:
            return
        
        self.show_progress_dialog("扫描歌词文件", True)
        
        self.current_thread = ScanFilesThread(
            self.lyrics_folders,
            {'.lrc', '.txt', '.lyric', '.lrcx'},
            "歌词"
        )
        self.current_thread.progress_updated.connect(self.on_scan_progress_updated)
        self.current_thread.finished.connect(self.on_lyrics_files_scanned)
        self.current_thread.error_occurred.connect(self.on_scan_error)
        self.current_thread.start()

    def scan_image_files(self):
        """扫描图片文件"""
        if not self.image_folders:
            return
        
        self.show_progress_dialog("扫描图片文件", True)
        
        self.current_thread = ScanFilesThread(
            self.image_folders,
            {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'},
            "图片"
        )
        self.current_thread.progress_updated.connect(self.on_scan_progress_updated)
        self.current_thread.finished.connect(self.on_image_files_scanned)
        self.current_thread.error_occurred.connect(self.on_scan_error)
        self.current_thread.start()

    def on_scan_progress_updated(self, current, total, message):
        """扫描进度更新"""
        if self.progress_dialog:
            self.progress_dialog.update_progress(current, total, message)

    def on_song_files_scanned(self):
        """歌曲文件扫描完成"""
        self.song_files = self.current_thread.files_result
        self.close_progress_dialog()
        self.refresh_matches()
        logging.info(f"歌曲文件扫描完成: {len(self.song_files)} 个文件")

    def on_lyrics_files_scanned(self):
        """歌词文件扫描完成"""
        self.lyrics_files = self.current_thread.files_result
        self.close_progress_dialog()
        self.refresh_matches()
        logging.info(f"歌词文件扫描完成: {len(self.lyrics_files)} 个文件")

    def on_image_files_scanned(self):
        """图片文件扫描完成"""
        self.image_files = self.current_thread.files_result
        self.close_progress_dialog()
        self.refresh_matches()
        logging.info(f"图片文件扫描完成: {len(self.image_files)} 个文件")

    def on_scan_error(self, error_message):
        """扫描错误处理"""
        self.close_progress_dialog()
        QMessageBox.critical(self, "错误", error_message)
        logging.error(error_message)

    def refresh_matches(self):
        """刷新匹配 - 使用线程"""
        if self.df is None or not self.song_files:
            return
        
        self.show_progress_dialog("匹配歌曲", True)
        
        self.current_thread = MatchSongsThread(
            self.df,
            self.song_files,
            self.threshold_spin.value(),
            self.text_processor
        )
        self.current_thread.progress_updated.connect(self.on_match_progress_updated)
        self.current_thread.finished.connect(self.on_matches_completed)
        self.current_thread.error_occurred.connect(self.on_match_error)
        self.current_thread.start()

    def on_match_progress_updated(self, current, total, message):
        """匹配进度更新"""
        if self.progress_dialog:
            self.progress_dialog.update_progress(current, total, message)

    def on_matches_completed(self):
        """匹配完成"""
        self.match_results = self.current_thread.match_results
        self.match_scores = self.current_thread.match_scores
        self.close_progress_dialog()
        self.display_data()
        
        total = len(self.df)
        matched = len(self.match_results)
        logging.info(f"匹配完成: {matched}/{total} 首歌曲匹配成功 ({matched/total*100:.1f}%)")

    def on_match_error(self, error_message):
        """匹配错误处理"""
        self.close_progress_dialog()
        QMessageBox.critical(self, "错误", error_message)
        logging.error(error_message)

    def start_save_process(self):
        """开始保存过程"""
        if self.df is None:
            QMessageBox.warning(self, "警告", "请先加载Excel文件")
            return
            
        if not self.song_files:
            QMessageBox.warning(self, "警告", "请先选择歌曲文件夹")
            return
            
        if not self.output_folder:
            QMessageBox.warning(self, "警告", "请先选择输出文件夹")
            return
        
        if not self.match_results:
            QMessageBox.warning(self, "警告", "没有匹配的歌曲，请先进行匹配")
            return
        
        # 确保所有匹配的歌曲都被处理
        total_matched = len(self.match_results)
        total_songs = len(self.df)
        
        if total_matched < total_songs:
            reply = QMessageBox.question(
                self, "确认", 
                f"只匹配了 {total_matched}/{total_songs} 首歌曲，是否继续保存？\n"
                f"未匹配的歌曲将不会被处理。"
            )
            if reply != QMessageBox.Yes:
                return
        
        self.show_progress_dialog("保存元数据", True)
        
        self.current_thread = SaveDataThread(
            self.match_results,
            self.df,
            self.mapping_rules,
            self.output_folder,
            self.song_files,
            self.lyrics_files,
            self.image_files,
            self.lyrics_var.isChecked(),
            self.images_var.isChecked(),
            self.backup_var.isChecked(),
            self.text_processor
        )
        self.current_thread.progress_updated.connect(self.on_save_progress_updated)
        self.current_thread.finished.connect(self.on_save_completed)
        self.current_thread.error_occurred.connect(self.on_save_error)
        self.current_thread.start()

    def on_save_progress_updated(self, current, total, message):
        """保存进度更新"""
        if self.progress_dialog:
            self.progress_dialog.update_progress(current, total, message)

    def on_save_completed(self):
        """保存完成"""
        results = self.current_thread.results
        self.close_progress_dialog()
        self.show_save_result(results['success_count'], results['fail_count'], results['failed_songs'])

    def on_save_error(self, error_message):
        """保存错误处理"""
        self.close_progress_dialog()
        QMessageBox.critical(self, "错误", error_message)
        logging.error(error_message)

    def show_save_result(self, success_count, fail_count, failed_songs):
        """显示保存结果"""
        result_text = f"处理完成: 成功{success_count}首, 失败{fail_count}首"
        self.result_label.setText(result_text)
        
        if failed_songs:
            self.save_error_log(failed_songs, success_count, fail_count)
            
            error_msg = f"失败的歌曲:\n" + "\n".join(failed_songs[:10])
            if len(failed_songs) > 10:
                error_msg += f"\n... 还有{len(failed_songs)-10}个失败项，详见错误日志"
                
            QMessageBox.warning(self, "处理结果", f"{result_text}\n\n失败的歌曲已保存到桌面错误日志文件")
        else:
            QMessageBox.information(self, "处理结果", result_text)

    def save_error_log(self, failed_songs, success_count, fail_count):
        """保存错误日志到桌面"""
        try:
            desktop = Path.home() / "Desktop"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = desktop / f"歌曲元数据处理错误_{timestamp}.txt"
            
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write("歌曲元数据处理错误报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"处理结果: 成功{success_count}首, 失败{fail_count}首\n\n")
                f.write("失败的歌曲列表:\n")
                f.write("-" * 30 + "\n")
                for i, song in enumerate(failed_songs, 1):
                    f.write(f"{i}. {song}\n")
            
            logging.info(f"错误日志已保存到: {error_file}")
        except Exception as e:
            logging.error(f"保存错误日志失败: {str(e)}")

    def validate_matched_files(self):
        """验证所有匹配的文件是否存在"""
        if not self.match_results:
            QMessageBox.information(self, "提示", "没有匹配的歌曲")
            return
        
        missing_files = []
        accessible_files = []
        
        for index, file_path in self.match_results.items():
            if not os.path.exists(file_path):
                missing_files.append(file_path)
            else:
                accessible_files.append(file_path)
        
        # 显示验证结果
        result_text = f"文件验证结果:\n"
        result_text += f"可访问文件: {len(accessible_files)} 个\n"
        result_text += f"缺失文件: {len(missing_files)} 个\n"
        
        if missing_files:
            result_text += "\n缺失文件列表:\n"
            for i, file_path in enumerate(missing_files[:20], 1):  # 只显示前20个
                result_text += f"{i}. {file_path}\n"
            if len(missing_files) > 20:
                result_text += f"... 还有 {len(missing_files)-20} 个文件\n"
        
        # 在日志窗口中显示详细结果
        if self.log_window:
            self.log_window.text_edit.append("=== 文件验证结果 ===\n")
            self.log_window.text_edit.append(result_text)
        
        QMessageBox.information(self, "文件验证结果", result_text)
        
        # 保存缺失文件列表到桌面
        if missing_files:
            self.save_missing_files_list(missing_files)

    def save_missing_files_list(self, missing_files):
        """保存缺失文件列表到桌面"""
        try:
            desktop = Path.home() / "Desktop"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            missing_file = desktop / f"缺失文件列表_{timestamp}.txt"
            
            with open(missing_file, 'w', encoding='utf-8') as f:
                f.write("缺失文件列表\n")
                f.write("=" * 50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总缺失文件数: {len(missing_files)}\n\n")
                f.write("缺失文件:\n")
                f.write("-" * 30 + "\n")
                for i, file_path in enumerate(missing_files, 1):
                    f.write(f"{i}. {file_path}\n")
            
            logging.info(f"缺失文件列表已保存到: {missing_file}")
            QMessageBox.information(self, "提示", f"缺失文件列表已保存到桌面: {missing_file.name}")
            
        except Exception as e:
            logging.error(f"保存缺失文件列表失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"保存缺失文件列表失败: {str(e)}")

    def load_excel(self):
        """加载Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                self.file_label.setText(f"已加载: {os.path.basename(file_path)}")
                self.display_data()
                self.setup_field_mapping()
                self.refresh_matches()
                logging.info(f"成功加载Excel文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载Excel文件失败: {str(e)}")
                logging.error(f"加载Excel文件失败: {str(e)}")

    def load_output_folder(self):
        """选择输出文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        
        if folder_path:
            self.output_folder = folder_path
            self.output_label.setText(f"已选择: {os.path.basename(folder_path)}")
            logging.info(f"成功选择输出文件夹: {folder_path}")

    def display_data(self):
        """显示数据"""
        self.tree_widget.clear()
        
        if self.df is not None:
            items = []
            
            for index, row in self.df.iterrows():
                excel_title = str(row.get('标题', ''))
                matched_file = self.match_results.get(index)
                lyrics_status = self.get_lyrics_status(excel_title)
                image_status = self.get_image_status(excel_title)
                
                match_score = self.match_scores.get(index, 0)
                match_rate = f"{match_score:.1%}" if matched_file else "0%"
                
                item = QTreeWidgetItem([
                    "✓",
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
                ])
                
                color = self.get_row_status_color(matched_file, match_score)
                for i in range(11):
                    item.setBackground(i, color)
                
                items.append(item)
            
            self.tree_widget.addTopLevelItems(items)
            self.update_stats()

    def get_row_status_color(self, matched_file, match_score):
        """根据匹配状态确定行的颜色"""
        if matched_file:
            if match_score > 0.9:
                return QColor('#e8f5e8')
            elif match_score > 0.7:
                return QColor('#fff9e6')
            else:
                return QColor('#ffe6e6')
        else:
            return QColor('#f5f5f5')

    def update_stats(self):
        """更新匹配统计信息"""
        if self.df is None:
            return
            
        total = len(self.df)
        matched = len(self.match_results)
        unmatched = total - matched
        
        failed = 0
        for index in range(total):
            if index not in self.match_results and self.match_scores.get(index, 0) < 0.5:
                failed += 1
        
        self.stats_label.setText(f"匹配统计: 成功 {matched} 首, 失败 {failed} 首, 未匹配 {unmatched} 首")

    def search_data(self):
        """搜索数据"""
        search_term = self.search_edit.text().lower()
        
        if not search_term:
            self.display_data()
            return
        
        self.tree_widget.clear()
        
        if self.df is not None:
            for index, row in self.df.iterrows():
                match_found = False
                for col in ['标题', '艺术家', '专辑', '年份', '语种']:
                    if search_term in str(row.get(col, '')).lower():
                        match_found = True
                        break
                
                if match_found:
                    excel_title = str(row.get('标题', ''))
                    matched_file = self.match_results.get(index)
                    lyrics_status = self.get_lyrics_status(excel_title)
                    image_status = self.get_image_status(excel_title)
                    
                    match_score = self.match_scores.get(index, 0)
                    match_rate = f"{match_score:.1%}" if matched_file else "0%"
                    
                    item = QTreeWidgetItem([
                        "✓",
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
                    ])
                    
                    color = self.get_row_status_color(matched_file, match_score)
                    for i in range(11):
                        item.setBackground(i, color)
                    
                    self.tree_widget.addTopLevelItem(item)
                    
            self.update_stats()

    def clear_search(self):
        """清除搜索"""
        self.search_edit.clear()

    def get_lyrics_status(self, title):
        """获取歌词文件状态"""
        if not self.lyrics_files:
            return "无歌词文件夹"
            
        clean_title = self.text_processor.multi_language_clean(title)
        
        for lyrics in self.lyrics_files:
            clean_filename = self.text_processor.multi_language_clean(lyrics['name_only'])
            
            if clean_title == clean_filename:
                return "歌词已匹配"
            elif clean_title in clean_filename or clean_filename in clean_title:
                return "歌词已匹配"
            elif self.text_processor.enhanced_similarity(clean_title, clean_filename) > 0.7:
                return "歌词已匹配"
                
        return "歌词未匹配"

    def get_image_status(self, title):
        """获取图片文件状态"""
        if not self.image_files:
            return "无图片文件夹"
            
        clean_title = self.text_processor.multi_language_clean(title)
        
        for image in self.image_files:
            clean_filename = self.text_processor.multi_language_clean(image['name_only'])
            
            if clean_title == clean_filename:
                return "图片已匹配"
            elif clean_title in clean_filename or clean_filename in clean_title:
                return "图片已匹配"
            elif self.text_processor.enhanced_similarity(clean_title, clean_filename) > 0.7:
                return "图片已匹配"
                
        return "图片未匹配"

    def setup_field_mapping(self):
        """设置字段映射"""
        if self.df is not None:
            self.map_tree.clear()
            
            standard_fields = ["标题", "艺术家", "专辑", "年份", "语种", "歌词", "作词", "作曲", "封面", 
                              "注释", "出品", "版权", "QQ音乐", "网易云音乐", "酷狗音乐", "5sing", "酷我音乐"]
            
            excel_columns = self.df.columns.tolist()
            
            for excel_col in excel_columns:
                matched = False
                for std_field in standard_fields:
                    if std_field in excel_col or excel_col in std_field:
                        item = QTreeWidgetItem([excel_col, std_field, "自动"])
                        self.mapping_rules[excel_col] = std_field
                        self.map_tree.addTopLevelItem(item)
                        matched = True
                        break
                
                if not matched:
                    item = QTreeWidgetItem([excel_col, "未匹配", "手动"])
                    self.map_tree.addTopLevelItem(item)

    def auto_match_fields(self):
        """自动匹配字段"""
        if self.df is not None:
            for i in range(self.map_tree.topLevelItemCount()):
                item = self.map_tree.topLevelItem(i)
                excel_field = item.text(0)
                
                if "标题" in excel_field or "歌曲" in excel_field or "歌名" in excel_field:
                    item.setText(1, "标题")
                    self.mapping_rules[excel_field] = "标题"
                elif "艺术家" in excel_field or "歌手" in excel_field or "演唱" in excel_field:
                    item.setText(1, "艺术家")
                    self.mapping_rules[excel_field] = "艺术家"
                elif "专辑" in excel_field or "唱片" in excel_field:
                    item.setText(1, "专辑")
                    self.mapping_rules[excel_field] = "专辑"
                elif "年份" in excel_field or "年代" in excel_field:
                    item.setText(1, "年份")
                    self.mapping_rules[excel_field] = "年份"
                elif "语种" in excel_field or "语言" in excel_field:
                    item.setText(1, "语种")
                    self.mapping_rules[excel_field] = "语种"
                elif "歌词" in excel_field:
                    item.setText(1, "歌词")
                    self.mapping_rules[excel_field] = "歌词"
                elif "作词" in excel_field:
                    item.setText(1, "作词")
                    self.mapping_rules[excel_field] = "作词"
                elif "作曲" in excel_field:
                    item.setText(1, "作曲")
                    self.mapping_rules[excel_field] = "作曲"
                elif "封面" in excel_field or "图片" in excel_field:
                    item.setText(1, "封面")
                    self.mapping_rules[excel_field] = "封面"
            
            QMessageBox.information(self, "提示", "自动匹配完成")

    def manual_match_fields(self):
        """手动匹配字段"""
        current_item = self.map_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个字段进行手动匹配")
            return
        
        excel_field = current_item.text(0)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("手动字段匹配")
        dialog.setModal(True)
        dialog.resize(300, 150)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"Excel字段: {excel_field}"))
        layout.addWidget(QLabel("选择目标字段:"))
        
        target_combo = QComboBox()
        standard_fields = ["标题", "艺术家", "专辑", "年份", "语种", "歌词", "作词", "作曲", "出品", 
                          "版权", "封面", "注释", "QQ音乐", "网易云音乐", "酷狗音乐", "5sing", "酷我音乐"]
        target_combo.addItems(standard_fields)
        layout.addWidget(target_combo)
        
        def confirm_match():
            target_field = target_combo.currentText()
            if target_field:
                current_item.setText(1, target_field)
                current_item.setText(2, "手动")
                self.mapping_rules[excel_field] = target_field
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "警告", "请选择一个目标字段")
        
        button_layout = QHBoxLayout()
        confirm_btn = QPushButton("确认")
        confirm_btn.clicked.connect(confirm_match)
        button_layout.addWidget(confirm_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def auto_match_songs(self):
        """自动匹配歌曲"""
        if self.df is None or not self.song_files:
            QMessageBox.warning(self, "警告", "请先加载Excel文件和歌曲文件夹")
            return
            
        self.refresh_matches()
        QMessageBox.information(self, "提示", "自动匹配完成")

    def manual_match_songs(self):
        """人工匹配歌曲"""
        if self.df is None or not self.song_files:
            QMessageBox.warning(self, "警告", "请先加载Excel文件和歌曲文件夹")
            return
            
        # 选择要匹配的行
        if self.selected_row_index is None:
            QMessageBox.warning(self, "警告", "请先在数据表格中选择一行")
            return
            
        row = self.df.iloc[self.selected_row_index]
        title = str(row.get('标题', ''))
        self.show_manual_match_dialog(self.selected_row_index, title)

    def clear_all_matches(self):
        """清除所有匹配"""
        if not self.match_results:
            QMessageBox.information(self, "提示", "没有匹配记录可清除")
            return
            
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有匹配记录吗？"
        )
        if reply == QMessageBox.Yes:
            self.match_results = {}
            self.match_scores = {}
            self.refresh_matches()
            QMessageBox.information(self, "成功", "已清除所有匹配记录")

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = SongMetadataEditorPyQt()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
