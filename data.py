from create_excel import fetch_table_data


def getCourses():
    courses_from_db = fetch_table_data('COURSE')[1]
    result = {}
    for row in courses_from_db:
        result[row[0]] = {}
        result[row[0]]['credits'] = row[1]
        result[row[0]]['title'] = row[2]
    return result


def getCredits():
    courses_from_db = fetch_table_data('COURSE')[1]
    result = {}
    for row in courses_from_db:
        result[row[0]] = row[1]
    return result


def getSemester():
    semester_from_db = fetch_table_data('COURSE_SEMESTER')[1]
    result = {}
    for row in semester_from_db:
        if row[0] in result:
            result[row[0]].append(row[2])
        else:
            result[row[0]] = [row[2]]
    return result


def getCoursesNeeded():
    courses_needed_from_db = fetch_table_data('COURSES_NEEDED')[1]
    result = [row[1] for row in courses_needed_from_db]
    return result


def getPrerequisites():
    courses_from_db = fetch_table_data('PRE_REQ')[1]
    result = {}
    for row in courses_from_db:
        if row[0] in result:
            result[row[0]].append(row[1])
        else:
            result[row[0]] = [row[1]]
    return result


semester = getSemester()
courses = getCourses()
prerequisitesCourses = getPrerequisites()
credits = getCredits()
coursesNeeded = ["CPSC 3165", "CPSC 4000", "CPSC 3121", "CPSC 3131", "CPSC 5115", "CPSC 5135", "CPSC 5128", "CPSC 5155", "CPSC 5157", "CPSC 4175", "CPSC 4176", "CPSC 3XXX1", "CPSC 3XXX2", "CYBR 2159", "CPSC 2108", "CPSC 1301K"]

# semester = {
#     "MATH 1113": ["Fa", "Sp", "Su"],
#     "MATH 2125": ["Fa", "Sp", "Su"],
#     "MATH 5125": ["Fa", "Sp", "Su"],
#     "CPSC 2108": ["Fa", "Sp", "Su"],
#     "CPSC 3175": ["Fa", "Sp"],
#     "CPSC 3125": ["Fa", "Sp"],
#     "CPSC 5135": ["Sp"],
#     "CPSC 5115": ["Fa"],
#     "CPSC 4175": ["Fa"],
#     "CPSC 5128": ["Sp"],
#     "CPSC 4176": ["Sp"],
#     "CPSC 4000": ["Fa", "Sp", "Su"],
#     "CPSC 5157": ["Fa", "Su"],
#     "CPSC 3165": ["Fa", "Sp", "Su"],
#     "CPSC 3131": ["Fa", "Sp"],
#     'CPSC 5155': ["Fa"],
#     "CPSC 3121": ["Sp"],
#     "CYBR 2106": ["Fa", "Sp"],
#     "CYBR 2159": ["Fa", "Sp"],
#     "CPSC 1302": ["Fa", "Sp"],
#     "CPSC 2105": ["Fa", "Sp", "Su"],
#     "CPSC 1301K": ["Fa", "Sp", "Su"],
#     "CPSC3XXX1": ["Fa", "Sp", "Su"],
#     "CPSC3XXX2": ["Fa", "Sp", "Su"],
# }


# prerequisitesCourses = {
#     "MATH2125": ["MATH1113"],
#     "MATH5125": ["MATH2125"],
#     "CPSC2108": ["MATH2125"],
#     "CPSC3175": ["CPSC2108"],
#     "CPSC3125": ["CPSC2108"],
#     "CPSC5135": ["CPSC3175"],
#     "CPSC5115": ["MATH5125", "CPSC2108"],
#     "CPSC4175": ["CPSC3175"],
#     "CPSC5128": ["CPSC5115"],
#     "CPSC4176": ["CPSC4175"],
#     "CPSC5157": ["CYBR2159", "CPSC2108"],
#     "CPSC3131": ["CPSC1302"],
#     "CPSC5155": ["CPSC3121"],
#     "CPSC3121": ["CPSC2105"],
#     "CYBR2106": ["CPSC1301K"],
#     "CYBR2159": ["CPSC1301K"],
#     "CPSC1302": ["CPSC1301K"],
#     "CPSC2105": ["CPSC1301K"],
# }
# credits = {"MATH 1113": 4,
#            "MATH 2125": 3,
#            "MATH 5125": 3,
#            "CPSC 2108": 3,
#            "CPSC 3175": 3,
#            "CPSC 3125": 3,
#            "CPSC 5135": 3,
#            "CPSC 5115": 3,
#            "CPSC 4175": 3,
#            "CPSC 5128": 3,
#            "CPSC 4176": 3,
#            "CPSC 4000": 0,
#            "CPSC 5157": 3,
#            "CPSC 3165": 3,
#            "CPSC 3131": 3,
#            "CPSC 5155": 3,
#            "CPSC 3121": 3,
#            "CYBR 2106": 3,
#            "CYBR 2159": 3,
#            "CPSC 1302": 3,
#            "CPSC 2105": 3,
#            "CPSC 1301K": 4,
#            "CPSC3XXX1": 3,
#            "CPSC3XXX2": 3}
