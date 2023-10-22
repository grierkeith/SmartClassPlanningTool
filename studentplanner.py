import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QLineEdit
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from parser_logic import Parser
import sqlite3


class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.setGeometry(1200, 500, 1200, 500)
        self.setWindowTitle("Student Planner")
        self.setToolTip("Student Planner")
        self.setWindowIcon(QIcon("Images/CSU.png"))
        self.background_pixmap = QPixmap("Images/CSU Logo.png")

        self.interface()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(0.6)
        scaled_pixmap = self.background_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled_pixmap.width()) / 2
        y = (self.height() - scaled_pixmap.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled_pixmap)
        super(Main, self).paintEvent(event)

    def interface(self):
        self.lbl_name = QtWidgets.QLabel("Name:", self)
        self.lbl_name.move(100, 40)

        self.txt_name = QLineEdit(self)
        self.txt_name.move(250, 40)
        self.txt_name.setFixedWidth(350)

        self.lbl_id = QtWidgets.QLabel("CSU ID:", self)
        self.lbl_id.move(100, 70)

        self.txt_id = QLineEdit(self)
        self.txt_id.move(250, 70)
        self.txt_id.setFixedWidth(350)

        self.lbl_year = QtWidgets.QLabel("Year:", self)
        self.lbl_year.move(100, 100)

        self.txt_year = QLineEdit(self)
        self.txt_year.move(250, 100)
        self.txt_year.setFixedWidth(350)

        self.lbl_one = QtWidgets.QLabel("Select the Student's DegreeWorks file:", self)
        self.lbl_one.setFixedWidth(500)
        self.lbl_one.move(100, 140)

        self.btn_one = QPushButton("Attach file", self)
        self.btn_one.move(500, 140)
        self.btn_one.clicked.connect(self.attach_file_one)

        self.file_path_display_one = QLabel(self)
        self.file_path_display_one.setFixedWidth(500)
        self.file_path_display_one.move(600, 140)

        self.lbl_two = QtWidgets.QLabel("Select the Program Map Diagram file:", self)
        self.lbl_two.setFixedWidth(500)
        self.lbl_two.move(100, 190)

        self.btn_two = QPushButton("Attach file", self)
        self.btn_two.move(500, 190)
        self.btn_two.clicked.connect(self.attach_file_two)

        self.file_path_display_two = QLabel(self)
        self.file_path_display_two.setFixedWidth(500)
        self.file_path_display_two.move(600, 190)

        self.btn_run = QPushButton("Run", self)
        self.btn_run.move(100, 290)
        self.btn_run.clicked.connect(self.run_program)

        self.btn_exit = QPushButton("Exit", self)
        self.btn_exit.move(220, 290)
        self.btn_exit.clicked.connect(self.exit_program)

    def save_to_db(self, name, csu_id, year):
        conn = sqlite3.connect('courses.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS INITIAL_DATA (
                Name TEXT NOT NULL,
                CSU_ID TEXT NOT NULL,
                Year TEXT NOT NULL
            )
            ''')

        cursor.execute('DELETE FROM INITIAL_DATA')
        cursor.execute('INSERT INTO INITIAL_DATA (Name, CSU_ID, Year) VALUES (?, ?, ?)', (name, csu_id, year))
        conn.commit()
        conn.close()

    def attach_file_one(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getOpenFileName(self, "Open DegreeWorks file", "",
                                                  "All Files (*);;Text Files (*.txt)", options=options)
        if filepath:
            print(f"Selected file: {filepath}")
            self.file_path_display_one.setText(filepath)

    def attach_file_two(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Program Map Diagram file", "",
                                                  "All Files (*);;Image Files (*.png;*.jpg)", options=options)
        if filepath:
            print(f"Selected file: {filepath}")
            self.file_path_display_two.setText(filepath)

    def run_program(self):
        self.parser_window = Parser(
            self.file_path_display_one.text(),
            self.file_path_display_two.text(),
            self.txt_name.text(),
            self.txt_id.text(),
            self.txt_year.text()
        )
        self.save_to_db(self.txt_name.text(), self.txt_id.text(), self.txt_year.text())
        self.parser_window.show()

    def exit_program(self):
        self.close()


def window():
    app = QApplication(sys.argv)
    win = Main()
    win.show()
    sys.exit(app.exec_())


window()
