import xlsxwriter
import sqlite3
import pandas as pd


def fetch_table_data(table_name):
    print(f"Fetching data from table: {table_name}")

    cnx = sqlite3.connect('courses.db')

    cursor = cnx.cursor()
    cursor.execute('select * from ' + table_name)

    header = [row[0] for row in cursor.description]
    print(f"Header: {header}")

    rows = cursor.fetchall()
    print(f"Number of rows fetched: {len(rows)}")

    cnx.close()

    return header, rows


def export(table_name):
    print(f"Exporting data from table {table_name} to Excel")

    workbook = xlsxwriter.Workbook(table_name + '.xlsx')
    worksheet = workbook.add_worksheet('MENU')

    header_cell_format = workbook.add_format(
        {'bold': True, 'border': True, 'bg_color': 'yellow'})
    body_cell_format = workbook.add_format({'border': True})

    header, rows = fetch_table_data(table_name)

    row_index = 0
    column_index = 0

    for column_name in header:
        worksheet.write(row_index, column_index,
                        column_name, header_cell_format)
        column_index += 1

    row_index += 1
    for row in rows:
        column_index = 0
        for column in row:
            worksheet.write(row_index, column_index, column, body_cell_format)
            column_index += 1
        row_index += 1

    print(f"{row_index} rows written successfully to {workbook.filename}")

    # Closing workbook
    workbook.close()
