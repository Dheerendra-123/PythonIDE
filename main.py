import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileDialog, QAction,
    QTabWidget, QTextEdit, QSplitter, QVBoxLayout, QWidget,
    QMessageBox, QTabBar, QTreeView, QFileSystemModel,
    QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame,
    QCheckBox, QShortcut, QMenu, QInputDialog, QToolButton
)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QKeySequence, QFont, QTextCharFormat, QTextCursor, QColor, QTextDocument
from editor import CodeEditor
from runner import run_code

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
        close_btn.setFixedSize(18, 18)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                font-weight: bold;
                font-size: 12px;
                background-color: transparent;
            }
            QPushButton:hover {
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
        
        while True:
            cursor = self.current_editor.document().find(find_text, cursor, flags)
            if cursor.isNull():
                break
            self.search_results.append(cursor.position())
            
        extra_selections = []
        for pos in self.search_results:
            cursor = self.current_editor.textCursor()
            cursor.setPosition(pos)
            cursor.setPosition(pos + len(find_text), QTextCursor.KeepAnchor)
            
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(255, 255, 0, 100))  # Yellow highlight
            
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = highlight_format
            extra_selections.append(selection)
            
        self.current_editor.setExtraSelections(extra_selections)
            
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
            
        pos = self.search_results[index]
        find_text = self.find_input.text()
        
        cursor = self.current_editor.textCursor()
        cursor.setPosition(pos)
        cursor.setPosition(pos + len(find_text), QTextCursor.KeepAnchor)
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
        
        title = QLabel("EXPLORER")
        title.setFont(QFont("Arial", 9, QFont.Bold))
        title.setStyleSheet("color: #666; border: none;")
        header_layout.addWidget(title)
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
        

        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.currentPath()))
        
        # Hide unnecessary columns
        self.tree.hideColumn(1)  # Size
        self.tree.hideColumn(2)  # Type
        self.tree.hideColumn(3)  # Date Modified

        self.tree.setStyleSheet("""
            QTreeView {
                border: none;
                background-color: #fafafa;
                alternate-background-color: #f5f5f5;
                font-size: 16px;
            }
            QTreeView::item {
                padding: 2px 6px;
                border: none;
                height: 20px;
            }
            QTreeView::item:selected {
                background-color: none;
                color: black;
            }
            QTreeView::item:hover {
                background-color: #e5e5e5;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
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
        
        # General actions
        menu.addAction("New File", self.create_new_file)
        menu.addAction("New Folder", self.create_new_folder)
        
        menu.exec_(self.tree.mapToGlobal(position))
    
    def delete_item(self, path):
        reply = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {os.path.basename(path)}?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    os.rmdir(path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {str(e)}")
        
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.model.setRootPath(folder)
            self.tree.setRootIndex(self.model.index(folder))
            
    def on_file_double_click(self, index):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path) and file_path.endswith('.py'):
            self.parent_ide.open_file_by_path(file_path)

class CustomTabBar(QTabBar):
    def __init__(self, new_tab_callback):
        super().__init__()
        self.new_tab_callback = new_tab_callback
        self.setTabsClosable(True)

    def mouseReleaseEvent(self, event):
        index = self.tabAt(event.pos())
        if index != -1 and self.tabText(index) == '+':
            self.new_tab_callback()
        else:
            super().mouseReleaseEvent(event)

class CustomTabWidget(QTabWidget):
    def __init__(self, ide_instance):
        super().__init__()
        self.ide_instance = ide_instance
        self.tab_bar = CustomTabBar(self.new_tab)
        self.setTabBar(self.tab_bar)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.add_plus_tab()

    def add_editor_tab(self, editor, title):
        if self.count() > 0 and self.tabText(self.count() - 1) == '+':
            self.removeTab(self.count() - 1)

        index = self.count()
        self.insertTab(index, editor, title)
        self.setCurrentIndex(index)
        self.add_plus_tab()
        return index

    def add_plus_tab(self):
        if self.count() == 0 or self.tabText(self.count() - 1) != '+':
            plus_tab = QWidget()
            self.addTab(plus_tab, '+')
            self.tabBar().setFont(QFont("Arial", 10))
            self.tabBar().setTabButton(self.count() - 1, QTabBar.RightSide, None)

    def new_tab(self):
        editor = CodeEditor()
        font = QFont("Consolas", 16)
        editor.setFont(font)
        self.ide_instance.file_paths[editor] = None
        self.add_editor_tab(editor, "*untitled")

    def close_tab(self, index):
        if self.tabText(index) == '+':
            return
        self.ide_instance.close_tab(index)
        self.removeTab(index)
        self.add_plus_tab()

class PythonIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Python IDE")
        self.setGeometry(100, 100, 1200, 800)

        self.main_splitter = QSplitter(Qt.Horizontal)

        self.file_explorer = FileExplorer(self)
        self.main_splitter.addWidget(self.file_explorer)

        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        self.find_replace_widget = FindReplaceWidget(self)
        editor_layout.addWidget(self.find_replace_widget)
        
        self.editor_splitter = QSplitter(Qt.Vertical)
        self.file_paths = {}
        self.tabs = CustomTabWidget(self)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #111; color: #0f0; font-family: Consolas;")
        font = QFont("Consolas", 14)
        self.terminal.setFont(font)

        self.editor_splitter.addWidget(self.tabs)
        self.editor_splitter.addWidget(self.terminal)
        self.editor_splitter.setStretchFactor(0, 3)
        self.editor_splitter.setStretchFactor(1, 1)

        editor_layout.addWidget(self.editor_splitter)
        editor_widget.setLayout(editor_layout)
        
        self.main_splitter.addWidget(editor_widget)
        
        self.main_splitter.setSizes([250, 950])
        self.main_splitter.setCollapsible(0, True) 
        
        self.setCentralWidget(self.main_splitter)

        self.create_menu()
        self.setup_shortcuts()
        self.new_tab()

    def create_menu(self):
        menu = self.menuBar()
        font = QFont("Arial", 10)
        file_menu = menu.addMenu("File")
        edit_menu = menu.addMenu("Edit")
        view_menu = menu.addMenu("View")
        menu.setFont(font)
        run_menu = menu.addMenu("Run")

        # File menu
        new_action = QAction("New File", self)
        new_action.setFont(font)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_action)

        open_action = QAction("Open File", self)
        open_action.setFont(font)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save File", self)
        save_action.setFont(font)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        find_action = QAction("Find", self)
        find_action.setFont(font)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(find_action)

        replace_action = QAction("Replace", self)
        replace_action.setFont(font)
        replace_action.setShortcut(QKeySequence.Replace)
        replace_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(replace_action)

        toggle_explorer_action = QAction("Toggle Explorer", self)
        toggle_explorer_action.setFont(font)
        toggle_explorer_action.setShortcut("Ctrl+Shift+E")
        toggle_explorer_action.triggered.connect(self.toggle_file_explorer)
        view_menu.addAction(toggle_explorer_action)

        run_action = QAction("Run", self)
        run_action.setShortcut("Ctrl+R")
        run_action.setFont(font)
        run_action.triggered.connect(self.run_current_code)
        run_menu.addAction(run_action)

    def setup_shortcuts(self):
        self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_shortcut.activated.connect(self.show_find_replace)
        
        self.replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.replace_shortcut.activated.connect(self.show_find_replace)
        
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.hide_find_replace)
        
        self.toggle_explorer_shortcut = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        self.toggle_explorer_shortcut.activated.connect(self.toggle_file_explorer)

    def toggle_file_explorer(self):
        if self.file_explorer.isVisible():
            self.file_explorer.hide()
        else:
            self.file_explorer.show()

    def show_find_replace(self):
        current_editor = self.tabs.currentWidget()
        if current_editor and hasattr(current_editor, 'toPlainText'):
            self.find_replace_widget.show_for_editor(current_editor)

    def hide_find_replace(self):
        self.find_replace_widget.hide()

    def new_tab(self):
        self.tabs.new_tab()

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        reply = QMessageBox.question(
            self, "Close Tab", "Are you sure you want to close this tab? Unsaved work will be lost.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.tabs.removeTab(index)
            if editor in self.file_paths:
                del self.file_paths[editor]

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Python Files (*.py)")
        if path:
            self.open_file_by_path(path)

    def open_file_by_path(self, path):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if editor and self.file_paths.get(editor) == path:
                self.tabs.setCurrentIndex(i)
                return

        if self.tabs.count() == 2 and self.tabs.tabText(0) == "*untitled":
            editor = self.tabs.widget(0)
            if not editor.toPlainText().strip(): 
                with open(path, "r") as file:
                    code = file.read()
                editor.setPlainText(code)
                self.tabs.setTabText(0, os.path.basename(path))
                self.file_paths[editor] = path
                return

        with open(path, "r") as file:
            code = file.read()
        editor = CodeEditor()
        font = QFont("Consolas", 14)
        editor.setFont(font)
        editor.setPlainText(code)
        index = self.tabs.add_editor_tab(editor, os.path.basename(path))
        self.file_paths[editor] = path

    def save_file(self):
        editor = self.tabs.currentWidget()
        if editor:
            current_path = self.file_paths.get(editor)
            if not current_path:
                path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Python Files (*.py)")
                if not path:
                    return
                self.file_paths[editor] = path
                index = self.tabs.indexOf(editor)
                self.tabs.setTabText(index, os.path.basename(path))
            else:
                path = current_path

            with open(path, "w") as file:
                file.write(editor.toPlainText())

    def append_terminal_output(self, text, color=QColor("#0f0")):
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self.terminal.moveCursor(QTextCursor.End)
        self.terminal.setCurrentCharFormat(fmt)
        self.terminal.insertPlainText(text + "\n")
        self.terminal.moveCursor(QTextCursor.End)

    def run_current_code(self):
        editor = self.tabs.currentWidget()
        if editor:
            self.terminal.clear()
            QApplication.processEvents()

            code = editor.toPlainText()
            result = run_code(code)

            file_path = self.file_paths.get(editor)
            display_name = file_path if file_path else self.tabs.tabText(self.tabs.currentIndex())
            self.append_terminal_output(f"Running file: {display_name}", QColor("cyan"))

            if any(err in result.lower() for err in ["error", "traceback", "exception"]):
                self.append_terminal_output(result, QColor("red"))
            else:
                self.append_terminal_output(result, QColor("#0f0"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PythonIDE()
    window.show()
    sys.exit(app.exec_())