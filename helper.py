from data import courses, credits, semester, prerequisitesCourses
import pandas as pd
import xlsxwriter


def sortCourses(lst):
    def sortKey(item):
        firstChar = item[0]
        numberPart = item[5:10]
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
                "name": j+" - "+course["title"],
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
        if self.totalCreditsIncurrentSemester + credits[c] <= self.maxCreditsForCurrentSemester and self.currentSemester in semester[c]:
            self.coursesInCurrentSemester.append(c)
            self.totalCreditsIncurrentSemester += credits[c]
            self.remainingCourses.remove(c)
            result = True
        else:
            result = False
        if self.totalCreditsIncurrentSemester >= self.maxCreditsForCurrentSemester:
            self.createNewSemester()
        return result


def createSuggestedProgram(suggestedProgram):
    courses = sorted(suggestedProgram.remainingCourses[:])
    theFirstCourseSkipped = []

    while len(suggestedProgram.remainingCourses) > 0:

        for c in courses:
            if c not in suggestedProgram.remainingCourses:
                continue
            r = getOneRootPrerequisite(c, suggestedProgram.remainingCourses)

            if r not in suggestedProgram.coursesInCurrentSemester:
                res = suggestedProgram.addCourseToCurrentSemester(r)
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

    if len(suggestedProgram.coursesInCurrentSemester) > 0:
        suggestedProgram.program.append(
            suggestedProgram.coursesInCurrentSemester)
    res = programWithDetails(suggestedProgram.program)
    return res


def exportSuggestedProgramToExcelFile(program):
    workbook = xlsxwriter.Workbook("output.xlsx")
    worksheet = workbook.add_worksheet()

    bold_format = workbook.add_format({
        'bold': True,
        'bg_color': '#CCEEFF',  # Light Blue
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#FFD700',  # Light Yellow
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    course_format = workbook.add_format({
        'bg_color': '#E6E6E6',  # Light Gray
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    })
    credits_format = workbook.add_format({
        'bg_color': '#A9D08E',  # Light Green
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    worksheet.set_column('A:A', 30)
    worksheet.set_column('B:B', 10)
    worksheet.set_column('C:C', 30)
    worksheet.set_column('D:D', 10)
    worksheet.set_column('G:G', 30)
    worksheet.set_column('H:H', 10)
    worksheet.set_column('I:I', 30)
    worksheet.set_column('J:J', 10)
    worksheet.set_column('L:L', 40)
    worksheet.set_column('M:M', 10)

    worksheet.write('A2', 'PATH TO GRADUATION', bold_format)
    worksheet.write('L2', 'Name', bold_format)
    worksheet.write('M2', 'Credits', bold_format)

    row = 2
    col = 0
    survey = {}
    for i, semester_data in enumerate(program):
        if i % 3 == 0:
            worksheet.write(row, col, f'Fall {2022 + (i // 3)}', header_format)
        elif i % 3 == 1:
            worksheet.write(row, col, f'Spring {2022 + (i // 3)}', header_format)

        for course in semester_data:
            if course['credits'] == 0:
                survey = course
                continue
            row += 1
            worksheet.write(row, col, course['name'], course_format)
            worksheet.write(row, col + 1, course['credits'], credits_format)

        col += 2
        row = 2

    courses_list = [{"name": key + " - " + value["title"], "credits": value["credits"]} for key, value in courses.items()]

    row = 3
    col = 11

    worksheet.write('L2', 'Software Systems Track Required Classes', bold_format)
    worksheet.write('M2', 'Credits', bold_format)
    worksheet.write('L3', 'Name', header_format)
    worksheet.write('M3', 'Credits', header_format)
    worksheet.write('B3', 'Credits', header_format)
    worksheet.write('D3', 'Credits', header_format)
    worksheet.write('H3', 'Credits', header_format)
    worksheet.write('J3', 'Credits', header_format)
    worksheet.write('I7', survey['name'], course_format)
    worksheet.write('J7', survey['credits'], credits_format)

    for course in courses_list:
        worksheet.write(row, col, course["name"], course_format)
        worksheet.write(row, col + 1, course["credits"], credits_format)
        row += 1

    workbook.close()