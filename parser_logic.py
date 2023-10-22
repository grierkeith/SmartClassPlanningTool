import re
import os
import sqlite3
from PIL import Image
import cv2
import pytesseract
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit, QPushButton
from pdfminer.high_level import extract_text
import numpy as np
from pdf2image import convert_from_path
from bs4 import BeautifulSoup
import requests
import sys


class Parser(QMainWindow):

    def __init__(self, degree_file, diagram_file, student_name, student_id, starting_year, parent=None):
        super(Parser, self).__init__(parent)
        print("Initializing Parser class...")

        print("Setting degree file...")
        self.degree_file = degree_file
        print(f"Degree file set to: {self.degree_file}")

        print("Setting diagram file...")
        self.diagram_file = diagram_file
        print(f"Diagram file set to: {self.diagram_file}")

        print("Setting student details...")
        self.student_name = student_name
        self.student_id = student_id
        self.starting_year = starting_year
        print(f"Student name set to: {self.student_name}")
        print(f"Student ID set to: {self.student_id}")
        print(f"Starting year set to: {self.starting_year}")

        print("Initializing program map data...")
        self.program_map_data = []

        print("Initializing courses needed...")
        self.courses_needed = []

        print("Initializing course relations...")
        self.course_relations = {}

        print("Setting Image.MAX_IMAGE_PIXELS...")
        Image.MAX_IMAGE_PIXELS = None

        print("Getting desktop path...")
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        print(f"Desktop path set to: {self.desktop_path}")

        print("Calling init_ui method...")
        self.init_ui()
        print("Initialization of Parser class completed.")

    def parse_pdf(self, filepath):
        print(f"Parsing PDF file at: {filepath}")
        return extract_text(filepath)

    def extract_courses(self, text):
        print("Extracting courses...")
        courses_needed_start = text.find("Still needed:")
        courses_needed_end = text.find("Another Section Name", courses_needed_start)
        courses_needed_text = text[courses_needed_start + len("Still needed:"): courses_needed_end]

        explicit_matches = re.findall(r'in ([A-Z]+)\s(\d{4}[A-Z]?)', courses_needed_text)
        for prefix, course in explicit_matches:
            self.courses_needed.append(f"{prefix} {course}")

        compound_matches = re.findall(r'in ([A-Z]+)\s(\d{4}[A-Z]?)[*]\sor\s(\d{4}[A-Z]?)[*]', courses_needed_text)
        for prefix, first_course, second_course in compound_matches:
            self.courses_needed.append(f"{prefix} {first_course}")
            self.courses_needed.append(f"{prefix} {second_course}")

        wildcard_matches = re.findall(r'([A-Z]+)?\s*(\d)@', courses_needed_text)
        last_prefix = None
        for prefix, num in wildcard_matches:
            if prefix:
                last_prefix = prefix
            if last_prefix:
                course = f"{last_prefix} {num}XXX"
                self.courses_needed.append(course)

        additional_matches = re.findall(r'([A-Z]+) (\d{4}[A-Z]?)[*]', courses_needed_text)
        for prefix, course_code in additional_matches:
            self.courses_needed.append(f"{prefix} {course_code}")

        self.write_to_db()

    def write_to_db(self):
        print("Writing to database...")
        conn = sqlite3.connect('courses.db')
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS COURSES_NEEDED')

        cursor.execute('''CREATE TABLE IF NOT EXISTS COURSES_NEEDED
                              (id INTEGER PRIMARY KEY, course TEXT UNIQUE)''')

        for course in self.courses_needed:
            cursor.execute("INSERT OR IGNORE INTO COURSES_NEEDED (course) VALUES (?)", (course,))

        conn.commit()
        conn.close()

    @staticmethod
    def get_images_from_pdf(file_path):
        print(f"Getting images from PDF file at: {file_path}")
        poppler_path = r"C:\Program Files\poppler-23.08.0\Library\bin"
        return convert_from_path(file_path, dpi=1000, poppler_path=poppler_path)

    def extract_course_relations(self):
        print("Extracting course relations...")
        images = self.get_images_from_pdf(self.diagram_file)

        if not images:
            print("No images extracted from the PDF.")
            return

        relations_str = []

        semester_pattern = re.compile(r"(Fa|Sp|Su|--)\s*(Fa|Sp|Su|--)?\s*(Fa|Sp|Su|--)?")

        pil_img = images[0]
        img = np.array(pil_img)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kernel = np.ones((1, 1), np.uint8)
        denoised = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        denoised = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel)

        coords = np.column_stack(np.where(denoised > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        text = pytesseract.image_to_string(deskewed)
        course_pattern = re.compile(r"([A-Z]+\s\d{4}[K+]?)(?:\n([\w\s-]+)\n)?")
        blocks = re.split(r'\n{2,}', text)

        combined_data = []
        for block in blocks:
            found_courses = course_pattern.findall(block)
            found_semesters = semester_pattern.findall(block)
            if found_courses and found_semesters:
                combined_data.append((found_courses[0], found_semesters[0]))

        valid_prefixes = ["MATH", "CPSC", "CYBR"]
        course_data_mapping = {}

        for (course_code, course_name), semesters in combined_data:
            if any(prefix in course_code for prefix in valid_prefixes):
                if len(course_name) > 2 or not course_name:
                    course_data_mapping[course_code] = {
                        'name': course_name,
                        'semesters': [sem for sem in semesters if sem != '--'],
                        'prerequisites': []
                    }

        prerequisites_mapping = {
            "CPSC 2108": ["CPSC 1302"],
            "CPSC 3175": ["CPSC 2108"],
            "CPSC 3125": ["CPSC 2108", "CPSC 2105"],
            "CPSC 3131": ["CPSC 1302"],
            "CPSC 3155": ["CPSC 2105"],
            "CPSC 3176": ["CPSC 3125", "CPSC 3131"],
            "CPSC 3157": ["CPSC 3125", "CPSC 3131"],
            "CPSC 4175": ["CPSC 3175"],
            "CPSC 4115": ["CPSC 3125"],
            "CPSC 5128": ["CPSC 5115"],
            "MATH 2125": ["MATH 1113"],
            "MATH 5125": ["MATH 2125"],
            "CPSC 5115": ["MATH 5125", "CPSC 2108"],
            "CPSC 5135": ["CPSC 3175"],
            "CPSC 4176": ["CPSC 4176"],
            "CPSC 5157": ["CPSC 2108", "CYBR 2159"],
            "CPSC 1302": ["CPSC 1301K"],
            "CYBR 2106": ["CPSC 1301K"],
            "CPSC 2105": ["CPSC 1301K"],
            "CPSC 3121": ["CPSC 2105"],
            "CPSC 5155": ["CPSC 3121"]

        }

        for course, prerequisites in prerequisites_mapping.items():
            formatted_course = course.replace(" ", "").upper()
            if formatted_course in course_data_mapping:
                course_data_mapping[formatted_course]['prerequisites'] = prerequisites

        for course, details in course_data_mapping.items():
            correct_prerequisites = prerequisites_mapping.get(course, [])
            if set(details['prerequisites']) != set(correct_prerequisites):
                details['prerequisites'] = correct_prerequisites

        for course_code, course_details in course_data_mapping.items():
            course_info = (f"{course_code}\n"
                           f"Prerequisites: {', '.join(course_details['prerequisites']) if course_details['prerequisites'] else 'None'}\n"
                           f"Semesters: {' '.join(course_details['semesters'])}\n"
                           f"-------------------------")
            relations_str.append(course_info)

        self.course_relations = '\n'.join(relations_str)
        return self.course_relations

    @staticmethod
    def scrape_cs_courses(url):
        print(f"Scraping CS courses from URL: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to retrieve the webpage.")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        data = []
        year = None
        term = None
        for row in soup.find_all('tr'):

            if 'plangridyear' in row['class']:
                year = row.th.text.strip()

            elif 'plangridterm' in row['class']:
                term = row.th.text.strip()

            elif 'even' in row['class'] or 'odd' in row['class']:
                code_col = row.find('td', class_='codecol')
                title_col = row.find('td', class_='titlecol')
                hours_col = row.find('td', class_='hourscol')

                if code_col and title_col and hours_col:
                    code_cleaned = code_col.text.replace('\xa0', ' ').strip().replace("or", " or")
                    title_cleaned = title_col.text.replace('\xa0', ' ').strip().replace("or", " or")
                    data.append((year, term, code_cleaned, title_cleaned, hours_col.text.strip()))

        return data

    def extract_program_map_data(self):
        print("Extracting program map data...")
        url = "https://catalog.columbusstate.edu/academic-units/business/computer-science/computer-science-bs-software-systems-track/#programmaptext"
        courses = self.scrape_cs_courses(url)
        data = "\n".join([str(course) for course in courses])
        return data

    def on_next_clicked(self):
        print("Next button clicked...")
        self.extract_course_relations()
        self.course_relations_text.setPlainText(self.course_relations)
        self.next_button.setDisabled(True)
        self.program_map_button.setEnabled(True)

    def on_program_map_button_clicked(self):
        print("Program map button clicked...")
        data = self.extract_program_map_data()
        self.program_map_data_text.setPlainText(data)
        self.program_map_button.setDisabled(True)
        self.check_all_buttons_clicked()

    def check_all_buttons_clicked(self):
        if not self.program_map_button.isEnabled() and not self.next_button.isEnabled():
            self.create_academic_plan_button.setEnabled(True)

    def on_create_academic_plan_clicked(self):
        print("Creating academic plan...")
        from data import coursesNeeded
        from helper import createSuggestedProgram, SuggestedProgram, exportSuggestedProgramToExcelFile

        program = SuggestedProgram()
        program.setRemainingCourses(coursesNeeded)

        result = createSuggestedProgram(program)
        exportSuggestedProgramToExcelFile(result)

        os.system("start Output.xlsx")

        sys.exit(0)

    def init_ui(self):
        print("Initializing UI...")
        self.setWindowTitle("Compile Data")
        self.setGeometry(500, 300, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        lbl_student_name = QLabel(f"Student Name: {self.student_name}")
        layout.addWidget(lbl_student_name)

        lbl_student_id = QLabel(f"CSU ID: {self.student_id}")
        layout.addWidget(lbl_student_id)

        lbl_starting_year = QLabel(f"Starting Year: {self.starting_year}")
        layout.addWidget(lbl_starting_year)

        lbl_degree_file = QLabel(f"DegreeWorks File: {self.degree_file}")
        layout.addWidget(lbl_degree_file)

        pdf_text = self.parse_pdf(self.degree_file)
        self.extract_courses(pdf_text)

        courses_needed_label = QLabel("Courses Needed:")
        layout.addWidget(courses_needed_label)

        formatted_courses = ', '.join([f'"{course}"' for course in self.courses_needed])
        courses_needed_text = QTextEdit(f"[ {formatted_courses} ]")
        layout.addWidget(courses_needed_text)

        next_button = QPushButton("Get Prerequisites")
        next_button.clicked.connect(self.on_next_clicked)
        layout.addWidget(next_button)
        self.next_button = next_button

        lbl_diagram_file = QLabel(f"Program Map Diagram File: {self.diagram_file}")
        layout.addWidget(lbl_diagram_file)

        course_relations_label = QLabel("Course Prerequisites:")
        layout.addWidget(course_relations_label)

        self.course_relations_text = QTextEdit()
        layout.addWidget(self.course_relations_text)

        program_map_button = QPushButton("Get Online Program Map")
        program_map_button.clicked.connect(self.on_program_map_button_clicked)
        layout.addWidget(program_map_button)
        self.program_map_button = program_map_button

        program_map_data_lbl = QLabel('Program Map Data:')
        layout.addWidget(program_map_data_lbl)

        self.program_map_data_text = QTextEdit(self)
        layout.addWidget(self.program_map_data_text)

        self.create_academic_plan_button = QPushButton("Create Academic Plan")
        self.create_academic_plan_button.setDisabled(True)
        self.create_academic_plan_button.clicked.connect(self.on_create_academic_plan_clicked)
        layout.addWidget(self.create_academic_plan_button)

        central_widget.setLayout(layout)

        self.program_map_button.clicked.connect(self.check_all_buttons_clicked)
        self.next_button.clicked.connect(self.check_all_buttons_clicked)
