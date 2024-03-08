import os
import subprocess
from django.conf import settings
from django.core.files.base import ContentFile


non_html_data = {
    "concept_staff_time_allocation": [
        ["Role", "Year 1", "Year 2", "Year 3"],
        ["Scientist", "", "", ""],
        ["Technical", "", "", ""],
        ["Volunteer", "", "", ""],
        ["Collaborator", "", "", ""],
    ],
    "concept_budget": [
        ["Source", "Year 1", "Year 2", "Year 3"],
        ["Consolidated Funds (DPaW)", "", "", ""],
        ["External Funding", "", "", ""],
    ],
    "project_plan_operating_budget": [
        ["Source", "Year 1", "Year 2", "Year 3"],
        ["FTE Scientist", "", "", ""],
        ["FTE Technical", "", "", ""],
        ["Equipment", "", "", ""],
        ["Vehicle", "", "", ""],
        ["Travel", "", "", ""],
        ["Other", "", "", ""],
        ["Total", "", "", ""],
    ],
    "project_plan_external_budget": [
        ["Source", "Year 1", "Year 2", "Year 3"],
        ["Salaries, Wages, OVertime", "", "", ""],
        ["Overheads", "", "", ""],
        ["Equipment", "", "", ""],
        ["Vehicle", "", "", ""],
        ["Travel", "", "", ""],
        ["Other", "", "", ""],
        ["Total", "", "", ""],
    ],
}


def iterate_rows_in_json_table(data_as_list):
    # Desired Structure
    #  <table class="table-dark">
    #       <colgroup>
    #         <col>
    #         <col>
    #         <col>
    #         <col>
    #         <col>
    #       </colgroup>
    #       <tbody>
    #         ${tableRows}
    #       </tbody>
    #     </table>

    table_innards = []

    for row_index, row in enumerate(data_as_list):
        row_contents = "".join(
            [
                f"<{'th' if (row_index == 0 or col_index == 0) else 'td'} "
                + f"class='table-cell-light{' table-cell-header-light' if row_index == 0 or col_index == 0 else ''}'>"
                + f"{col}"
                + f"</{'th' if (row_index == 0 or col_index == 0) else 'td'}>"
                for col_index, col in enumerate(row)
            ]
        )
        row_data = f"<tr>{row_contents}</tr>"
        table_innards.append(row_data)

    return_table = f'<table class="table-light">\
        <colgroup>\
            {" ".join("<col>" for _ in range(len(data_as_list[0])))}\
        </colgroup>\
        <tbody>{"".join(table_innards)}</tbody>\
    </table>'
    return return_table


def convert_to_html_table(data):
    value = data[0]
    if isinstance(data, str) and data.startswith("[[") and data.endswith("]]"):
        table_data = eval(data)
    elif isinstance(data, list):
        pass
    else:
        print(
            "ERR: The data you passed does not start and end with [[]] either as a string or a list"
        )
        print(type(data), data)
        return ""
    html = iterate_rows_in_json_table(eval(f"{table_data}"))
    return html


def create_prince_html_file(html_content):
    # Specify the file path where you want to save the HTML file on the server
    html_file_path = os.path.join(os.path.curdir, f"table_test.html")
    css_path = os.path.join(os.path.curdir, "documents", "rte_styles.css")

    with open(html_file_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

    p = subprocess.Popen(
        ["prince", "-", f"--style={css_path}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    outs, errs = p.communicate(f"{html_content}".encode("utf-8"))

    if p.returncode:
        # Handle `errs`.
        print(p.returncode)

    else:
        pdf = outs
        print("PDF is " + str(len(pdf)) + " bytes in size")

        pdf_filename = "table_test_pdf.pdf"
        pdf_file_path = os.path.join(
            os.path.curdir,
            "documents",
            f"pdf_filename",
        )

        with open(pdf_file_path, "wb") as pdf_file:
            pdf_file.write(outs)
            print(f"Saved pdf file to {pdf_file_path}")
        # file_content = ContentFile(pdf, name=pdf_filename)


if __name__ == "__main__":
    html_for_prince = ""
    for section in non_html_data:
        table_html_data = convert_to_html_table(section)
        html_for_prince += table_html_data
    print(html_for_prince)
