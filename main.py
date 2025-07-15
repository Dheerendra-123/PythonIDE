import sys
import os
import queue
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileDialog, QAction,
    QTabWidget, QTextEdit, QSplitter, QVBoxLayout, QWidget,
    QMessageBox,QTreeView, QFileSystemModel,
    QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame,
    QCheckBox, QShortcut, QMenu, QInputDialog, QToolButton
)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QKeySequence, QFont, QTextCharFormat, QTextCursor, QColor, QTextDocument
from editor import CodeEditor
from runner import run_code, run_command

class TerminalWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ide = parent
        self.setReadOnly(False)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                border: none;
                selection-background-color: #264f78;
            }
        """)
        font = QFont("Consolas", 12)
        self.setFont(font)
        
        self.input_queue = queue.Queue()
        self.current_directory = os.getcwd()
        self.command_history = []
        self.history_index = -1
        self.input_mode = False
        self.prompt_position = 0
        
        self.clear_terminal()
        self.show_prompt()
        
    def clear_terminal(self):
        self.clear()
        self.append_output("Python IDE Terminal", QColor("#569cd6"))
        self.append_output(f"Working directory: {self.current_directory}", QColor("#6a9955"))
        self.append_output("Type 'help' for available commands\n", QColor("#6a9955"))
        
    def show_prompt(self):
        self.input_mode = True
        prompt = f"{self.current_directory}> "
        self.append_output(prompt, QColor("#569cd6"), newline=False)
        self.prompt_position = self.textCursor().position()
        
    def append_output(self, text, color=QColor("#d4d4d4"), newline=True):
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self.moveCursor(QTextCursor.End)
        self.setCurrentCharFormat(fmt)
        if newline:
            self.insertPlainText(text + "\n")
        else:
            self.insertPlainText(text)
        self.moveCursor(QTextCursor.End)
        
    def keyPressEvent(self, event):
        if not self.input_mode:
            return
            
        cursor = self.textCursor()
        
        if cursor.position() < self.prompt_position:
            cursor.setPosition(self.prompt_position)
            self.setTextCursor(cursor)
            
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_command()
        elif event.key() == Qt.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key_Down:
            self.navigate_history(1)
        elif event.key() == Qt.Key_Backspace:
            if cursor.position() > self.prompt_position:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key_Left:
            if cursor.position() > self.prompt_position:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key_Home:
            cursor.setPosition(self.prompt_position)
            self.setTextCursor(cursor)
        else:
            super().keyPressEvent(event)
            
    def get_current_input(self):
        cursor = self.textCursor()
        cursor.setPosition(self.prompt_position)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        return cursor.selectedText()
        
    def set_current_input(self, text):
        cursor = self.textCursor()
        cursor.setPosition(self.prompt_position)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.insertText(text)
        
    def navigate_history(self, direction):
        if not self.command_history:
            return
            
        self.history_index += direction
        self.history_index = max(-1, min(self.history_index, len(self.command_history) - 1))
        
        if self.history_index == -1:
            self.set_current_input("")
        else:
            self.set_current_input(self.command_history[self.history_index])
            
    def handle_command(self):
        command = self.get_current_input().strip()
        self.append_output("")  # New line
        
        if not command:
            self.show_prompt()
            return
            
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = -1
        
        if command == "clear":
            self.clear_terminal()
            self.show_prompt()
            return
        elif command == "help":
            self.show_help()
            self.show_prompt()
            return
        elif command.startswith("cd "):
            self.change_directory(command[3:].strip())
            self.show_prompt()
            return
        elif command == "pwd":
            self.append_output(self.current_directory, QColor("#d4d4d4"))
            self.show_prompt()
            return
        elif command == "ls" or command == "dir":
            self.list_directory()
            self.show_prompt()
            return
            
        self.input_mode = False
        self.run_system_command(command)
        
    def show_help(self):
        help_text = """
        Available commands:
        clear    - Clear the terminal
        cd <dir> - Change directory
        pwd      - Print working directory
        ls/dir   - List directory contents
        help     - Show this help message
        
        You can also run any system command or Python file.
        """
        self.append_output(help_text, QColor("#6a9955"))
        
    def change_directory(self, path):
        try:
            if path == "..":
                new_path = os.path.dirname(self.current_directory)
            elif os.path.isabs(path):
                new_path = path
            else:
                new_path = os.path.join(self.current_directory, path)
                
            if os.path.exists(new_path) and os.path.isdir(new_path):
                self.current_directory = os.path.abspath(new_path)
                self.append_output(f"Changed to: {self.current_directory}", QColor("#d4d4d4"))
            else:
                self.append_output(f"Directory not found: {path}", QColor("#f44747"))
        except Exception as e:
            self.append_output(f"Error: {str(e)}", QColor("#f44747"))
            
    def list_directory(self):
        try:
            items = os.listdir(self.current_directory)
            for item in sorted(items):
                item_path = os.path.join(self.current_directory, item)
                if os.path.isdir(item_path):
                    self.append_output(f"📁 {item}", QColor("#569cd6"))
                else:
                    self.append_output(f"📄 {item}", QColor("#d4d4d4"))
        except Exception as e:
            self.append_output(f"Error: {str(e)}", QColor("#f44747"))
            
    def run_system_command(self, command):
        try:
            result, return_code = run_command(command, self.current_directory)
            
            if return_code == 0:
                self.append_output(result, QColor("#d4d4d4"))
            else:
                self.append_output(result, QColor("#f44747"))
                
        except Exception as e:
            self.append_output(f"Error: {str(e)}", QColor("#f44747"))
        finally:
            self.input_mode = True
            self.show_prompt()
            
    def run_python_code(self, code, file_path=None):
        self.input_mode = False
        
        try:
            display_name = file_path if file_path else "*untitled"
            self.append_output(f"Running: {display_name}", QColor("#569cd6"))
            self.append_output(f"Working directory: {self.current_directory}", QColor("#6a9955"))
            self.append_output("-" * 50, QColor("#6a9955"))
            
            result, return_code, actual_path = run_code(code, file_path, self.input_queue)
            
            # Display output
            if return_code == 0:
                if result.strip():
                    self.append_output(result, QColor("#d4d4d4"))
                else:
                    self.append_output("Program completed successfully", QColor("#4ec9b0"))
            else:
                self.append_output(result, QColor("#f44747"))
                
            self.append_output("-" * 50, QColor("#6a9955"))
            
        except Exception as e:
            self.append_output(f"Error: {str(e)}", QColor("#f44747"))
        finally:
            self.input_mode = True
            self.show_prompt()

class FindReplaceWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ide = parent
        self.current_editor = None
        self.search_results = []
        self.current_result_index = -1
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 2px;
                padding: 3px;
                font-size: 11px;
            }
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 2px;
                padding: 3px 8px;
                font-size: 11px;
                background-color: #fff;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QCheckBox {
                font-size: 11px;
            }
            QLabel {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(3)
        main_layout.setContentsMargins(8, 5, 8, 5)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Find and Replace")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(23, 23)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                font-weight: bold;
                font-size: 14px;
                background-color: #ff4444;
                color: white;
            }
        """)
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        find_layout = QHBoxLayout()
        find_layout.setSpacing(5)
        
        find_layout.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.setFixedHeight(22)
        self.find_input.textChanged.connect(self.on_find_text_changed)
        find_layout.addWidget(self.find_input)
        
        self.find_next_btn = QPushButton("↓")
        self.find_next_btn.setFixedSize(24, 22)
        self.find_next_btn.setToolTip("Find Next")
        self.find_next_btn.clicked.connect(self.find_next)
        find_layout.addWidget(self.find_next_btn)
        
        self.find_prev_btn = QPushButton("↑")
        self.find_prev_btn.setFixedSize(24, 22)
        self.find_prev_btn.setToolTip("Find Previous")
        self.find_prev_btn.clicked.connect(self.find_previous)
        find_layout.addWidget(self.find_prev_btn)
        
        self.match_case_cb = QCheckBox("Aa")
        self.match_case_cb.setToolTip("Match Case")
        self.match_case_cb.stateChanged.connect(self.on_find_text_changed)
        find_layout.addWidget(self.match_case_cb)
        
        main_layout.addLayout(find_layout)
        
        replace_layout = QHBoxLayout()
        replace_layout.setSpacing(5)
        
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.setFixedHeight(22)
        replace_layout.addWidget(self.replace_input)
        
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setFixedHeight(22)
        self.replace_btn.clicked.connect(self.replace_current)
        replace_layout.addWidget(self.replace_btn)
        
        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setFixedHeight(22)
        self.replace_all_btn.clicked.connect(self.replace_all)
        replace_layout.addWidget(self.replace_all_btn)
        
        main_layout.addLayout(replace_layout)
        
        self.setLayout(main_layout)
        self.setFixedHeight(85)
        self.hide()
        
        self.find_input.returnPressed.connect(self.find_next)
        
    def show_for_editor(self, editor):
        self.current_editor = editor
        self.show()
        self.find_input.setFocus()
        
        cursor = editor.textCursor()
        if cursor.hasSelection():
            self.find_input.setText(cursor.selectedText())
        self.find_input.selectAll()
        
    def on_find_text_changed(self):
        if not self.current_editor:
            return
            
        find_text = self.find_input.text()
        if not find_text:
            self.clear_highlights()
            self.search_results = []
            return
            
        self.highlight_all_matches(find_text)
        
    def highlight_all_matches(self, find_text):
        if not self.current_editor:
            return
            
        self.clear_highlights()

        flags = QTextDocument.FindFlag(0)
        if self.match_case_cb.isChecked():
            flags |= QTextDocument.FindCaseSensitively
            
        self.search_results = []
        cursor = self.current_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        extra_selections = []
        
        while True:
            cursor = self.current_editor.document().find(find_text, cursor, flags)
            if cursor.isNull():
                break

            self.search_results.append({
                'start': cursor.selectionStart(),
                'end': cursor.selectionEnd()
            })
            
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(255, 255, 0, 100)) 
            
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = highlight_format
            extra_selections.append(selection)
            
        self.current_editor.setExtraSelections(extra_selections)
        
        self.current_result_index = -1
            
    def clear_highlights(self):
        if self.current_editor:
            self.current_editor.setExtraSelections([])
            
    def find_next(self):
        if not self.search_results:
            return
            
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        self.move_to_result(self.current_result_index)
        
    def find_previous(self):
        if not self.search_results:
            return
            
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
        self.move_to_result(self.current_result_index)
        
    def move_to_result(self, index):
        if not self.current_editor or index >= len(self.search_results):
            return
            
        result = self.search_results[index]
        
        cursor = self.current_editor.textCursor()
        cursor.setPosition(result['start'])
        cursor.setPosition(result['end'], QTextCursor.KeepAnchor)
        self.current_editor.setTextCursor(cursor)
        self.current_editor.ensureCursorVisible()
        
    def replace_current(self):
        if not self.current_editor:
            return
            
        cursor = self.current_editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
            self.on_find_text_changed() 
            
    def replace_all(self):
        if not self.current_editor:
            return
            
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        
        if not find_text:
            return
            
        text = self.current_editor.toPlainText()
        
        if self.match_case_cb.isChecked():
            new_text = text.replace(find_text, replace_text)
        else:
            import re
            new_text = re.sub(re.escape(find_text), replace_text, text, flags=re.IGNORECASE)
            
        self.current_editor.setPlainText(new_text)
        self.on_find_text_changed()  
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTreeView, QFileSystemModel,
    QToolButton, QPushButton, QInputDialog, QMessageBox, QFileDialog, QMenu
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDir


class FileExplorer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ide = parent
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QFrame()
        header.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;")
        header.setFixedHeight(30)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 5, 8, 5)

        explorer_label = QLabel("EXPLORER")
        explorer_label.setFont(QFont("Arial", 9, QFont.Bold))
        explorer_label.setStyleSheet("color: #666; border: none;")
        header_layout.addWidget(explorer_label)
        header_layout.addStretch()

        add_file_btn = QToolButton()
        add_file_btn.setText("📄")
        add_file_btn.setToolTip("New File")
        add_file_btn.setFixedSize(20, 20)
        add_file_btn.clicked.connect(self.create_new_file)
        add_file_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        header_layout.addWidget(add_file_btn)

        add_folder_btn = QToolButton()
        add_folder_btn.setText("📁")
        add_folder_btn.setToolTip("New Folder")
        add_folder_btn.setFixedSize(20, 20)
        add_folder_btn.clicked.connect(self.create_new_folder)
        add_folder_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        header_layout.addWidget(add_folder_btn)

        header.setLayout(header_layout)
        layout.addWidget(header)

        self.folder_name_label = QLabel()
        self.folder_name_label.setFont(QFont("Arial", 9))
        self.folder_name_label.setStyleSheet("color: #333; padding: 4px 8px; font-weight: bold;")
        layout.addWidget(self.folder_name_label)


        self.tree = QTreeView()
        self.model = QFileSystemModel()
        current_dir = QDir.currentPath()
        self.model.setRootPath(current_dir)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(current_dir))
        self.update_folder_name(current_dir)  

        self.tree.hideColumn(1) 
        self.tree.hideColumn(2)  
        self.tree.hideColumn(3)  
        self.tree.header().hide()  

        self.tree.setStyleSheet("""
            QTreeView {
                border: none;
                background-color: #fafafa;
                alternate-background-color: #f5f5f5;
                font-size: 18px;
            }
            QTreeView::item {
                padding: 2px 6px;
                border: none;
                height: 20px;
                padding-bottom: 4px;
            }
            QTreeView::item:selected {
                background-color: none;
                color: black;
            }
            QTreeView::item:hover {
                background-color: #e5e5e5;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings,
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
        """)

        self.tree.doubleClicked.connect(self.on_file_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree)


        footer = QFrame()
        footer.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #d0d0d0;")
        footer.setFixedHeight(38)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(9, 6, 9, 6)

        select_folder_btn = QPushButton("📁 Select Folder")
        select_folder_btn.setFixedHeight(24)
        select_folder_btn.clicked.connect(self.select_folder)
        select_folder_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 2px;
                padding: 4px 10px;
                font-size: 15px;
                background-color: #fff;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
        """)
        footer_layout.addWidget(select_folder_btn)

        footer.setLayout(footer_layout)
        layout.addWidget(footer)

        self.setLayout(layout)

    def update_folder_name(self, path):
        folder_name = os.path.basename(path)
        if not folder_name:
            folder_name = path 
        self.folder_name_label.setText(folder_name)

    def create_new_file(self):
        current_path = self.model.rootPath()
        name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and name:
            if not name.endswith('.py'):
                name += '.py'
            file_path = os.path.join(current_path, name)
            try:
                with open(file_path, 'w') as f:
                    f.write("")
                self.parent_ide.open_file_by_path(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create file: {str(e)}")

    def create_new_folder(self):
        current_path = self.model.rootPath()
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            folder_path = os.path.join(current_path, name)
            try:
                os.makedirs(folder_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")

    def show_context_menu(self, position):
        index = self.tree.indexAt(position)
        menu = QMenu()

        if index.isValid():
            file_path = self.model.filePath(index)
            if os.path.isfile(file_path):
                open_action = menu.addAction("Open")
                open_action.triggered.connect(lambda: self.parent_ide.open_file_by_path(file_path))

            menu.addSeparator()
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self.delete_item(file_path))

        menu.addAction("New File", self.create_new_file)
        menu.addAction("New Folder", self.create_new_folder)

        menu.exec_(self.tree.mapToGlobal(position))

    def delete_item(self, path):
        reply = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {os.path.basename(path)}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    import shutil
                    shutil.rmtree(path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {str(e)}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.model.setRootPath(folder)
            self.tree.setRootIndex(self.model.index(folder))
            self.update_folder_name(folder)

    def on_file_double_click(self, index):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.parent_ide.open_file_by_path(file_path)



class PythonIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python IDE")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()
        self.init_menu()
        self.init_shortcuts()
        
        self.open_files = {} 
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)   
        main_splitter = QSplitter(Qt.Horizontal)    
        self.file_explorer = FileExplorer(self)
        self.file_explorer.setFixedWidth(250)
        main_splitter.addWidget(self.file_explorer)
        
        right_splitter = QSplitter(Qt.Vertical)
  
        editor_container = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        self.find_replace_widget = FindReplaceWidget(self)
        editor_layout.addWidget(self.find_replace_widget)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setMovable(True)
        
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
            QTabBar::close-button {
                image: url(resources/close.png);
                subcontrol-position: right;
                margin-left: 4px;
                width: 14px;
                height: 14px;
            }
        """)
        
        editor_layout.addWidget(self.tab_widget)
        editor_container.setLayout(editor_layout)
        right_splitter.addWidget(editor_container)
        
        self.terminal = TerminalWidget(self)
        right_splitter.addWidget(self.terminal)
        
        right_splitter.setSizes([600, 200])
        
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([250, 950])
        
        main_layout.addWidget(main_splitter)
        central_widget.setLayout(main_layout)
        
        self.create_new_tab()
        
    def init_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.create_new_tab)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu('Edit')
        
        find_action = QAction('Find and Replace', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(find_action)
        
        run_menu = menubar.addMenu('Run')
        
        run_action = QAction('Run', self)
        run_action.setShortcut('Ctrl+R')
        run_action.triggered.connect(self.run_current_file)
        run_menu.addAction(run_action)
        
    def init_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+T"), self, self.create_new_tab)
        QShortcut(QKeySequence("Escape"), self, self.hide_find_replace)
        
    def create_new_tab(self, file_path=None, content=""):
        editor = CodeEditor()
        editor.setPlainText(content)
        
        if file_path:
            tab_name = os.path.basename(file_path)
            self.open_files[file_path] = self.tab_widget.addTab(editor, tab_name)
            editor.file_path = file_path
        else:
            tab_index = self.tab_widget.addTab(editor, "*untitled")
            editor.file_path = None
            
        self.tab_widget.setCurrentWidget(editor)
        editor.setFocus()
        
        editor.textChanged.connect(lambda: self.mark_tab_modified(editor))
        
        return editor
        
    def mark_tab_modified(self, editor):
        tab_index = self.tab_widget.indexOf(editor)
        if tab_index != -1:
            current_text = self.tab_widget.tabText(tab_index)
            if not current_text.endswith('*'):
                self.tab_widget.setTabText(tab_index, current_text + '*')
                
    def remove_modified_indicator(self, editor):
        tab_index = self.tab_widget.indexOf(editor)
        if tab_index != -1:
            current_text = self.tab_widget.tabText(tab_index)
            if current_text.endswith('*'):
                self.tab_widget.setTabText(tab_index, current_text[:-1])
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            self.open_file_by_path(file_path)
            
    def open_file_by_path(self, file_path):
        if file_path in self.open_files:
            tab_index = self.open_files[file_path]
            self.tab_widget.setCurrentIndex(tab_index)
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                editor = self.create_new_tab(file_path, content)
                self.remove_modified_indicator(editor)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
            
    def save_file(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            if hasattr(current_editor, 'file_path') and current_editor.file_path:
                self.save_file_to_path(current_editor, current_editor.file_path)
            else:
                self.save_file_as()
                
    def save_file_as(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save File", "", "Python Files (*.py);;All Files (*)"
            )
            if file_path:
                self.save_file_to_path(current_editor, file_path)
                
    def save_file_to_path(self, editor, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(editor.toPlainText())
            
            tab_index = self.tab_widget.indexOf(editor)
            tab_name = os.path.basename(file_path)
            self.tab_widget.setTabText(tab_index, tab_name)
            
            if hasattr(editor, 'file_path') and editor.file_path in self.open_files:
                del self.open_files[editor.file_path]
            
            editor.file_path = file_path
            self.open_files[file_path] = tab_index
            
            self.remove_modified_indicator(editor)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
            
    def close_tab(self, tab_index):
        editor = self.tab_widget.widget(tab_index)
        
        tab_text = self.tab_widget.tabText(tab_index)
        if tab_text.endswith('*'):
            reply = QMessageBox.question(
                self, "Unsaved Changes", 
                f"'{tab_text[:-1]}' has unsaved changes. Do you want to save?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        if hasattr(editor, 'file_path') and editor.file_path in self.open_files:
            del self.open_files[editor.file_path]
        
        for file_path, index in self.open_files.items():
            if index > tab_index:
                self.open_files[file_path] = index - 1
        
        self.tab_widget.removeTab(tab_index)
        
        if self.tab_widget.count() == 0:
            self.create_new_tab()
            
    def close_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.close_tab(current_index)
            
    def show_find_replace(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            self.find_replace_widget.show_for_editor(current_editor)
            
    def hide_find_replace(self):
        self.find_replace_widget.hide()
        
    def run_current_file(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            code = current_editor.toPlainText()
            file_path = getattr(current_editor, 'file_path', None)
            self.terminal.run_python_code(code, file_path)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ide = PythonIDE()
    ide.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()