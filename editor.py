from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt5.QtGui import QTextCursor, QTextFormat, QColor, QPainter, QFont
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from highlighter import PythonHighlighter

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    textChangedSignal = pyqtSignal()
    cursorPositionChangedSignal = pyqtSignal(int, int)  # line, column
    
    def __init__(self):
        super().__init__()
        self.highlighter = PythonHighlighter(self.document())
        self.line_number_area = LineNumberArea(self)
        self.setTabStopDistance(40)  
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        font = QFont("Consolas", 12)
        if not font.exactMatch():
            font = QFont("Courier New", 12)
        font.setFixedPitch(True)
        self.setFont(font)
        
        self.brackets = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        self.bracket_colors = {
            '()': QColor(255, 215, 0),    # Gold
            '[]': QColor(135, 206, 235),  # Sky blue
            '{}': QColor(255, 105, 180),  # Hot pink
        }
        
        self.auto_complete_enabled = True
        self.completion_words = [
            'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except',
            'finally', 'with', 'import', 'from', 'return', 'yield', 'lambda',
            'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None', 'pass',
            'break', 'continue', 'global', 'nonlocal', 'assert', 'del', 'raise'
        ]
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.emit_cursor_position)
        self.textChanged.connect(self.on_text_changed)
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        self.setUndoRedoEnabled(True)
        
    def emit_cursor_position(self):
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursorPositionChangedSignal.emit(line, column)
        
    def on_text_changed(self):
        self.textChangedSignal.emit()
        
    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
        
    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
            
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        
    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(255,255,255))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        height = self.fontMetrics().height()
        
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(block_number + 1)
                painter.setPen(QColor(150, 150, 150))
                painter.drawText(0, int(top), self.line_number_area.width(), height, Qt.AlignRight, number)
                
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
            
    def highlight_current_line(self):
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(255,255,255)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        extra_selections.extend(self.match_brackets())
        
        self.setExtraSelections(extra_selections)
        
    def match_brackets(self):
        selections = []
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()
        
        if pos > 0 and pos <= len(text):
            char_before = text[pos - 1] if pos > 0 else ''
            char_at = text[pos] if pos < len(text) else ''
            
            bracket_pair = None
            start_pos = None
            if char_before in self.brackets:
                bracket_pair = char_before + self.brackets[char_before]
                start_pos = pos - 1
                match_pos = self.find_matching_bracket(text, start_pos, bracket_pair[0], bracket_pair[1], True)
            elif char_at in self.brackets.values():
                for open_br, close_br in self.brackets.items():
                    if char_at == close_br:
                        bracket_pair = open_br + close_br
                        start_pos = pos
                        match_pos = self.find_matching_bracket(text, start_pos, open_br, close_br, False)
                        break
                        
            if bracket_pair and start_pos is not None:
                color = self.bracket_colors.get(bracket_pair, QColor(255, 255, 255))
                
                selection1 = QTextEdit.ExtraSelection()
                selection1.format.setBackground(color)
                selection1.cursor = self.textCursor()
                selection1.cursor.setPosition(start_pos)
                selection1.cursor.setPosition(start_pos + 1, QTextCursor.KeepAnchor)
                selections.append(selection1)
                
                if match_pos != -1:
                    selection2 = QTextEdit.ExtraSelection()
                    selection2.format.setBackground(color)
                    selection2.cursor = self.textCursor()
                    selection2.cursor.setPosition(match_pos)
                    selection2.cursor.setPosition(match_pos + 1, QTextCursor.KeepAnchor)
                    selections.append(selection2)
                    
        return selections
        
    def find_matching_bracket(self, text, start_pos, open_char, close_char, forward):
        count = 1
        pos = start_pos + 1 if forward else start_pos - 1
        
        while 0 <= pos < len(text):
            if text[pos] == open_char:
                count += 1 if forward else -1
            elif text[pos] == close_char:
                count -= 1 if forward else -1
                
            if count == 0:
                return pos
                
            pos += 1 if forward else -1
            
        return -1
        
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.select(QTextCursor.LineUnderCursor)
            line = cursor.selectedText()
            indent = len(line) - len(line.lstrip(' '))
            
            stripped_line = line.strip()
            if stripped_line.endswith(":"):
                indent += 4
            elif stripped_line.endswith('\\'):
                indent += 4
            elif self.is_continuation_line(line):
                indent += 4
                
            super().keyPressEvent(event)
            self.insertPlainText(" " * indent)
            return
            
        elif event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self.indent_selection()
            else:
                self.insertPlainText("    ")  
            return
            
        elif event.key() == Qt.Key_Backtab:
            self.unindent_selection()
            return

        elif event.key() == Qt.Key_Slash and event.modifiers() == Qt.ControlModifier:
            self.toggle_comment()
            return
            
        elif event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            self.duplicate_line()
            return

        elif event.key() == Qt.Key_K and event.modifiers() == Qt.ControlModifier:
            self.delete_line()
            return

        elif event.key() == Qt.Key_Backspace:
            if self.smart_backspace():
                return
                
        elif event.text() in self.brackets and self.auto_complete_enabled:
            self.auto_complete_bracket(event.text())
            return
            
        elif event.text() in self.brackets.values() and self.auto_complete_enabled:
            if self.skip_closing_bracket(event.text()):
                return
                
        super().keyPressEvent(event)
        
    def is_continuation_line(self, line):
        """Check if this is a continuation of a multi-line statement"""
        stripped = line.strip()
        return (stripped.endswith(',') or 
                stripped.endswith('(') or 
                stripped.endswith('[') or 
                stripped.endswith('{') or
                '(' in stripped and ')' not in stripped)
                
    def smart_backspace(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
            
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText()
        
        pos = self.textCursor().columnNumber()
        if pos > 0 and line[:pos].strip() == '':
            spaces_to_remove = min(4, pos)
            cursor = self.textCursor()
            for _ in range(spaces_to_remove):
                cursor.deletePreviousChar()
            return True
            
        return False
        
    def indent_selection(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfBlock)
        
        while cursor.position() <= end:
            cursor.insertText("    ")
            end += 4
            if not cursor.movePosition(QTextCursor.NextBlock):
                break
                
    def unindent_selection(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfBlock)
        
        while cursor.position() <= end:
            cursor.select(QTextCursor.LineUnderCursor)
            line = cursor.selectedText()
            
            if line.startswith("    "):
                cursor.insertText(line[4:])
                end -= 4
            elif line.startswith("\t"):
                cursor.insertText(line[1:])
                end -= 1
                
            if not cursor.movePosition(QTextCursor.NextBlock):
                break
                
    def toggle_comment(self):
        cursor = self.textCursor()
        
        if cursor.hasSelection():
            self.toggle_comment_selection()
        else:
            self.toggle_comment_line()
            
    def toggle_comment_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText()
        
        if line.lstrip().startswith("#"):
            new_line = line.replace("#", "", 1).replace(" ", "", 1) if line.lstrip().startswith("# ") else line.replace("#", "", 1)
            cursor.insertText(new_line)
        else:
            indent = len(line) - len(line.lstrip())
            new_line = line[:indent] + "# " + line[indent:]
            cursor.insertText(new_line)
            
    def toggle_comment_selection(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfBlock)
        all_commented = True
        temp_cursor = QTextCursor(cursor)
        
        while temp_cursor.position() <= end:
            temp_cursor.select(QTextCursor.LineUnderCursor)
            line = temp_cursor.selectedText()
            if line.strip() and not line.lstrip().startswith("#"):
                all_commented = False
                break
            if not temp_cursor.movePosition(QTextCursor.NextBlock):
                break
                
        while cursor.position() <= end:
            cursor.select(QTextCursor.LineUnderCursor)
            line = cursor.selectedText()
            
            if all_commented and line.lstrip().startswith("#"):
                new_line = line.replace("#", "", 1).replace(" ", "", 1) if line.lstrip().startswith("# ") else line.replace("#", "", 1)
                cursor.insertText(new_line)
            elif not all_commented and line.strip():
                indent = len(line) - len(line.lstrip())
                new_line = line[:indent] + "# " + line[indent:]
                cursor.insertText(new_line)
                
            if not cursor.movePosition(QTextCursor.NextBlock):
                break
                
    def duplicate_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText()
        
        cursor.movePosition(QTextCursor.EndOfBlock)
        cursor.insertText("\n" + line)
        
    def delete_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar() 
        
    def auto_complete_bracket(self, opening_bracket):
        if opening_bracket in self.brackets:
            closing_bracket = self.brackets[opening_bracket]
            cursor = self.textCursor()
            cursor.insertText(opening_bracket + closing_bracket)
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            
    def skip_closing_bracket(self, closing_bracket):
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()
        
        if pos < len(text) and text[pos] == closing_bracket:
            cursor.movePosition(QTextCursor.Right)
            self.setTextCursor(cursor)
            return True
            
        return False
        
    def get_word_under_cursor(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()
        
    def go_to_line(self, line_number):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line_number - 1):
            cursor.movePosition(QTextCursor.Down)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        
    def set_font_size(self, size):
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        
    def zoom_in(self):
        font = self.font()
        size = font.pointSize()
        if size < 20:
            font.setPointSize(size + 1)
            self.setFont(font)
            
    def zoom_out(self):
        font = self.font()
        size = font.pointSize()
        if size > 8:
            font.setPointSize(size - 1)
            self.setFont(font)