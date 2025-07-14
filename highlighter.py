from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.keywords = [
            'def', 'class', 'if', 'elif', 'else', 'while', 'for', 'import',
            'from', 'return', 'try', 'except', 'finally', 'with', 'as', 'pass',
            'break', 'continue', 'lambda', 'True', 'False', 'None', 'print'
        ]

    def highlightBlock(self, text):
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))
        keyword_format.setFontWeight(QFont.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("darkGreen"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("gray"))

        for keyword in self.keywords:
            pattern = rf'\b{keyword}\b'
            index = text.find(keyword)
            while index != -1:
                self.setFormat(index, len(keyword), keyword_format)
                index = text.find(keyword, index + len(keyword))

        for quote in ['"', "'"]:
            start = text.find(quote)
            end = text.find(quote, start + 1)
            if start != -1 and end != -1:
                self.setFormat(start, end - start + 1, string_format)

        comment_index = text.find("#")
        if comment_index != -1:
            self.setFormat(comment_index, len(text) - comment_index, comment_format)
