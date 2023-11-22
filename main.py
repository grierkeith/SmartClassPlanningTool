from data import coursesNeeded
from helper import createSuggestedProgram, SuggestedProgram, exportSuggestedProgramToExcelFile, check_suggested_plan

program = SuggestedProgram()
program.setRemainingCourses(coursesNeeded)

result = createSuggestedProgram(program)
is_passed_check = check_suggested_plan(coursesNeeded, result)

if is_passed_check:
    exportSuggestedProgramToExcelFile(result)
else:
    print("Return back to upload file page")
