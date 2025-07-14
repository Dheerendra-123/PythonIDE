import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileDialog, QAction,
    QTabWidget, QTextEdit, QSplitter, QVBoxLayout, QWidget,
    QMessageBox, QTabBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QFont,QTextCharFormat, QTextCursor, QColor
from editor import CodeEditor
from runner import run_code

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
        self.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.splitter = QSplitter(Qt.Vertical)
        self.file_paths = {}
        self.tabs = CustomTabWidget(self)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #111; color: #0f0; font-family: Consolas;")
        font = QFont("Consolas", 14)
        self.terminal.setFont(font)

        self.splitter.addWidget(self.tabs)
        self.splitter.addWidget(self.terminal)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)
        self.setCentralWidget(central_widget)

        self.create_menu()
        self.new_tab()

    def create_menu(self):
        menu = self.menuBar()
        font=QFont("Arial",10)
        file_menu = menu.addMenu("File")
        menu.setFont(font)
        run_menu = menu.addMenu("Run")

        new_action = QAction("New File", self)
        new_action.setFont(font)
        new_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_action)

        open_action = QAction("Open File", self)
        open_action.setFont(font)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save File", self)
        save_action.setFont(font)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        run_action = QAction("Run", self)
        run_action.setShortcut("Ctrl+R")
        run_action.setFont(font)
        run_action.triggered.connect(self.run_current_code)
        run_menu.addAction(run_action)

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
            if self.tabs.count() == 2 and self.tabs.tabText(0) == "*untitled":
                editor = self.tabs.widget(0)
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

            # Show file path like VS Code, fallback to tab name
            file_path = self.file_paths.get(editor)
            display_name = file_path if file_path else self.tabs.tabText(self.tabs.currentIndex())
            self.append_terminal_output(f"Running file: {display_name}", QColor("cyan"))

            # Display result
            if any(err in result.lower() for err in ["error", "traceback", "exception"]):
                self.append_terminal_output(result, QColor("red"))
            else:
                self.append_terminal_output(result, QColor("#0f0"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PythonIDE()
    window.show()
    sys.exit(app.exec_())



