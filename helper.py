import sqlite3
from data import courses, credits, semester, prerequisitesCourses
import pandas as pd
import xlsxwriter

FALL_MONTHS = ['August', 'September', 'October', 'November', 'December']
SPRING_MONTHS = ['January', 'February', 'March', 'April', 'May']
SUMMER_MONTHS = ['June', 'July']


def get_start_year():
    connection = sqlite3.connect("courses.db")
    cursor = connection.cursor()
    cursor.execute("SELECT YEAR FROM INITIAL_DATA")
    year = cursor.fetchone()[0]
    connection.close()
    return year


def next_semester(semester, year):
    if semester == "Fall":
        return "Spring", year + 1
    elif semester == "Spring":
        return "Summer", year
    elif semester == "Summer":
        return "Fall", year


def sortCourses(lst):
    def sortKey(item):
        if item == 'CPSC 4000':
            return ('Z', '99999')
        firstChar = item[0]
        numberPart = item[1:10]
        return (firstChar, numberPart)

    return sorted(lst, key=sortKey)


def equalToList(lst, value1, value2):
    if len(lst) == 0:
        return False
    if lst[0] == value1 and lst[1] == value2:
        return True
    else:
        return False


def getOneRootPrerequisite(c, remainingCourses):
    res = c
    prerequisites = prerequisitesCourses.get(c)
    # base case: no prerequisites: return res
    if prerequisites is None:
        return res
    for p in prerequisites:
        while p in remainingCourses:
            return getOneRootPrerequisite(p, remainingCourses)
    return res


def programWithDetails(lst):
    res = []
    for i in range(len(lst)):
        res.append([])

        for j in lst[i]:
            course = courses[j]
            res[i].append({
                "name": j + " - " + course["title"],
                "credits": course["credits"],
            })

    return res


class SuggestedProgram:
    def __init__(self):
        self.program = []
        self.coursesInCurrentSemester = []
        self.totalCreditsIncurrentSemester = 0
        # self.currentSemester = "Fa"
        self.currentSemester = 8

        self.maxCreditsForCurrentSemester = 15
        self.remainingCourses = []

    def setRemainingCourses(self, remainingCourses):
        self.remainingCourses = remainingCourses

    def updateCurrentSemester(self):
        if len(self.program) % 3 == 0:
            # self.currentSemester = "Fa"
            self.currentSemester = 8
            self.maxCreditsForCurrentSemester = 15
        elif len(self.program) % 3 == 1:
            self.currentSemester = 2
            self.maxCreditsForCurrentSemester = 15
        else:
            self.currentSemester = 5
            self.maxCreditsForCurrentSemester = 6

    def createNewSemester(self):
        self.program.append(self.coursesInCurrentSemester)
        self.coursesInCurrentSemester = []
        self.totalCreditsIncurrentSemester = 0
        self.updateCurrentSemester()

    def addCourseToCurrentSemester(self, c):
        result = None
        if self.totalCreditsIncurrentSemester + credits[
            c] <= self.maxCreditsForCurrentSemester and self.currentSemester in semester[c]:
            self.coursesInCurrentSemester.append(c)
            self.totalCreditsIncurrentSemester += credits[c]
            self.remainingCourses.remove(c)
            result = True
        else:
            result = False
        if self.totalCreditsIncurrentSemester >= self.maxCreditsForCurrentSemester:
            self.createNewSemester()
        return result

    def addCourseToLastSemester(self, c):
        if len(self.program) == 0:
            self.program.append([c])
        else:
            self.program[-1].append(c)

    def addCourseToAvailableSemester(self, c):
        available_semesters = semester[c]
        for sem in available_semesters:
            if self.totalCreditsIncurrentSemester + credits[
                c] <= self.maxCreditsForCurrentSemester and sem == self.currentSemester:
                self.coursesInCurrentSemester.append(c)
                self.totalCreditsIncurrentSemester += credits[c]
                self.remainingCourses.remove(c)
                if self.totalCreditsIncurrentSemester >= self.maxCreditsForCurrentSemester:
                    self.createNewSemester()
                return True
        return False


def createSuggestedProgram(suggestedProgram):
    courses = sortCourses(suggestedProgram.remainingCourses[:])
    theFirstCourseSkipped = []

    schedule_CPSC_4000_last = 'CPSC 4000' in suggestedProgram.remainingCourses
    if schedule_CPSC_4000_last:
        suggestedProgram.remainingCourses.remove('CPSC 4000')

    while len(suggestedProgram.remainingCourses) > 0:
        for c in courses:
            if c not in suggestedProgram.remainingCourses:
                continue

            r = getOneRootPrerequisite(c, suggestedProgram.remainingCourses)

            if r not in suggestedProgram.coursesInCurrentSemester:
                res = suggestedProgram.addCourseToAvailableSemester(r)
                if res:
                    if equalToList(theFirstCourseSkipped, c, r):
                        theFirstCourseSkipped = []
                    continue

                if len(theFirstCourseSkipped) == 0:
                    theFirstCourseSkipped.extend([c, r])
                elif equalToList(theFirstCourseSkipped, c, r):
                    suggestedProgram.createNewSemester()
                    theFirstCourseSkipped = []

        courses = suggestedProgram.remainingCourses[:]

    # Schedule CPSC 4000 in the last semester if required
    if schedule_CPSC_4000_last:
        if len(suggestedProgram.coursesInCurrentSemester) > 0:
            suggestedProgram.program.append(suggestedProgram.coursesInCurrentSemester)
            suggestedProgram.coursesInCurrentSemester = []
        suggestedProgram.addCourseToLastSemester('CPSC 4000')

    if len(suggestedProgram.coursesInCurrentSemester) > 0:
        suggestedProgram.program.append(suggestedProgram.coursesInCurrentSemester)

    res = programWithDetails(suggestedProgram.program)
    return res


def exportSuggestedProgramToExcelFile(program):
    dfs = []
    START_YEAR = int(get_start_year())
    fa_year, sp_year, su_year = START_YEAR, START_YEAR + 1, START_YEAR + 1

    connection = sqlite3.connect("courses.db")
    cursor = connection.cursor()
    cursor.execute("SELECT Name, CSU_ID FROM INITIAL_DATA")
    name, csu_id = cursor.fetchone()
    connection.close()

    while len(program) < 9:
        program.append([{"name": "", "credits": ""} for _ in range(7)])

    for i, d in enumerate(program):
        while len(d) < 7:
            d.append({"name": "", "credits": ""})

        d.append({"name": "Total:", "credits": ""})
        df = pd.DataFrame(d)

        if i % 3 == 0:
            df = df.rename(columns={"name": "Fall " + str(fa_year)})
            fa_year += 1
        elif i % 3 == 1:
            df = df.rename(columns={"name": "Spring " + str(sp_year)})
            sp_year += 1
        else:
            df = df.rename(columns={"name": "Summer " + str(su_year)})
            su_year += 1
        dfs.append(df)

    with pd.ExcelWriter("Output.xlsx", engine="xlsxwriter") as writer:
        workbook = writer.book
        writer.sheets["Sheet1"] = workbook.add_worksheet("Sheet1")
        worksheet = writer.sheets["Sheet1"]
        worksheet.merge_range("A2:F2", "PATH TO GRADUATION", workbook.add_format({'font_size': 48}))
        worksheet.write("H2", "Software Systems Track Required Classes")
        worksheet.write("I2", "Credits")
        worksheet.write("B1", "Name:")
        worksheet.write("D1", "CSU ID:")
        worksheet.write("C1", name)
        worksheet.write("E1", csu_id)

        desired_width1 = 405 * 7 / 100
        desired_width2 = 725 * 7 / 100
        desired_width3 = 107 * 7 / 100
        worksheet.set_column('A:A', desired_width1)
        worksheet.set_column('C:C', desired_width1)
        worksheet.set_column('E:E', desired_width1)
        worksheet.set_column('H:H', desired_width2)
        worksheet.set_column('B:B', desired_width3)
        worksheet.set_column('D:D', desired_width3)
        worksheet.set_column('F:F', desired_width3)
        worksheet.set_column('I:I', desired_width3)

        fa_table_row_col = [2, 0]
        sp_table_row_col = [2, 2]
        su_table_row_col = [2, 4]

        for i, df in enumerate(dfs):
            if i % 3 == 0:
                df.to_excel(writer, startrow=fa_table_row_col[0], startcol=fa_table_row_col[1], sheet_name="Sheet1",
                            header=True, index=False)
                worksheet.write_formula(fa_table_row_col[0] + 8, fa_table_row_col[1] + 1,
                                        f"=SUM(B{fa_table_row_col[0] + 2}:B{fa_table_row_col[0] + 8})")
                fa_table_row_col[0] += 9
            elif i % 3 == 1:
                df.to_excel(writer, startrow=sp_table_row_col[0], startcol=sp_table_row_col[1], sheet_name="Sheet1",
                            header=True, index=False)
                worksheet.write_formula(sp_table_row_col[0] + 8, sp_table_row_col[1] + 1,
                                        f"=SUM(D{sp_table_row_col[0] + 2}:D{sp_table_row_col[0] + 8})")
                sp_table_row_col[0] += 9
            else:
                df.to_excel(writer, startrow=su_table_row_col[0], startcol=su_table_row_col[1], sheet_name="Sheet1",
                            header=True, index=False)
                worksheet.write_formula(su_table_row_col[0] + 8, su_table_row_col[1] + 1,
                                        f"=SUM(F{su_table_row_col[0] + 2}:F{su_table_row_col[0] + 8})")
                su_table_row_col[0] += 9

        # write program
        # error: remove 3 last courses PEDS,  CPSC3XXX1, CPSC3XXX2, should back them in
        # courses.pop('PEDS1399')
        # courses.pop('CPSC3XXX1')
        # courses.pop('CPSC3XXX2')

        courses_list = [{"name": key + " - " + value["title"],
                         "credits": value["credits"]} for key, value in courses.items()]

        df_courses = pd.DataFrame(courses_list)
        df_courses.to_excel(writer, startrow=2, startcol=7,
                            sheet_name=f"Sheet1", header=True, index=False)


def check_suggested_plan(courses_needed, plan):
    # check pre-requisite issue:
    print("----Check pre-requisite issue in plan-------")
    courses_needed = list(courses_needed)

    def get_course_code(name):
        code = name.split(" - ")[0]
        return code[:4] + code[5:]

    for semester in plan:
        for course in semester:
            code = get_course_code(course.get("name"))
            prerequisites = prerequisitesCourses.get(code)
            if prerequisites is None:
                continue
            else:
                for j in prerequisites:
                    if j in courses_needed:
                        print("There is issue with pre-requisite courses in plan")
                        return False
                    else:
                        courses_needed.remove(j)
    print("There is no pre-requisite issue in plan")
    return True
