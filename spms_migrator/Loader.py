from datetime import datetime as dt
from pathlib import Path
import subprocess

# import time
import traceback
from django.conf import settings
import requests
from django.contrib.auth.hashers import make_password

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
import environ
import random
import string
import urllib3
import json
import os
from psycopg2 import sql

# from django.core.files import File
# from django.core.files.uploadedfile import SimpleUploadedFile
# from psycopg2 import Binary
# from django.core.files.images import ImageFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage

# from ..config.settings
from django.conf import settings
import psycopg2


def determine_user():
    env = environ.Env()
    BASE_DIR = Path(__file__).resolve().parent.parent
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
    print("basedir:", BASE_DIR)
    debugmode = env("DJANGO_DEBUG")
    print("debug:", debugmode)
    if debugmode == "True":
        user = (
            os.environ.get("USER") or os.getlogin()
        )  # Update to support linux environment
        return user


def determine_project_folder():
    print("DETERMINING PROJECT FOLDER")
    env = environ.Env()
    BASE_DIR = Path(__file__).resolve().parent.parent
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
    print("basedir:", BASE_DIR)
    debugmode = env("DJANGO_DEBUG")
    print("debug:", debugmode)
    if debugmode == "True":
        user = (
            os.environ.get("USER") or os.getlogin()
        )  # Update to support linux environment

        if user == "JaridPrince":
            return os.path.join(f"C:\\Users\\{user}\\Documents\\GitHub\\service_spms")
        else:
            return os.path.join(
                f"C:\\Users\\{user}\\Documents\\GitHub\\science-projects-service"
            )

    else:
        return os.path.join("/usr/src/app/backend")


class Loader:
    def __init__(
        self,
        file_handler,
        misc,
        psycopg2,
        tqdm,
        pd,
        os,
        load_dotenv,
        parent_directory,
    ):
        self.os = os
        self.user = determine_user()
        self.load_dotenv = load_dotenv
        self.tqdm = tqdm
        self.pd = pd
        self.psycopg2 = psycopg2
        self.misc = misc
        self.django_project_path = determine_project_folder()

        self.migrator_path = os.path.join(self.django_project_path, "spms_migrator")
        self.parent_directory = parent_directory
        self.file_handler = file_handler
        self.db_source = ""
        self.db_destination = ""
        self.functions = [
            {
                "name": "Run All",
                "function": self.spms_run_all,
            },
            {
                "name": "Recreate DB",
                "function": self.spms_recreate_db,
            },
            # SETUP AND DBCA BRANCHES/DIVISIONS/BAs
            {
                "name": "Create Super User",
                "function": self.spms_create_super_user,
                # TODO: Create UserProfile, UserContact, UserWork, UserAvatar entries for superuser
                # add a function for each of the below to add the superuser to those
            },
            {
                "name": "Create DBCA Agency",
                "function": self.spms_create_dbca_agency,
            },
            {
                "name": "Create DBCA Branches",
                "function": self.spms_create_dbca_branches,
            },
            {
                "name": "Create DBCA Business Areas",
                "function": self.spms_create_dbca_business_areas,
            },
        ]

    # GETTERS =====================================================================================

    def spms_upload_image_file(self, file_string, static=False):
        if file_string is not None:
            print(file_string)

        return None

    def spms_set_media_file(self, file_string, static=False):
        if file_string is not None:
            if static == True:
                file = (
                    f"http://scienceprojects.dbca.wa.gov.au/static/files/{file_string}"
                )
            else:
                file = f"http://scienceprojects.dbca.wa.gov.au/media/{file_string}"
            return file
        return None

    def get_empty_operating_budget_string(self):
        return '<table class="table-light">\
    <colgroup>\
        <col>\
        <col>\
        <col>\
        <col>\
    </colgroup>\
    <tbody>\
        <tr>\
        <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
            <p class="editor-p-light" dir="ltr">\
            <span style="white-space: pre-wrap;">Source</span>\
            </p>\
        </th>\
        <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
            <p class="editor-p-light" dir="ltr">\
            <span style="white-space: pre-wrap;">Year 1</span>\
            </p>\
        </th>\
        <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
            <p class="editor-p-light" dir="ltr">\
            <span style="white-space: pre-wrap;">Year 2</span>\
            </p>\
        </th>\
        <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
            <p class="editor-p-light" dir="ltr">\
            <span style="white-space: pre-wrap;">Year 3</span>\
            </p>\
        </th>\
        </tr>\
        <tr>\
        <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
            <p class="editor-p-light" dir="ltr">\
            <span style="white-space: pre-wrap;">Consolidated Funds (DBCA)</span>\
            </p>\
        </th>\
        <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
        <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
        <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
        </tr>\
        <tr>\
        <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
            <p class="editor-p-light" dir="ltr">\
            <span style="white-space: pre-wrap;">External Funding</span>\
            </p>\
        </th>\
        <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
        <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
        <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
        </tr>\
    </tbody>\
    </table>'

    def replace_json_string_with_html_table(self, input_string):
        # This function should generate a html table using a string in this format:
        # [["Source", "Year 1", "Year 2", "Year 3"], ["Consolidated Funds (DBCA)", "", "", ""], ["External Funding", "", "", ""]]
        # It should preserve the data values but should format things into a html table like the above
        try:
            # Attempt to parse the input JSON string
            data = json.loads(input_string)
        except json.JSONDecodeError:
            # If parsing fails, return the original input string
            return input_string

        # Begin constructing the HTML table with additional styling
        html_table = '<table class="table-light">\n  <colgroup>\n'
        html_table += '    <col style="background-color: rgb(242, 243, 245);">\n'  # Style for the leftmost column

        for _ in range(len(data[0])):
            html_table += "    <col>\n"

        html_table += "  </colgroup>\n  <tbody>\n"

        for i, row in enumerate(data):
            html_table += "    <tr>\n"
            for j, cell in enumerate(row):
                if i == 0:
                    # Apply background color to the first row
                    html_table += f'      <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\n'
                elif j == 0:
                    # Apply background color to the leftmost column
                    html_table += f'      <th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\n'
                else:
                    html_table += f'      <td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;">\n'

                html_table += f'        <p class="editor-p-light" dir="ltr">\n'
                html_table += (
                    f'          <span style="white-space: pre-wrap;">{cell}</span>\n'
                )
                html_table += f"        </p>\n"
                html_table += "      </" + ("th" if i == 0 else "td") + ">\n"

            html_table += "    </tr>\n"

        # Close the table
        html_table += "  </tbody>\n</table>"

        return html_table

    def generate_boundary(self):
        # Generate a random boundary value
        boundary = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        return boundary

    def spms_get_affiliation_by_name(self, connection, cursor, name):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_affiliation WHERE name = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (name,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                affiliation_id = result[0]  # Return the affiliation ID
        except Exception as e:
            self.misc.nli(f"here {name}")
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Affiliation: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            print(f"here2 {name}")
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Affiliation retrieved ({affiliation_id})!{self.misc.bcolors.ENDC}"
            )
            return affiliation_id

    def spms_check_proj_pdf_exists(self, doc_id, cursor, connection):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                    SELECT id FROM medias_projectdocumentpdf WHERE document_id = %s
                """

            # Execute the query with the user name
            cursor.execute(sql, (doc_id,))

            # Fetch the result
            result = cursor.fetchone()

            print(f"Result: {result}")

            if result:
                pdf_id = result[0]  # Return the report id
            else:
                return False
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}No PDF: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return False
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}PDF retrieved ({pdf_id})!{self.misc.bcolors.ENDC}"
            )
            return True

    def spms_get_new_report_id_by_year(self, connection, cursor, year):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                    SELECT id FROM documents_annualreport WHERE year = %s
                """

            # Execute the query with the user name
            cursor.execute(sql, (year,))

            # Fetch the result
            result = cursor.fetchone()

            print(f"Old Year: {year}")
            print(f"Result: {result}")

            if result:
                report_id = result[0]  # Return the report id
            else:
                return None
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Report: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Report retrieved ({report_id})!{self.misc.bcolors.ENDC}"
            )
            return report_id

    def spms_get_project_by_document_id(self, connection, cursor, document_id):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT project_id FROM documents_projectdocument WHERE id = %s
            """

            # Execute the query with the document_id
            cursor.execute(sql, (document_id,))

            # Fetch the result
            result = cursor.fetchone()

            print(f"Document ID: {document_id}")
            print(f"Result: {result}")

            if result:
                project_id = result[0]  # Return the project_id
            else:
                return None
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Project ID: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Project ID retrieved ({project_id})!{self.misc.bcolors.ENDC}"
            )
            return project_id

    def spms_get_ba_by_old_program_id(self, connection, cursor, old_id):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_businessarea WHERE old_id = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            print(f"Old ID: {old_id}")
            print(f"Result: {result}")

            if result:
                ba_id = result[0]  # Return the user ID
            else:
                return None
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Business Area: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Business Area retrieved ({ba_id})!{self.misc.bcolors.ENDC}"
            )
            return ba_id

    def spms_get_project_plan_details_by_new_id(self, connection, cursor, new_id):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM documents_projectplan WHERE document_id = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (new_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                new_doc_id = result[0]  # Return the ID
            else:
                # found none
                # new_doc_id =
                print(f"NO document corresponding to {new_id}")
                print(result)
                print(result[0])
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Document: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Document retrieved ({new_doc_id})!{self.misc.bcolors.ENDC}"
            )
            return new_doc_id

    def spms_get_address_by_branch_id(self, connection, cursor, branch_id):
        cursor = connection.cursor()

        # Construct the SQL query
        sql = """
            SELECT id FROM contacts_address WHERE branch_id = %s
        """

        print(f"Finding address with branch_id = {branch_id}")

        # Execute the query with the user name
        cursor.execute(sql, (branch_id,))

        # Fetch the result
        result = cursor.fetchone()
        print(result)

        if result:
            address = result[0]  # Return the branch ID
            return address
        else:
            input(f"NO address corresponding to {branch_id}")
            print(result)
            return None

    def spms_get_document_id_by_old_id(self, connection, cursor, old_id):
        cursor = connection.cursor()

        # Construct the SQL query
        sql = """
            SELECT id FROM documents_projectdocument WHERE old_id = %s
        """

        print(f"Finding document with old_id = {old_id}")

        # Execute the query with the user name
        cursor.execute(sql, (old_id,))

        # Fetch the result
        result = cursor.fetchone()
        print(result)

        if result:
            new_doc_id = result[0]  # Return the branch ID
            return new_doc_id
        else:
            # found none
            # new_doc_id =
            print(f"NO document corresponding to {old_id}")
            print(result)
            return None

    def spms_get_branch_by_old_id(self, connection, cursor, old_id):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_branch WHERE old_id = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                branch_id = result[0]  # Return the branch ID
            else:
                # found none
                # branch_id =
                print(f"NO branch corresponding to {old_id}")
                print(result)
                print(result[0])
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving branch: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Branch retrieved ({branch_id})!{self.misc.bcolors.ENDC}"
            )
            return branch_id

    def spms_get_user_by_username(self, connection, cursor, username):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM users_user WHERE username = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (username,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                user_id = result[0]  # Return the user ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving user: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User retrieved ({user_id})!{self.misc.bcolors.ENDC}"
            )
            return user_id

    def spms_get_area_by_old_id(self, connection, cursor, old_id):
        try:
            cursor = connection.cursor()

            old_id = int(old_id)

            # Construct the SQL query
            sql = """
                SELECT id FROM locations_area WHERE old_id = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                area_id = result[0]  # Return the user ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Area ID: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Area ID retrieved ({area_id})!{self.misc.bcolors.ENDC}"
            )
            return area_id

    def spms_get_project_details_based_on_doc_id(self, connection, cursor, document_id):
        try:
            cursor = connection.cursor()

            # Convert the old_id value to a regular Python integer
            document_id = int(document_id)

            # Construct the SQL query
            sql = """
                SELECT project_id FROM documents_projectdocument WHERE id = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (document_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                project_id = result[0]
            else:
                input("NO RESULT")
                return None
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving project: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Project ID retrieved. Fetching details for that project... ({project_id})!{self.misc.bcolors.ENDC}"
            )
            proj_sql = """
                SELECT * FROM projects_project WHERE id = %s
            """
            # Execute the query with the user name
            cursor.execute(proj_sql, (project_id,))

            # Fetch the result with column names
            columns = [col[0] for col in cursor.description]
            result = cursor.fetchone()

            if result:
                # Create a dictionary using column names as keys
                project_data = dict(zip(columns, result))
                print(project_data)
                print(project_data["title"])
                return project_data
            else:
                input("NO RESULT")
                return None

    def spms_get_ba_leader_from_project_ba(self, connection, cursor, business_area_id):
        try:
            cursor = connection.cursor()

            # Convert the old_id value to a regular Python integer
            ba_id = int(business_area_id)

            # Construct the SQL query
            sql = """
                SELECT leader_id FROM agencies_businessarea WHERE id = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (ba_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                leader_id = result[0]
            else:
                input("NO RESULT WHEN TRYING TO GET BUSINESS AREA LEADER")
                return None
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving project: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Returning leader_id... ({leader_id})!{self.misc.bcolors.ENDC}"
            )
            return leader_id

    def spms_get_directorate_id(self, connection, cursor):
        directorate_old_id = 6
        new_id = self.spms_get_user_by_old_id(
            connection=connection, cursor=cursor, old_id=directorate_old_id
        )
        return new_id

    def spms_set_real_directorate(self, connection, cursor):
        sql = """
        BEGIN;
        UPDATE agencies_agency
        SET key_stakeholder_id = %s;
        COMMIT;
        """

        print("Getting Director ID")
        director_id = self.spms_get_directorate_id(connection=connection, cursor=cursor)

        print("Updating Agency Director")
        cursor.execute(sql, (director_id,))

    def spms_get_project_by_old_id(self, connection, cursor, old_id):
        try:
            cursor = connection.cursor()

            # Convert the old_id value to a regular Python integer
            old_id = int(old_id)

            # Construct the SQL query
            sql = """
                SELECT id FROM projects_project WHERE old_id = %s
            """
            print(f"Seeking old id {old_id} in new table")

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                project_id = result[0]  # Return the user ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving project: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Project retrieved ({project_id})!{self.misc.bcolors.ENDC}"
            )
            return project_id

    def spms_get_division_by_old_id(self, connection, cursor, old_id):
        print(f"trying for old id: {old_id}")
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_division WHERE old_id = %s
            """

            old_id = int(old_id)

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                id = result[0]
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error old division id: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}New div id fetched ({id})!{self.misc.bcolors.ENDC}"
            )
            return id

    def spms_get_user_name_old_id(self, connection, cursor, old_id):
        print(f"trying for old id: {old_id}")
        if old_id == 101073 or old_id == "101073":
            return old_id
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT first_name, last_name FROM users_user WHERE old_pk = %s
            """

            old_id = int(old_id)

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                first_name, last_name = result
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving user: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User retrieved ({first_name} {last_name})!{self.misc.bcolors.ENDC}"
            )
            return f"{first_name} {last_name}"

    def spms_get_business_area_by_old_id(self, connection, cursor, old_id):
        print(f"trying for old id: {old_id}")
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_businessarea WHERE old_id = %s
            """

            old_id = int(old_id)

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                ba_id = result[0]  # Return the user ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving business area: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Business Area retrieved ({ba_id})!{self.misc.bcolors.ENDC}"
            )
            return ba_id

    def spms_get_user_by_old_id(self, connection, cursor, old_id):
        print(f"trying for old id: {old_id}")
        if old_id == 101073 or old_id == "101073":
            return old_id
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM users_user WHERE old_pk = %s
            """

            old_id = int(old_id)

            # Execute the query with the user name
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                user_id = result[0]  # Return the user ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving user: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User retrieved ({user_id})!{self.misc.bcolors.ENDC}"
            )
            return user_id

    # def spms_get_research_function_by_old_id(self, connection, cursor, old_id):
    #     try:
    #         # cursor = connection.cursor()

    #         # Construct the SQL query
    #         sql = """
    #             SELECT id FROM projects_researchfunction WHERE old_id = %s
    #         """

    #         old_id = int(old_id)

    #         # Execute the query with the user name
    #         cursor.execute(sql, (old_id,))

    #         # Fetch the result
    #         result = cursor.fetchone()

    #         if result:
    #             rf_id = result[0]  # Return the user ID
    #     except Exception as e:
    #         self.misc.nli(
    #             f"{self.misc.bcolors.FAIL}Error retrieving Research function: {str(e)}{self.misc.bcolors.ENDC}"
    #         )
    #         # Rollback the transaction
    #         connection.rollback()
    #         return None
    #     else:
    #         self.misc.nls(
    #             f"{self.misc.bcolors.OKGREEN}Research function retrieved ({rf_id})!{self.misc.bcolors.ENDC}"
    #         )
    #         return rf_id

    def spms_get_superuser(self, connection, cursor):
        # connection.autocommit = False
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM users_user WHERE username = %s
            """

            # Read .env for username
            print(f"{self.misc.bcolors.WARNING}Loading .env...{self.misc.bcolors.ENDC}")
            self.load_dotenv()

            superuser_username = self.os.getenv(
                "SPMS_SUPERUSER_USERNAME", "jarid.prince@dbca.wa.gov.au"
            )

            # Execute the query with the user name
            cursor.execute(sql, (superuser_username,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                superuser_id = result[0]  # Return the user ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving user: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User retrieved ({superuser_id})!{self.misc.bcolors.ENDC}"
            )
            return superuser_id

    def spms_get_agency_image(self, connection, cursor, agency_id):
        try:
            # Construct the SQL query
            sql = """
                SELECT id FROM medias_agencyimage WHERE agency_id = %s
            """

            # Execute the query with the agency id
            cursor.execute(sql, (agency_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                agency_image_id = result[0]  # Return the agency image ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving agency image ({agency_image_id}): {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Agency retrieved by agency_id ({agency_id})!{self.misc.bcolors.ENDC}"
            )
            return agency_image_id

    def spms_get_project_image(self, connection, cursor, project_id):
        try:
            # Construct the SQL query
            sql = """
                SELECT id FROM medias_projectphoto WHERE project_id = %s
            """

            # Execute the query with the agency id
            cursor.execute(sql, (project_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                project_image_id = result[0]  # Return the agency image ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving project image ({project_id}): {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Project Image retrieved by project_id ({project_id})!{self.misc.bcolors.ENDC}"
            )
            return project_image_id

    def spms_get_user_image(self, connection, cursor, user_id):
        try:
            # Construct the SQL query
            sql = """
                SELECT id FROM medias_useravatar WHERE user_id = %s
            """

            # Execute the query with the user id
            cursor.execute(sql, (user_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                user_image_id = result[0]  # Return the user avatar image ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving user image ({user_image_id}): {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            # self.misc.nls(
            #     f"{self.misc.bcolors.OKGREEN}Branch retrieved by old_id ({branch_id})!{self.misc.bcolors.ENDC}"
            # )
            return user_image_id

    def spms_get_dbca_agency(self, connection, cursor):
        try:
            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_agency WHERE name = %s
            """

            # Execute the query with the agency name
            cursor.execute(sql, ("DBCA",))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                agency_id = result[0]  # Return the agency ID

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving agency: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}DBCA agency retrieved ({agency_id})!{self.misc.bcolors.ENDC}"
            )
            return agency_id

    def spms_get_dbca_branch_by_old_id(self, connection, cursor, old_id):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_branch WHERE old_id = %s
            """

            # Execute the query with the old id of the branch (work center)
            cursor.execute(sql, (old_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                branch_id = result[0]  # Return the branch ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Branch by old_id ({branch_id}): {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Branch retrieved by old_id ({branch_id})!{self.misc.bcolors.ENDC}"
            )
            return branch_id

    def spms_get_dbca_branch_by_name(self, connection, cursor, name):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_branch WHERE name = %s
            """

            # Execute the query with the brnach name
            cursor.execute(sql, (name,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                branch_id = result[0]  # Return the branch ID
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Branch by name ({branch_id}): {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Branch retrieved by name ({branch_id})!{self.misc.bcolors.ENDC}"
            )
            return branch_id

    def spms_get_ba_by_name(self, connection, cursor, name):
        try:
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_businessarea WHERE name = %s
            """

            # Execute the query with the ba name
            cursor.execute(sql, (name,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                business_area_id = result[0]  # Return the ba ID

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving Business Area by name ({business_area_id}): {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Business Area retrieved by name ({business_area_id})!{self.misc.bcolors.ENDC}"
            )
            return business_area_id

    # HELPER & INTERMEDIATE FUNCTIONS =============================================================
    def spms_establish_dest_db_connection_and_return_cursor_conn(self):
        # Load the .env file
        print(f"{self.misc.bcolors.WARNING}Loading .env...{self.misc.bcolors.ENDC}")
        self.load_dotenv()

        try:
            # Establish a connection to the PostgreSQL database
            print(
                f"{self.misc.bcolors.WARNING}Establishing conn...{self.misc.bcolors.ENDC}"
            )

            env = environ.Env()
            BASE_DIR = Path(__file__).resolve().parent
            environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
            print("basedir:", BASE_DIR)
            debugmode = env("DJANGO_DEBUG")
            print("debug:", debugmode)
            print(
                "connecting to",
                (
                    env("SPMS_DESTINATION_HOST")
                    if debugmode == "True"
                    else env("PRODUCTION_HOST")
                ),
            )
            if debugmode == "True" or debugmode == True:
                connection = self.psycopg2.connect(
                    host=env("SPMS_DESTINATION_HOST"),
                    port=env("SPMS_DESTINATION_PORT"),
                    database=env("SPMS_DESTINATION_DB"),
                    user=env("SPMS_DESTINATION_USER"),
                    password=env("SPMS_DESTINATION_PASSWORD"),
                )
            else:
                connection = self.psycopg2.connect(
                    host=env("PRODUCTION_HOST"),
                    port=5432,
                    database=env("PRODUCTION_DB_NAME"),
                    user=env("PRODUCTION_USERNAME"),
                    password=env("PRODUCTION_PASSWORD"),
                )

            # Create a cursor object to execute SQL queries
            print(f"{self.misc.bcolors.WARNING}Creating cursor{self.misc.bcolors.ENDC}")
            cursor = connection.cursor()

            # Set the client_encoding parameter
            # self.psycopg2.extensions.register_type(
            #     self.psycopg2.extensions.UNICODE,
            #     connection_or_cursortype=self.psycopg2.extensions.connection,
            # )
            cursor.execute("SET client_encoding = 'UTF8';")
            connection.commit()
            print("Client encoding set to UTF8")

            return cursor, connection

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.WARNING}Error establishing database connection: {e}{self.misc.bcolors.ENDC}"
            )
            raise

    def display_columns_available_in_df(self, df):
        for i, column in enumerate(df.columns):
            print(f"{i + 1}. {column}")

    def alter_column_check(self, df):
        these_columns_okay = self.misc.nli(
            "Continue with these columns?\nType 'y' for yes or press enter for no:"
        )

        # If altering columns
        if these_columns_okay not in self.misc.yes_array:
            # Prompt user for columns to remove
            columns_to_remove = (
                input("Enter the column numbers to remove (comma-separated): ")
                .strip()
                .split(",")
            )

            # Convert user input to a list of integers
            columns_to_remove = [int(col.strip()) - 1 for col in columns_to_remove]

            # Remove selected columns from the DataFrame
            df.drop(df.columns[columns_to_remove], axis=1, inplace=True)

            # Check if user wishes to change column names
            # after displaying available columns
            self.display_columns_available_in_df(df)

            these_column_names_okay = self.misc.nli(
                "Continue with these column names?\nType 'y' for yes or press enter for no:"
            )

            # If altering columns
            if these_column_names_okay not in self.misc.yes_array:
                # Prompt user for columns to rename
                columns_to_rename = (
                    input("Enter the column numbers to rename (comma-separated): ")
                    .strip()
                    .split(",")
                )

                for column_num in columns_to_rename:
                    try:
                        column_num = int(column_num.strip()) - 1
                        old_column_name = df.columns[column_num]
                        new_column_name = input(
                            f"Enter new name for column '{old_column_name}': "
                        )

                        # Rename the column
                        df.rename(
                            columns={old_column_name: new_column_name}, inplace=True
                        )
                        print(
                            f"Column '{old_column_name}' renamed to '{new_column_name}'"
                        )
                    except (ValueError, IndexError):
                        print(f"Invalid column number: {column_num}")

        return df

    def spms_clean_migrations(self):
        removed_items = []
        env = environ.Env()
        BASE_DIR = Path(__file__).resolve().parent.parent
        environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
        print("basedir:", BASE_DIR)
        debugmode = env("DJANGO_DEBUG")

        for root, dirs, files in self.os.walk(self.django_project_path):
            for dir_name in dirs:
                if dir_name == "migrations":
                    migrations_path = self.os.path.join(root, dir_name)
                    for file_name in self.os.listdir(migrations_path):
                        if file_name != "__pycache__":
                            if file_name != "__init__.py":
                                file_path = self.os.path.join(
                                    migrations_path, file_name
                                )
                                if debugmode == "True":
                                    try:
                                        self.os.remove(file_path)
                                        print(f"Removed file: {file_path}")
                                        removed_items.append(file_path)
                                    except PermissionError:
                                        self.misc.nli(
                                            f"Permission denied: {file_path} - [WinError 5] Access is denied"
                                        )
                                    except Exception as e:
                                        print(e)

                                else:
                                    try:
                                        subprocess.run(["rm", file_path])
                                        print(
                                            f"Removed file using rm command: {file_path}"
                                        )
                                        removed_items.append(file_path)
                                    except Exception as e:
                                        print(
                                            f"Error removing file {file_path} with rm command: {e}"
                                        )

                    print(f"Removed files in {migrations_path}")
                elif dir_name == "__pycache__":
                    migrations_path = self.os.path.join(root, dir_name)
                    for file_name in self.os.listdir(migrations_path):
                        file_path = self.os.path.join(migrations_path, file_name)
                        try:
                            self.os.remove(file_path)
                            print(f"Removed file: {file_path}")
                            removed_items.append(file_path)
                        except PermissionError:
                            self.misc.nli(
                                f"Permission denied: {file_path} - [WinError 5] Access is denied"
                            )
                    print(f"Removed files in {migrations_path}")

        self.misc.nls("Removed theses files:")
        for item in removed_items:
            print(item)

    def spms_run_migrations(self):
        # Change to the Django project directory
        print(
            f"{self.misc.bcolors.WARNING}Changing to Django app dir...{self.misc.bcolors.ENDC}"
        )
        self.os.chdir(self.django_project_path)

        # Run the makemigrations and migrate commands
        print(
            f"{self.misc.bcolors.WARNING}Attempting migration...{self.misc.bcolors.ENDC}"
        )
        try:
            # Ensure DB clean
            # self.misc.nls(
            #     f"{self.misc.bcolors.OKGREEN}CLEANING!{self.misc.bcolors.ENDC}"
            # )
            # clean_command = "py manage.py migrate spms zero"
            # subprocess.run(clean_command, shell=True)

            # Run the makemigrations command
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}MAKING MIGRATIONS!{self.misc.bcolors.ENDC}"
            )
            makemigrations_command = "python manage.py makemigrations"
            subprocess.run(makemigrations_command, shell=True)

            # Run the migrate command
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}MIGRATING!{self.misc.bcolors.ENDC}"
            )
            migrate_command = "python manage.py migrate"
            subprocess.run(migrate_command, shell=True)
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not run migrations: {e}{self.misc.bcolors.ENDC}"
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Migrations complete!{self.misc.bcolors.ENDC}"
            )

        # Change back to this directory
        self.os.chdir(self.migrator_path)

    def spms_drop_and_create(self):
        # Load environment variables from .env file
        print(f"{self.misc.bcolors.WARNING}Loading Env...{self.misc.bcolors.ENDC}")
        self.load_dotenv()

        # Run the dropdb command
        print(
            f"{self.misc.bcolors.WARNING}Running drop command...{self.misc.bcolors.ENDC}"
        )
        try:
            dropdb_command = f"dropdb --if-exists --username={self.os.getenv('PGUSER')} --no-password {self.os.getenv('DBNAME')}"
            subprocess.run(dropdb_command, shell=True)
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not Run drop command{self.misc.bcolors.ENDC}",
                e,
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}DB Dropped successfully{self.misc.bcolors.ENDC}"
            )

        # Run the createdb command
        print("Running create command")
        try:
            createdb_command = f"createdb --username={self.os.getenv('PGUSER')} --no-password {self.os.getenv('DBNAME')}"
            subprocess.run(createdb_command, shell=True)
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not Run create command{self.misc.bcolors.ENDC}",
                e,
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}DB Created successfully{self.misc.bcolors.ENDC}"
            )

    def spms_create_super_user(self, auto=True):
        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        # Loading environment variables:
        if auto == True:
            print(
                f"{self.misc.bcolors.WARNING}Loading Environment variables...{self.misc.bcolors.ENDC}"
            )
            env_fn = self.os.getenv("SPMS_SUPERUSER_FIRST_NAME")
            env_ln = self.os.getenv("SPMS_SUPERUSER_LAST_NAME")
            env_email = self.os.getenv("SPMS_SUPERUSER_EMAIL")
            env_username = self.os.getenv("SPMS_SUPERUSER_USERNAME")
            env_pass = self.os.getenv("SPMS_SUPERUSER_PASSWORD")
            print(env_username, env_pass)

        else:
            print("Seeking details...")
            env_fn = self.misc.nli("Provide a first name:")
            env_ln = self.misc.nli("Provide a last name:")
            env_email = self.misc.nli("Provide an email:")
            env_username = self.misc.nli("Provide a username:")
            env_pass = self.misc.nli("Provide a password:")

        print(
            f"{self.misc.bcolors.WARNING}Setting the DJANGO_SETTINGS_MODULE...{self.misc.bcolors.ENDC}"
        )
        # Set the DJANGO_SETTINGS_MODULE environment variable
        self.os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", f"{self.django_project_path}.config.settings"
        )

        # Configure Django settings
        settings.configure()
        settings.MEDIA_URL = "/files/"
        settings.MEDIA_ROOT = os.path.join(self.django_project_path, "files")

        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL query...{self.misc.bcolors.ENDC}"
        )

        # Get the current date and time
        current_datetime = dt.now()

        try:
            # Start a transaction
            connection.autocommit = False
            cursor = connection.cursor()

            # Hash the password using Django's make_password function
            hashed_password = make_password(env_pass)

            # Construct the SQL query
            sql = """
                BEGIN;
                INSERT INTO users_user (
                    id, username, email, first_name, last_name, password,
                    is_superuser, is_aec, is_staff, is_active, date_joined
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                COMMIT;
            """
            # %s, %s, is_biometrician, is_herbarium_curator

            # Execute the query with the user data
            cursor.execute(
                sql,
                (
                    101073,  # The id of my email in db (to maintain links and skip this user when creating users)
                    env_username,
                    env_email,
                    env_fn,
                    env_ln,
                    hashed_password,
                    True,
                    True,
                    True,
                    True,
                    current_datetime,
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error creating super user: {str(e)}{self.misc.bcolors.ENDC}"
            )
            self.misc.nli(
                f"{self.misc.bcolors.UNDERLINE}MAKE SURE YOU DO NOT HAVE AN ACTIVE CONNECTION TO THE DATABASE!!{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Superuser Created!{self.misc.bcolors.ENDC}"
            )

        # Close the cursor and connection
        cursor.close()
        connection.close()

    def spms_create_super_user_profile(
        self, connection, cursor, superuser_id, current_datetime
    ):
        # Loading environment variables for superuser profile:
        print(
            f"{self.misc.bcolors.WARNING}Loading Environment variables for profile...{self.misc.bcolors.ENDC}"
        )
        env_about = self.os.getenv("SPMS_SUPERUSER_ABOUT", "Web Developer")
        env_role = self.os.getenv("SPMS_SUPERUSER_ROLE")
        env_expertise = self.os.getenv("SPMS_SUPERUSER_EXPERTISE", "Making this site")
        env_title = self.os.getenv("SPMS_SUPERUSER_TITLE", "mr")
        env_mid_init = self.os.getenv("SPMS_SUPERUSER_MIDDLE_INITIALS", "M.")
        env_cv = self.os.getenv(
            "SPMS_SUPERUSER_CURRICULUM_VITAE"
        )  # UNUSED FOR THIS PURPOSE, WILL BE A RELATIONAL LINK TO A FILES MODEL
        env_user_image = self.os.getenv("SPMS_SUPERUSER_IMAGE")

        # Create the User Avatar based on the env image
        user_image_id = self.spms_create_user_profile_image(
            image_file="profiles/1693448033243.jpg",
            connection=connection,
            cursor=cursor,
            image_link=env_user_image,
            user_id=superuser_id,
            current_datetime=current_datetime,
        )

        # Create the profile that correspond with the User
        try:
            # Construct the SQL query
            print(
                f"{self.misc.bcolors.WARNING}Contructing SQL for UserProfile...{self.misc.bcolors.ENDC}"
            )
            new_sql = """
                BEGIN;
                INSERT INTO users_userprofile (
                    created_at, updated_at, title, middle_initials, about, expertise, image_id, user_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                COMMIT;
            """

            # Execute the SQL query
            print(
                f"{self.misc.bcolors.WARNING}Executing SQL for UserProfile...{self.misc.bcolors.ENDC}"
            )
            cursor.execute(
                new_sql,
                (
                    current_datetime,  # created at
                    current_datetime,  # updated at
                    # env_role,  # role
                    env_title,  # title
                    env_mid_init,  # middle_initials
                    env_about,  # about
                    # env_cv,  # curriculum_vitae
                    env_expertise,  # expertise
                    user_image_id,  # image_id
                    superuser_id,  # user_id
                    # dbca_id,  # agency_id
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error Creating Superuser Profile:\n{str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User Profile Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

    def spms_check_affiliation_existence_by_name(self, name, cursor, connection):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Checking whether affiliation ({name}) exists...{self.misc.bcolors.ENDC}"
        )
        try:
            # Construct the SQL query
            sql = """
                SELECT id FROM agencies_affiliation WHERE name = %s
            """

            # Execute the query with the user name
            cursor.execute(sql, (name,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                return True
            else:
                return False
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error with affiliation search!{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
            return False

    def spms_create_affiliation(self, connection, cursor, name, current_datetime):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Attempting to create Affiliation with name...{self.misc.bcolors.ENDC}"
        )
        try:
            # Construct the SQL query
            sql = """
                BEGIN;
                INSERT INTO agencies_affiliation (
                    created_at, updated_at, name
                ) VALUES (%s, %s, %s);
                COMMIT;
            """

            # Execute the query with the user data
            cursor.execute(
                sql,
                (
                    current_datetime,
                    current_datetime,
                    name,
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error creating affiliation: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Affiliation Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

        # image_id = self.spms_get_user_image(
        #     connection=connection, cursor=cursor, user_id=user_id
        # )
        # return image_id

    def spms_create_user_profile_image(
        self, connection, cursor, image_link, user_id, current_datetime, image_file
    ):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Attempting to create UserAvatar with image link...{self.misc.bcolors.ENDC}"
        )
        try:
            # Construct the SQL query
            sql = """
                BEGIN;
                INSERT INTO medias_useravatar (
                    created_at, updated_at, file, user_id
                ) VALUES (%s, %s, %s, %s);
                COMMIT;
            """
            # old_file, %s
            image_file_directory = os.path.join(
                self.django_project_path, "dumped_media", image_file
            )
            print(image_file_directory)
            save_location = os.path.join(
                self.django_project_path, "files", "user_avatars"
            )
            saved_file = self.create_local_image(
                original_image_path=image_file_directory,
                folder_to_save_to=save_location,
            )

            # Execute the query with the user data
            print(user_id)
            cursor.execute(
                sql,
                (
                    current_datetime,
                    current_datetime,
                    saved_file,
                    # image_link,
                    # None,
                    user_id,
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error creating image: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User Image Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

        image_id = self.spms_get_user_image(
            connection=connection, cursor=cursor, user_id=user_id
        )
        return image_id

    def spms_create_dbca_image(
        self, connection, cursor, image_link, dbca_id, current_datetime
    ):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Attempting to create Image for DBCA with env image link...{self.misc.bcolors.ENDC}"
        )
        #
        file_path = os.path.join(self.django_project_path, "dbca.jpg")
        print(file_path)
        # Read the file content
        with open(file_path, "rb") as file:
            # Create an InMemoryUploadedFile
            uploaded_file = InMemoryUploadedFile(
                file,
                None,
                os.path.basename(file_path),
                "image/jpeg",  # Adjust the content type based on your file type
                len(file.read()),  # Pass the file content length
                None,
            )

            # Load the settings
            print(
                f"{self.misc.bcolors.WARNING}Setting the DJANGO_SETTINGS_MODULE...{self.misc.bcolors.ENDC}"
            )
            # Set the DJANGO_SETTINGS_MODULE environment variable
            self.os.environ.setdefault(
                "DJANGO_SETTINGS_MODULE", f"{self.django_project_path}.config.settings"
            )

            print(self.os.getenv("DJANGO_SETTINGS_MODULE"))

            # Configure Django settings
            # settings.configure()

            # Save the file to the default storage
            saved_file = default_storage.save(
                f"agencies/{uploaded_file.name}", uploaded_file
            )

            try:
                # Construct the SQL query
                sql = """
                    BEGIN;
                    INSERT INTO medias_agencyimage (
                        created_at, updated_at, file, agency_id
                    ) VALUES (%s, %s, %s, %s);
                    COMMIT;
                """

                # Execute the query with the user data
                cursor.execute(
                    sql,
                    (
                        current_datetime,
                        current_datetime,
                        saved_file,
                        dbca_id,
                    ),
                )

            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating image for DBCA: {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}DBCA Image Created!{self.misc.bcolors.ENDC}"
                )
            finally:
                connection.commit()

            agency_image_id = self.spms_get_agency_image(
                connection=connection, cursor=cursor, agency_id=dbca_id
            )
            return agency_image_id

    def create_local_image(self, original_image_path, folder_to_save_to):
        try:
            with open(original_image_path, "rb") as file:
                # Create an InMemoryUploadedFile
                uploaded_file = InMemoryUploadedFile(
                    file,
                    None,
                    os.path.basename(original_image_path),
                    "image/jpeg",  # Adjust the content type based on your file type
                    len(file.read()),  # Pass the file content length
                    None,
                )
                # Load the settings
                print(
                    f"{self.misc.bcolors.WARNING}Setting the DJANGO_SETTINGS_MODULE...{self.misc.bcolors.ENDC}"
                )
                # Set the DJANGO_SETTINGS_MODULE environment variable
                self.os.environ.setdefault(
                    "DJANGO_SETTINGS_MODULE",
                    f"{self.django_project_path}.config.settings",
                )

                print(self.os.getenv("DJANGO_SETTINGS_MODULE"))

                # Save the file to the default storage
                saved_file = default_storage.save(
                    f"{folder_to_save_to}/{uploaded_file.name}", uploaded_file
                )
                return saved_file
        except FileNotFoundError as fe:
            try:
                print(f"File not Found, stage 1: {fe}")
                # If the original file is not found, try with a capitalized file extension (for linux)
                root, ext = os.path.splitext(original_image_path)
                capitalized_path = f"{root}{ext.upper()}"
                with open(capitalized_path, "rb") as file:
                    uploaded_file = InMemoryUploadedFile(
                        file,
                        None,
                        os.path.basename(capitalized_path),
                        "image/jpeg",
                        len(file.read()),
                        None,
                    )
                    # Load the settings
                    print(
                        f"{self.misc.bcolors.WARNING}Setting the DJANGO_SETTINGS_MODULE...{self.misc.bcolors.ENDC}"
                    )
                    # Set the DJANGO_SETTINGS_MODULE environment variable
                    self.os.environ.setdefault(
                        "DJANGO_SETTINGS_MODULE",
                        f"{self.django_project_path}.config.settings",
                    )

                    print(self.os.getenv("DJANGO_SETTINGS_MODULE"))

                    # Save the file to the default storage
                    saved_file = default_storage.save(
                        f"{folder_to_save_to}/{uploaded_file.name}", uploaded_file
                    )
                    return saved_file
            except FileNotFoundError as fe2:
                print(f"File not Found, stage 2: {fe2}")
                # If both attempts fail, raise an error
                raise FileNotFoundError(
                    f"File not found: {original_image_path} or {capitalized_path}"
                )

    def spms_create_project_image(
        self,
        image_file,
        connection,
        cursor,
        image_link,
        current_datetime,
        project_id,
        uploader,
    ):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Attempting to create Image for Project with image link...{self.misc.bcolors.ENDC}"
        )
        try:
            # Construct the SQL query
            sql = """
                BEGIN;
                INSERT INTO medias_projectphoto (
                    created_at, updated_at, file, project_id, uploader_id
                ) VALUES (%s, %s, %s, %s, %s);
                COMMIT;
            """

            image_file_directory = os.path.join(
                self.django_project_path, "dumped_media", image_file
            )
            print(image_file_directory)
            save_location = os.path.join(self.django_project_path, "files", "projects")
            saved_file = self.create_local_image(
                original_image_path=image_file_directory,
                folder_to_save_to=save_location,
            )

            # Execute the query with the user data
            cursor.execute(
                sql,
                (
                    current_datetime,
                    current_datetime,
                    saved_file,
                    # image_link,
                    # None,
                    project_id,
                    uploader,
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error creating image for Project: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Project Image Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

        project_image_id = self.spms_get_project_image(
            connection=connection, cursor=cursor, project_id=project_id
        )
        return project_image_id

    def spms_create_super_user_contact(
        self, connection, cursor, superuser_id, current_datetime
    ):
        # Loading environment variables for superuser contact:
        print(
            f"{self.misc.bcolors.WARNING}Loading Environment variables for super user contact...{self.misc.bcolors.ENDC}"
        )
        email = self.os.getenv(
            "SPMS_SUPERUSER_CONTACT_EMAIL", "jarid.prince@dbca.wa.gov.au"
        )
        phone = self.os.getenv("SPMS_SUPERUSER_PHONE")
        alt_phone = self.os.getenv("SPMS_SUPERUSER_ALT_PHONE")
        fax = self.os.getenv("SPMS_SUPERUSER_FAX")

        # Create the contact info that correspond with the User
        try:
            # Construct the SQL query
            print(
                f"{self.misc.bcolors.WARNING}Contructing SQL for UserContact...{self.misc.bcolors.ENDC}"
            )
            new_sql = """
                BEGIN;
                INSERT INTO contacts_usercontact (
                    created_at, updated_at, email, phone, alt_phone, fax, user_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                COMMIT;
            """

            # Execute the SQL query
            print(
                f"{self.misc.bcolors.WARNING}Executing SQL for UserContact...{self.misc.bcolors.ENDC}"
            )
            cursor.execute(
                new_sql,
                (
                    current_datetime,  # created at
                    current_datetime,  # updated at
                    email,
                    phone,
                    alt_phone,
                    fax,
                    superuser_id,  # user_id
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error Creating Superuser Contact Details:\n{str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User Contact Details Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

    def spms_create_super_user_work(
        self,
        connection,
        cursor,
        superuser_id,
        current_datetime,
        # , dbca_id
    ):
        # Loading environment variables for superuser work:
        print(
            f"{self.misc.bcolors.WARNING}Loading Environment variables for super user work...{self.misc.bcolors.ENDC}"
        )
        branch_name = self.os.getenv("SPMS_SUPERUSER_BRANCH_NAME", "Kensington")
        ba_name = self.os.getenv("SPMS_SUPERUSER_BUSINESS_AREA_NAME", "Ecoinformatics")

        # Get the DBCA Agency ID
        dbca_id = self.spms_get_dbca_agency(connection=connection, cursor=cursor)
        # input(f"dbca_id: {dbca_id}")

        # Get branch by name
        branch_id = self.spms_get_dbca_branch_by_name(
            connection=connection, cursor=cursor, name=branch_name
        )
        # input(f"branch id: {branch_id}")

        # Get business area by name
        business_area_id = self.spms_get_ba_by_name(
            connection=connection, cursor=cursor, name=ba_name
        )
        # input(f"business_area_id: {business_area_id}")

        # Create the contact info that correspond with the User
        try:
            # Construct the SQL query
            print(
                f"{self.misc.bcolors.WARNING}Contructing SQL for UserWork...{self.misc.bcolors.ENDC}"
            )
            new_sql = """
                BEGIN;
                INSERT INTO users_userwork (
                    created_at, updated_at, branch_id, business_area_id, user_id, agency_id
                ) VALUES (%s, %s, %s, %s, %s, %s);
                COMMIT;
            """

            # Execute the SQL query
            print(
                f"{self.misc.bcolors.WARNING}Executing SQL for UserWork...{self.misc.bcolors.ENDC}"
            )
            cursor.execute(
                new_sql,
                (
                    current_datetime,  # created at
                    current_datetime,  # updated at
                    branch_id,
                    business_area_id,
                    superuser_id,  # user_id
                    dbca_id,  # agency
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error Creating Superuser Work Details:\n{str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}User Work Details Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

    def spms_determine_area_type(self, name):
        print(name)
        if name == 3:
            return "dbcaregion"
        elif name == 4:
            return "dbcadistrict"
        elif name == 5:
            return "ibra"
        elif name == 6:
            return "imcra"
        elif name == 7:
            return "nrm"

    # SPMS FUNCTIONS ===============================================================

    def spms_set_correct_user_ids(self):
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Creating SQL QUERY...{self.misc.bcolors.ENDC}"
        )
        ba_query = """
                SELECT * FROM agencies_businessarea
            """

        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Executing Query...{self.misc.bcolors.ENDC}"
        )
        cursor.execute(ba_query)

        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Fetching all and closing...{self.misc.bcolors.ENDC}"
        )
        data = cursor.fetchall()
        cursor.close()
        connection.close()

        data_dict = {
            "id": [],
            "old_leader_id": [],
            "old_finance_admin_id": [],
            "old_data_custodian_id": [],
        }

        column_names = [desc[0] for desc in cursor.description]  # Get the column names

        for row in data:
            row_dict = dict(zip(column_names, row))
            data_dict["id"].append(row_dict["id"])
            data_dict["old_leader_id"].append(row_dict["old_leader_id"])
            data_dict["old_finance_admin_id"].append(row_dict["old_finance_admin_id"])
            data_dict["old_data_custodian_id"].append(row_dict["old_data_custodian_id"])

        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Creating DataFrame...{self.misc.bcolors.ENDC}"
        )
        df = self.pd.DataFrame(data_dict)

        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Updating DataFrame...{self.misc.bcolors.ENDC}"
        )
        (
            new_cursor,
            new_connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        for _, row in df.iterrows():
            if row["old_leader_id"] is not None and not self.pd.isna(
                row["old_leader_id"]
            ):
                print(f"Updating old_leader: {row['old_leader_id']}")
                new_leader_id = self.spms_get_user_by_old_id(
                    old_id=row["old_leader_id"],
                    cursor=new_cursor,
                    connection=new_connection,
                )
                update_query = (
                    "UPDATE agencies_businessarea SET leader_id = %s WHERE id = %s"
                )
                new_cursor.execute(
                    update_query,
                    (
                        new_leader_id,
                        self.spms_get_ba_by_old_program_id(
                            old_id=row["id"],
                            cursor=new_cursor,
                            connection=new_connection,
                        ),
                    ),
                )

            if row["old_finance_admin_id"] is not None and not self.pd.isna(
                row["old_finance_admin_id"]
            ):
                print(f"Updating old_finance_admin_id: {row['old_finance_admin_id']}")
                new_finance_admin_id = self.spms_get_user_by_old_id(
                    old_id=row["old_finance_admin_id"],
                    cursor=new_cursor,
                    connection=new_connection,
                )
                update_query = "UPDATE agencies_businessarea SET finance_admin_id = %s WHERE id = %s"
                new_cursor.execute(
                    update_query,
                    (
                        new_finance_admin_id,
                        self.spms_get_ba_by_old_program_id(
                            old_id=row["id"],
                            cursor=new_cursor,
                            connection=new_connection,
                        ),
                    ),
                )

            if row["old_data_custodian_id"] is not None and not self.pd.isna(
                row["old_data_custodian_id"]
            ):
                print(f"Updating old_data_custodian_id: {row['old_data_custodian_id']}")
                new_data_custodian_id = self.spms_get_user_by_old_id(
                    old_id=row["old_data_custodian_id"],
                    cursor=new_cursor,
                    connection=new_connection,
                )
                update_query = "UPDATE agencies_businessarea SET data_custodian_id = %s WHERE id = %s"
                new_cursor.execute(
                    update_query,
                    (
                        new_data_custodian_id,
                        self.spms_get_ba_by_old_program_id(
                            old_id=row["id"],
                            cursor=new_cursor,
                            connection=new_connection,
                        ),
                    ),
                )

        new_connection.commit()
        new_cursor.close()
        new_connection.close()

        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Finished updating the database for BAs.{self.misc.bcolors.ENDC}"
        )

        # NOTE THAT BRANCHES (manager id must change to the real user)

        # pass

    def spms_clear_files(self):
        folder_path = os.path.join(self.django_project_path, "files")
        dump_path_arar = os.path.join(
            self.django_project_path, "dumped_media", "ararreports"
        )
        dump_path_docs = os.path.join(
            self.django_project_path, "dumped_media", "documents"
        )

        try:
            # Walk through all directories and files in the specified folder
            for root, dirs, files in os.walk(folder_path):
                # Delete all files in the current directory
                for file in files:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
        except Exception as e:
            print(f"Error clearing files: {e}")
        else:
            print("All files in subdirectories deleted successfully.")

    def spms_run_all(self):
        self.spms_clear_files()
        self.spms_recreate_db()  # Resets DB and creates superuser with user profile/image
        self.spms_set_encoding_to_utf8()
        self.spms_create_dbca_agency()  # Creates DBCA Agency
        self.spms_create_dbca_branches()  # Creates DBCA branches and their addresses
        self.spms_create_dbca_business_areas()  # Create Business Areas of DBCA Agency
        # # TODO: Create cost centers (no data present but a number)?
        self.spms_create_super_user_secondary_entries()  # Creates SU profile, contact, and work tables
        self.spms_create_users()  # populate users

        self.spms_set_correct_user_ids()
        # self.spms_create_dbca_research_functions()  # populate research functions (with users)
        self.spms_create_dbca_divisions()  # create the divisions that programs belong to
        self.spms_create_dbca_departmental_services()  # populate departmental services (with users)
        self.spms_create_quotes()  # Creates quotes from unique_quotes.txt file
        self.spms_create_locations()
        # # TODO: Remove "All" entries for areas
        self.spms_create_projects()
        self.spms_remove_empty_business_areas_and_set_original_ba_divisions()  # Removes BAs with no projects and saves it to txt

        self.spms_project_members_setter()  # Set the project team
        # (NOTE: duplicates are skipped, the first instance of user is taken into account only per project)
        self.spms_set_project_leaders()  # Set leaders if none

        self.spms_project_areas_setter()  # Sets which areas the project belongs to
        self.spms_create_annual_reports()
        self.spms_create_project_documents()  # Creates the concept, progress/stu report, project plan, closure And related tasks
        # # input("Create comments?")
        self.spms_create_document_comments()
        self.spms_create_superuser_todos()
        self.spms_set_new_leaders()
        # # Majority of media photo uploads
        # self.spms_replace_photo_with_cf_file(from_table="agencyimage")
        # self.spms_replace_photo_with_cf_file(from_table="businessareaphoto")
        # self.spms_replace_photo_with_cf_file(from_table="useravatar")
        # self.spms_replace_photo_with_cf_file(from_table="projectphoto")
        # self.spms_replace_photo_with_cf_file(from_table="annualreportmedia")

        self.misc.nls("Data ETL complete! You may now use the site!")

    def spms_remove_empty_business_areas_and_set_original_ba_divisions(self):
        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        try:
            # Scan all business areas and add them to a DataFrame
            cursor.execute("SELECT id, name FROM agencies_businessarea;")
            business_areas_data = cursor.fetchall()
            business_areas_df = self.pd.DataFrame(
                business_areas_data, columns=["id", "name"]
            )

            # Scan all projects, and if the business area in the project is in the DataFrame, remove the row from the DataFrame
            cursor.execute("SELECT id, business_area_id FROM projects_project;")
            projects_data = cursor.fetchall()
            projects_df = self.pd.DataFrame(
                projects_data, columns=["id", "business_area_id"]
            )

            business_areas_df = business_areas_df[
                ~business_areas_df["id"].isin(projects_df["business_area_id"])
            ]

            # Get the IDs of business areas that will be removed
            removed_business_area_ids = business_areas_df["id"].tolist()

            # Set the "business_area_id" to null in users_userwork for matching business areas

            for business_area_id in removed_business_area_ids:
                cursor.execute(
                    "UPDATE users_userwork SET business_area_id = NULL WHERE business_area_id = %s;",
                    (business_area_id,),
                )
                cursor.execute(
                    "DELETE FROM medias_businessareaphoto WHERE business_area_id = %s;",
                    (business_area_id,),
                )

            # When finished, remove all remaining business areas in the DataFrame from the db
            removed_business_areas = business_areas_df["name"].tolist()
            for business_area_id in removed_business_area_ids:
                cursor.execute(
                    "DELETE FROM agencies_businessarea WHERE id = %s;",
                    (business_area_id,),
                )

            # Commit the changes
            connection.commit()
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Empty business areas removed successfully.{self.misc.bcolors.ENDC}"
            )

            # Save the names of removed business areas to a text file

            # with open("RemovedBusinessAreas.txt", "w") as file:
            #     for name in removed_business_areas:
            #         file.write(name + "\n")
            filename = "RemovedBusinessAreas.txt"
            bas_dir = os.path.join(self.django_project_path, filename)
            # Read existing content from the file
            with open(bas_dir, "r") as file:
                existing_content = file.read()
            # Check if the content already exists
            for name in removed_business_areas:
                if f"{name}\n" not in existing_content:
                    # Append to the file
                    with open(bas_dir, "a") as file:
                        file.write(f"{name}\n")
                else:
                    print("already present in ba removal file")

        except Exception as e:
            connection.rollback()
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error occurred while removing empty business areas: {e}{self.misc.bcolors.ENDC}"
            )

        else:
            # Set the division to BCS for all current items
            try:
                bcs_division_id = self.spms_get_division_by_old_id(
                    connection=connection, cursor=cursor, old_id=1
                )
                sql = "UPDATE agencies_businessarea SET division_id = %s;"

                cursor.execute(sql, (bcs_division_id,))
                connection.commit()
            except Exception as e:
                connection.rollback()
                print("ERROR1:", e)

            # Add the new business areas
            def add_cem_bas():
                array_of_non_led = [
                    "Rivers and Estuaries Branch",
                    "Ecosystem Health Branch",
                    "Forest Management Branch",
                ]
                # dic_of_led = {
                #     "Rivers and Estuaries Branch": "Glen McLeod-Thorpe",
                #     "Ecosystem Health Branch": "Tony Mennen",
                #     "Forest Management Branch": "Martin Rayner",    # EXISTS
                # }
                cem_division_id = self.spms_get_division_by_old_id(
                    connection=connection, cursor=cursor, old_id=4
                )
                agency_id = 1
                now = dt.now()

                for ba in array_of_non_led:
                    sql = """
                            BEGIN;
                            INSERT INTO agencies_businessarea (
                                old_id, created_at, updated_at, division_id, name, slug, cost_center, published, is_active, focus, introduction, agency_id, data_custodian_id, finance_admin_id, leader_id, old_leader_id, old_finance_admin_id, old_data_custodian_id
                            ) VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s);
                            COMMIT;
                        """
                    cursor.execute(
                        sql,
                        (
                            None,
                            now,  # created at
                            now,  # updated at
                            cem_division_id,
                            ba,
                            None,
                            None,  # cost center
                            False,
                            True,
                            "",
                            "",
                            agency_id,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                        ),
                    )

            def add_rfms_bas():
                array_of_non_led = [
                    "Kimberley Region",
                    "Goldfields Region",
                    "Wheatbelt Region",
                    "Swan Region",
                    "Warren Region",
                    "East Kimberley District",
                    "West Kimberley District",
                    "Karratha District",
                    "Exmouth District",
                    "Murchison District",
                    "Gascoyne District",
                    "Turquoise Coast District",
                    "Perth Hills District",
                    "Swan Coastal District",
                    "Blackwood District",
                    "Wellington District",
                    "Donnelly District",
                    "Frankland District",
                    "Albany District",
                    "Esperance District",
                    "Pilbara Region",  # Led from here
                    "Midwest Region",
                    "South West Region",
                    "South Coast Region",
                ]

                # dic_of_led = {
                #     "Pilbara Region": "Alicia Whittington", #Exists
                #     "Midwest Region": "Alison Donovan",
                #     "South West Region": "Aminya Ennis",
                #     "South Coast Region": "Peter Hartley",
                # }

                rfms_division_id = self.spms_get_division_by_old_id(
                    connection=connection, cursor=cursor, old_id=6
                )
                agency_id = 1
                now = dt.now()

                for ba in array_of_non_led:
                    sql = """
                            BEGIN;
                            INSERT INTO agencies_businessarea (
                                old_id, created_at, updated_at, division_id, name, slug, cost_center, published, is_active, focus, introduction, agency_id, data_custodian_id, finance_admin_id, leader_id, old_leader_id, old_finance_admin_id, old_data_custodian_id
                            ) VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s);
                            COMMIT;
                        """
                    cursor.execute(
                        sql,
                        (
                            None,
                            now,  # created at
                            now,  # updated at
                            rfms_division_id,
                            ba,
                            None,
                            None,  # cost center
                            False,
                            True,
                            "",
                            "",
                            agency_id,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                        ),
                    )

            try:
                add_cem_bas()
            except Exception as e:
                print("Error on CEM:", e)

            try:
                add_rfms_bas()
            except Exception as e:
                print("Error on RFMS:", e)

            # Deactivate the business areas which are not in the list
            try:
                bas_to_deactivate = [
                    "Biodiversity and Climate Change Unit",
                    "Biogeography",
                    "Ecoinformatics",
                    "Perth Observatory",
                    "Region Swan",
                    "Wetlands Conservation",
                ]
                deactivate_sql = "UPDATE agencies_businessarea SET is_active = False WHERE name = %s;"

                for ba in bas_to_deactivate:
                    cursor.execute(deactivate_sql, (ba,))
                    connection.commit()
                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}Business area '{ba}' deactivated successfully.{self.misc.bcolors.ENDC}"
                    )
            except Exception as e:
                connection.rollback()
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error occurred while deactivating business areas: {e}{self.misc.bcolors.ENDC}"
                )

        finally:
            cursor.close()
            connection.close()

    def spms_set_new_leaders(self):
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False
        # FOR BCS, SET THE NEW BA LEADERS, DATA CUSTODIANS/FINANCIAL ADMINS BASED ON LIST FROM RORY
        ba_to_leader = [
            {
                "old_user_pk": 100934,
                "old_business_area_pk": 4,
            },  # Directorate BCS Rory McAuley Rory McAuley
            {
                "old_user_pk": 93,
                "old_business_area_pk": 5,
            },  # Animal Science Program BCS Lesley Gibson Lesley Gibson
            {
                "old_user_pk": 100936,
                "old_business_area_pk": 22,
            },  # Biodiversity Information Office BCS Rob Cechner Rob Cechner
            {
                "old_user_pk": 22,
                "old_business_area_pk": 7,
            },  # Ecosystem Science Program BCS Adrian Pinder Adrian Pinder
            {
                "old_user_pk": 100457,
                "old_business_area_pk": 21,
            },  # Fire Science Program BCS Ben Miller Ben Miller
            {
                "old_user_pk": 100462,
                "old_business_area_pk": 17,
            },  # Kings Park Science Program BCS Jason Stevens Jason Stevens
            {
                "old_user_pk": 156,
                "old_business_area_pk": 9,
            },  # Marine Science Program BCS Tom Holmes Tom Holmes
            {
                "old_user_pk": 101019,
                "old_business_area_pk": 18,
            },  # Perth Zoo Science Program BCS Harriet Mills Harriet Mills
            {
                "old_user_pk": 47,
                "old_business_area_pk": 6,
            },  # Plant Science and Herbarium BCS Carl Gosper Carl Gosper
            {
                "old_user_pk": 100448,
                "old_business_area_pk": 19,
            },  # Remote Sensing and Spatial Analysis BCS Katherine Zdunic Katherine Zdunic
            {
                "old_user_pk": 100458,
                "old_business_area_pk": 20,
            },  # Rivers and Estuaries BCS Kerry Trayler Kerry Trayler
            {
                "old_user_pk": 100749,
                "old_business_area_pk": 15,
            },  # Species and Communities BCS Ruth Harvey Ruth Harvey
        ]

        ba_leader_update_sql = "UPDATE agencies_businessarea SET leader_id = %s, data_custodian_id = %s, finance_admin_id = %s WHERE id = %s;"

        for item in ba_to_leader:
            # get the new leader id
            try:
                leader_id = self.spms_get_user_by_old_id(
                    connection=connection, cursor=cursor, old_id=item["old_user_pk"]
                )
                ba_id = self.spms_get_business_area_by_old_id(
                    connection=connection,
                    cursor=cursor,
                    old_id=item["old_business_area_pk"],
                )
                cursor.execute(
                    ba_leader_update_sql, (leader_id, leader_id, leader_id, ba_id)
                )
                connection.commit()
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Business area '{item}' updated successfully.{self.misc.bcolors.ENDC}"
                )

            except Exception as e:
                connection.rollback()
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error while setting new ba leaders: {e}{self.misc.bcolors.ENDC}"
                )

    def spms_create_users(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Base Users...{self.misc.bcolors.ENDC}"
        )

        # Load the users file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_user.csv"
            )
            users_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the current date and time
        current_datetime = dt.now()

        # Set checker variable
        temp_number = 1  # Used for creating a temp email
        created_user_count = 0
        first_names_created = 0
        last_names_created = 0

        # Establish columns we want to use in users df
        users_columns = users_df[
            [
                "id",
                "password",
                "last_login",
                "is_active",
                "is_superuser",
                "is_staff",
                "is_external",
                "date_joined",
                "username",
                "first_name",
                "last_name",
                "email",
                "publications_staff",
                "publications_other",
                "program_id",
                "work_center_id",
                "affiliation",
                "phone",
                "phone_alt",
                "fax",
                "middle_initials",
                "title",
                "profile_text",
                "expertise",
                "image",
            ]
        ]

        total_user_count = users_columns.shape[0]

        # Construct the SQL queries
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL queries...{self.misc.bcolors.ENDC}"
        )
        sql = """
            BEGIN;
            INSERT INTO users_user (
                is_active, 
                username, 
                password, 
                last_login, 
                is_superuser, 
                is_staff, 
                is_aec,
                date_joined, 
                first_name, last_name, email, old_pk
            ) VALUES (%s, %s,  %s, %s, %s,%s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        #                 is_herbarium_curator,
        # is_biometrician,
        # %s, %s,

        contact_sql = """
                BEGIN;
                INSERT INTO contacts_usercontact (
                    created_at, updated_at, email, phone, alt_phone, fax, user_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                COMMIT;
            """

        work_sql = """
            BEGIN;
            INSERT INTO users_userwork (
                created_at, updated_at, role, branch_id, business_area_id, affiliation_id, user_id, agency_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        profile_sql = """
                BEGIN;
                INSERT INTO users_userprofile (
                    created_at, updated_at, title, middle_initials, about, expertise, image_id, user_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                COMMIT;
        """

        self.load_dotenv()
        throwaway_pass = self.os.getenv("SPMS_THROWAWAY_PASS")

        for index, user in users_columns.iterrows():
            # Skip my superuser account
            if user["id"] != 101073:
                # Create a temp email for external users to avoid duplicate email issue.
                if self.pd.isna(user["email"]):
                    user["email"] = f"unset_{temp_number}@email.com"
                    temp_number += 1

                is_staff_value = False
                is_superuser_value = False

                if self.pd.isna(user["first_name"]):
                    user["first_name"] = "None"
                    first_names_created += 1

                if self.pd.isna(user["last_name"]):
                    user["last_name"] = "None"
                    last_names_created += 1

                if (
                    user["email"].endswith("@dbca.wa.gov.au")
                    and user["is_external"] == False
                ):
                    is_staff_value = True
                    if user["is_superuser"]:
                        is_superuser_value = True

                if is_staff_value == False:
                    is_superuser_value = False

                hashed_password = (
                    # make_password(throwaway_pass)
                    # if self.pd.isna(user["password"])
                    # else
                    user["password"]
                )

                try:
                    # Start a transaction
                    cursor = connection.cursor()

                    cursor.execute(
                        sql,
                        (
                            user["is_active"],
                            user["username"],
                            hashed_password,
                            user["last_login"],
                            is_superuser_value,
                            is_staff_value,
                            # False,  # is_herbarium_curator,
                            # False,  # is_biometrician,
                            False,  # is_aec,
                            user["date_joined"],
                            user["first_name"],
                            user["last_name"],
                            user["email"],
                            user["id"],  # old_pk
                        ),
                    )

                except Exception as e:
                    self.misc.nli(
                        f"{self.misc.bcolors.FAIL}Error creating User ({user['username']}): {str(e)}{self.misc.bcolors.ENDC}"
                    )
                    input()
                    # Rollback the transaction
                    connection.rollback()

                else:
                    # self.misc.nls(
                    #     f"{self.misc.bcolors.OKGREEN}User ({user['username']}) Created!{self.misc.bcolors.ENDC}"
                    # )
                    created_user_count += 1
                    if user["first_name"] == "None" and user["last_name"] != "None":
                        self.misc.nls(
                            f"{self.misc.bcolors.WARNING}User ({user['username']}): {user['first_name']} {user['last_name']}{self.misc.bcolors.ENDC}"
                        )
                    if not self.pd.isna(user["publications_staff"]) or not self.pd.isna(
                        user["publications_other"]
                    ):
                        print(user["username"])
                        print(f"staff pubs: {user['publications_staff']}")
                        print(f"other pubs: {user['publications_other']}")

                finally:
                    connection.commit()
                    new_user_id = self.spms_get_user_by_old_id(
                        old_id=user["id"],
                        cursor=cursor,
                        connection=connection,
                    )

                    print("created user")

                # Create Affiliations if they don't exist
                if not self.pd.isna(user["affiliation"]):
                    exists = self.spms_check_affiliation_existence_by_name(
                        name=user["affiliation"], cursor=cursor, connection=connection
                    )
                    if not exists:
                        self.spms_create_affiliation(
                            cursor=cursor,
                            connection=connection,
                            name=user["affiliation"],
                            current_datetime=current_datetime,
                        )

                # Create Images
                if self.pd.isna(user["image"]):
                    image_string = None
                    image_id = None
                else:
                    image_string = (
                        f'https://scienceprojects.dbca.wa.gov.au/media/{user["image"]}'
                    )
                    image_id = self.spms_create_user_profile_image(
                        image_file=user["image"],
                        connection=connection,
                        cursor=cursor,
                        image_link=image_string,
                        user_id=new_user_id,
                        current_datetime=current_datetime,
                    )

                # Get the branch, business area and affiliation based on old_id and affiliatoin name
                users_branch_id = (
                    self.spms_get_branch_by_old_id(
                        connection=connection,
                        cursor=cursor,
                        old_id=user["work_center_id"],
                    )
                    if not self.pd.isna(user["work_center_id"])
                    else None
                )

                users_ba_id = (
                    self.spms_get_ba_by_old_program_id(
                        connection=connection, cursor=cursor, old_id=user["program_id"]
                    )
                    if not self.pd.isna(user["program_id"])
                    else None
                )

                users_affiliation_id = (
                    None
                    if self.pd.isna(user["affiliation"])
                    else self.spms_get_affiliation_by_name(
                        connection=connection, cursor=cursor, name=user["affiliation"]
                    )
                )

                # Get the user ID for newly committed user as well as agency
                user_id = self.spms_get_user_by_username(
                    connection=connection, cursor=cursor, username=user["username"]
                )
                agency_id = (
                    None
                    if is_staff_value == False
                    else self.spms_get_dbca_agency(connection=connection, cursor=cursor)
                )

                # Attempt PROFILE creation
                self.misc.nls(
                    f"{self.misc.bcolors.WARNING}Attempting to create profile ({user['username']})...{self.misc.bcolors.ENDC}"
                )
                try:
                    cursor.execute(
                        profile_sql,
                        (
                            current_datetime,  # created at
                            current_datetime,  # updated at
                            # "NONE",  # role
                            (
                                None
                                if self.pd.isna(user["title"]) or len(user["title"]) > 5
                                else user["title"]
                            ),  # title #TODO: Double check
                            (
                                None
                                if self.pd.isna(user["middle_initials"])
                                else user["middle_initials"]
                            ),  # middle_initials
                            (
                                None
                                if self.pd.isna(user["profile_text"])
                                else user["profile_text"]
                            ),  # about
                            (
                                None
                                if self.pd.isna(user["expertise"])
                                else user["expertise"]
                            ),  # expertise
                            image_id,  # image_id
                            user_id,  # user_id
                        ),
                    )
                except Exception as e:
                    self.misc.nli(
                        f"{self.misc.bcolors.FAIL}Failed to create profile ({user['username']}): {str(e)}{self.misc.bcolors.ENDC}"
                    )
                    input()
                    connection.rollback()
                else:
                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}User Profile Details Created!{self.misc.bcolors.ENDC}"
                    )
                finally:
                    connection.commit()

                # Attempt WORK creation
                self.misc.nls(
                    f"{self.misc.bcolors.WARNING}Attempting to create work ({user['username']})...{self.misc.bcolors.ENDC}"
                )
                try:
                    cursor.execute(
                        work_sql,
                        (
                            current_datetime,  # created at
                            current_datetime,  # updated at
                            None,  # role
                            (
                                None
                                if self.pd.isna(user["work_center_id"])
                                else users_branch_id
                            ),
                            None if self.pd.isna(user["program_id"]) else users_ba_id,
                            users_affiliation_id,
                            user_id,  # user_id
                            agency_id,  # agency_id
                        ),
                    )
                except Exception as e:
                    self.misc.nli(
                        f"{self.misc.bcolors.FAIL}Failed to create work ({user['username']}): {str(e)}{self.misc.bcolors.ENDC}"
                    )
                    input()
                    connection.rollback()
                else:
                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}User Work Details Created!{self.misc.bcolors.ENDC}"
                    )
                finally:
                    connection.commit()

                # Attempt CONTACT creation
                self.misc.nls(
                    f"{self.misc.bcolors.WARNING}Attempting to create contact ({user['username']}...{self.misc.bcolors.ENDC}"
                )
                try:
                    cursor.execute(
                        contact_sql,
                        (
                            current_datetime,  # created at
                            current_datetime,  # updated at
                            user["email"],
                            # None if self.pd.isna(user["email"]) else user["email"],
                            None if self.pd.isna(user["phone"]) else user["phone"],
                            (
                                None
                                if self.pd.isna(user["phone_alt"])
                                else user["phone_alt"]
                            ),
                            None if self.pd.isna(user["fax"]) else user["fax"],
                            user_id,  # user_id
                        ),
                    )

                except Exception as e:
                    self.misc.nli(
                        f"{self.misc.bcolors.FAIL}Error Creating User Contact Details ({user['username']}):\n{str(e)}{self.misc.bcolors.ENDC}"
                    )
                    # Rollback the transaction
                    input()
                    connection.rollback()
                else:
                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}User Contact Details Created!{self.misc.bcolors.ENDC}"
                    )
                finally:
                    connection.commit()

            # TODO: At the end of all operations remove old_id from users table in django

        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Setting the directorate{self.misc.bcolors.ENDC}."
        )
        self.spms_set_real_directorate(connection=connection, cursor=cursor)

        self.misc.nls(
            f"{self.misc.bcolors.OKGREEN}{created_user_count}/{total_user_count} Created!  {temp_number} external emails created.{self.misc.bcolors.ENDC}."
        )
        self.misc.nls(
            f"{self.misc.bcolors.OKGREEN}{first_names_created}/{total_user_count} first names created! {last_names_created}/{total_user_count} last names created!{self.misc.bcolors.ENDC}."
        )
        # Commit the changes and close the cursor and connection
        cursor.close()
        connection.close()

        print("User Load operation finished.")

        pass

    def spms_create_super_user_secondary_entries(self):
        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        # Get the current date and time
        current_datetime = dt.now()

        # Get the Super User ID
        superuser_id = self.spms_get_superuser(connection=connection, cursor=cursor)

        # Create the profile info that correspond with the User
        self.spms_create_super_user_profile(
            connection=connection,
            cursor=cursor,
            current_datetime=current_datetime,
            superuser_id=superuser_id,
        )

        # Create the contact info that correspond with the User
        self.spms_create_super_user_contact(
            connection=connection,
            cursor=cursor,
            current_datetime=current_datetime,
            superuser_id=superuser_id,
        )

        # # Create the contact info that correspond with the User
        self.spms_create_super_user_work(
            connection=connection,
            cursor=cursor,
            current_datetime=current_datetime,
            superuser_id=superuser_id,
            # dbca_id=dbca_id,
        )

    def spms_create_quotes(self):
        # Quote Cleaner function (Transforms)
        def clean_quotes():
            print(self.os.path.dirname(self.os.path.realpath(__file__)))
            quote_file_location = (
                self.os.path.dirname(self.os.path.realpath(__file__))
                + "/unique_quotes.txt"
            )
            print(quote_file_location)
            with open(quote_file_location) as quotesfile:
                processed_1 = []
                duplicates = []
                unique_quotes = []
                array_of_raw_quotes = quotesfile.readlines()
                for line in array_of_raw_quotes:
                    line.strip()
                    line.lower()
                    if line not in processed_1:
                        processed_1.append(line)
                    else:
                        duplicates.append(line)
                for p1 in processed_1:
                    line_array = p1.split(" - ")
                    check = len(line_array)
                    if check <= 2:
                        quote = line_array[0]
                        author = line_array[1]
                    else:
                        quote_array = line_array[:-1]
                        quote = " - ".join(item for item in quote_array)
                        quote.strip()
                        author = line_array[-1]
                    unique_quotes.append({"text": quote, "author": author})

                print(f"\n\n\nFormatting: {unique_quotes[0]}\n")
                print(f"Uniques: {len(unique_quotes)}/{len(array_of_raw_quotes)}\n")
                print(f"Duplicates: {duplicates}\n")
                return unique_quotes

        # Ensures quotes are clean
        uniques = clean_quotes()

        # Establish connection to the server
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        # Start a transaction
        connection.autocommit = False
        cursor = connection.cursor()

        # Create the SQL query
        sql = """
            BEGIN;
            INSERT INTO quotes_quote (
                created_at, updated_at, text, author
            ) VALUES (%s, %s, %s, %s);
            COMMIT;
        """

        current_datetime = dt.now()

        try:
            # Execute the query per quote
            for obj in uniques:
                text = obj["text"]
                author = obj["author"]

                cursor.execute(
                    sql,
                    (current_datetime, current_datetime, text, author),
                )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error creating quote: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Quotes Created!{self.misc.bcolors.ENDC}"
            )

        # Close the cursor and connection
        cursor.close()
        connection.close()

    def create_psqlrc_file(self):
        home_dir = self.os.path.expanduser("~")
        psqlrc_path = self.os.path.join(home_dir, ".psqlrc")

        if not self.os.path.exists(psqlrc_path):
            with open(psqlrc_path, "w") as psqlrc_file:
                psqlrc_file.write("\\encoding UTF8\n")

            print("Created .psqlrc file with UTF8 encoding.")
        else:
            print(".psqlrc file already exists.")

    def spms_set_encoding_to_utf8(self):
        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        self.create_psqlrc_file()

        try:
            self.misc.nls(
                f"{self.misc.bcolors.WARNING}Setting DB to UTF 8...{self.misc.bcolors.ENDC}"
            )
            self.os.environ["PGCLIENTENCODING"] = "UTF8"  # Set the environment variable
            cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
            # cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
            # cursor.execute("SET PGCLIENTENCODING=utf-8;")
            # cursor.execute("\encoding UTF8;")
            connection.commit()
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Failed: {e}{self.misc.bcolors.ENDC}"
            )
        finally:
            try:
                # Execute the query to fetch the encoding
                cursor.execute("SHOW server_encoding;")
                encoding = cursor.fetchone()[0]

                print(f"The database encoding is: {encoding}")

            except Exception as e:
                self.misc.nli(
                    f"Failed to fetch the encoding: {e}"
                )  # Clean up resources
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    def spms_clean_database(self):
        # Load environment variables from .env file
        print(f"{self.misc.bcolors.WARNING}Loading Env...{self.misc.bcolors.ENDC}")
        self.load_dotenv()

        # Run the sqlflush command
        print(
            f"{self.misc.bcolors.WARNING}Running sqlflush command...{self.misc.bcolors.ENDC}"
        )
        try:
            print("User is", self.user)
            flush_command = f"python manage.py flush --noinput"
            subprocess.run(flush_command, shell=True, cwd=self.django_project_path)
        except Exception as e:
            print("project path", self.django_project_path)
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not run flush command: {e}{self.misc.bcolors.ENDC}",
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Flush ran successfully{self.misc.bcolors.ENDC}"
            )
        self.spms_drop_all_tables_in_db()

    def spms_drop_all_tables_in_db(self):
        try:
            print(
                f"{self.misc.bcolors.OKBLUE}Dropping every table...{self.misc.bcolors.ENDC}"
            )
            # Establish a database connection
            (
                cursor,
                connection,
            ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

            # Disable foreign key checks
            # NO PERMISSIONS
            # cursor.execute("SET session_replication_role = 'replica';")

            # Get a list of all tables in the public schema
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            )
            tables = cursor.fetchall()

            # Drop each table
            for table in tables:
                table_name = table[0]
                drop_table_query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE;").format(
                    sql.Identifier(table_name)
                )
                cursor.execute(drop_table_query)

            # Enable foreign key checks
            # NO PERMISSIONS
            # cursor.execute("SET session_replication_role = 'origin';")

            # Commit the changes
            connection.commit()

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not drop all tables: {str(e)}{self.misc.bcolors.ENDC}",
            )
            # Rollback the transaction
            connection.rollback()
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Tables dropped successfully{self.misc.bcolors.ENDC}"
            )
        finally:
            # Close the cursor and connection
            cursor.close()
            connection.close()

    def spms_recreate_db(self):
        print(
            f"{self.misc.bcolors.WARNING}Recreating DB Function Starting...{self.misc.bcolors.ENDC}"
        )

        # Dropping and Recreating DB
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Recreating DB...{self.misc.bcolors.ENDC}"
        )
        # self.spms_drop_and_create()
        self.spms_clean_database()

        # Removing migration files
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Removing Migration Files...{self.misc.bcolors.ENDC}"
        )
        self.spms_clean_migrations()

        # Running Migrations
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Running Migrations...{self.misc.bcolors.ENDC}"
        )
        self.spms_run_migrations()

        # Creating Superuser
        print(
            f"{self.misc.bcolors.OKBLUE}Creating Superuser...{self.misc.bcolors.ENDC}"
        )
        self.spms_create_super_user()

    def spms_create_dbca_agency(self, auto=True):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating DBCA Agency...{self.misc.bcolors.ENDC}"
        )

        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        # Get the current date and time
        current_datetime = dt.now()

        # Try the Query
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL query...{self.misc.bcolors.ENDC}"
        )
        try:
            # Start a transaction
            connection.autocommit = False
            cursor = connection.cursor()

            # Construct the SQL query
            sql = """
                BEGIN;
                INSERT INTO agencies_agency (
                    created_at, updated_at, name, key_stakeholder_id, is_active
                ) VALUES (%s, %s,%s, %s, %s);
                COMMIT;
            """

            # Execute the query with the user data
            cursor.execute(
                sql,
                (
                    current_datetime,
                    current_datetime,
                    "DBCA",
                    101073,
                    True,
                ),
            )
            # ,

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error creating DBCA Agency: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}DBCA Agency Created!{self.misc.bcolors.ENDC}"
            )
            # Create agency image
            try:
                self.misc.nls(
                    f"{self.misc.bcolors.WARNING}Creating agency image...{self.misc.bcolors.ENDC}"
                )
                print(
                    f"{self.misc.bcolors.WARNING}Getting agency...{self.misc.bcolors.ENDC}"
                )
                dbca_id = self.spms_get_dbca_agency(
                    connection=connection, cursor=cursor
                )

                print(
                    f"{self.misc.bcolors.WARNING}Loading env image...{self.misc.bcolors.ENDC}"
                )
                dbca_logo = self.os.getenv("DBCA_LOGO")

                print(
                    f"{self.misc.bcolors.WARNING}Creating the image...{self.misc.bcolors.ENDC}"
                )
                self.spms_create_dbca_image(
                    connection=connection,
                    cursor=cursor,
                    current_datetime=current_datetime,
                    image_link=dbca_logo,
                    dbca_id=dbca_id,
                )
            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating DBCA Agency Image: {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Rollback the transaction
                connection.rollback()
            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}DBCA Agency Image Created!{self.misc.bcolors.ENDC}"
                )

        finally:
            # Close the cursor and connection
            cursor.close()
            connection.close()

    def spms_create_dbca_branches(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating DBCA Branches...{self.misc.bcolors.ENDC}"
        )

        # Load the workcenter file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_workcenter.csv"
            )
            workcenter_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Load the address file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_address.csv"
            )
            address_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Display the columns available in workcenter file
        self.misc.nls("Columns available for workcenter df:")
        self.display_columns_available_in_df(workcenter_df)

        # Display the columns available in address file
        self.misc.nls("Columns available for address df:")
        self.display_columns_available_in_df(address_df)

        # Get the agency with the name "DBCA" if it exists
        # And set the agency_id value to the id of that row.
        dbca_id = self.spms_get_dbca_agency(connection=connection, cursor=cursor)

        # Get the user with the name "jp" if it exists
        # And set the manager_id value to the id of that row.
        superuser_id = self.spms_get_superuser(connection=connection, cursor=cursor)

        # Insert data from the DataFrame into the Branches model
        # Try the Query
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL query...{self.misc.bcolors.ENDC}"
        )
        # Get the current date and time
        current_datetime = dt.now()

        # Establish columns we want to use in workcenter df
        workcenter_cols = workcenter_df[["id", "name", "physical_address_id"]]

        # Establish columns we want to use in address df
        address_cols = address_df[
            ["id", "street", "extra", "city", "zipcode", "state", "country"]
        ]

        # Create an entry for each branch in the csv
        for index, workcenter in workcenter_cols.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating entry for {workcenter['name']}...{self.misc.bcolors.ENDC}"
            )
            try:
                # Start a transaction
                cursor = connection.cursor()

                # Construct the SQL query
                sql = """
                    BEGIN;
                    INSERT INTO agencies_branch (
                        created_at, updated_at, old_id, name, agency_id, manager_id
                    ) VALUES (%s, %s, %s,%s, %s, %s);
                    COMMIT;
                """
                cursor.execute(
                    sql,
                    (
                        current_datetime,
                        current_datetime,
                        workcenter["id"],
                        (
                            workcenter["name"]
                            if workcenter["name"]
                            != "Kensington (including Herbarium)"  # Removes the bracketed part from Kensington
                            else "Kensington"
                        ),
                        dbca_id,
                        superuser_id,
                    ),
                )

            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating DBCA branch ({workcenter['name']}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}DBCA branch ({workcenter['name']}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # Create the addresses that correspond with the Branch
            try:
                # Start a transaction - alr started
                # cursor = connection.cursor()

                # Construct the SQL query for address
                print("contructing SQL...")
                new_address_sql = """
                    BEGIN;
                    INSERT INTO contacts_address (
                        created_at, updated_at, street, suburb, city, zipcode, state, country, pobox, branch_id, agency_id
                    ) VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s,%s, %s);
                    COMMIT;
                """

                # Construct the SQL query for branch contact
                print("contructing SQL...")
                new_branch_contact_sql = """
                    BEGIN;
                    INSERT INTO contacts_branchcontact (
                        created_at, updated_at, email, phone, alt_phone, fax, address_id, branch_id
                    ) VALUES (%s, %s, %s, %s, %s, %s,%s, %s);
                    COMMIT;
                """
                # Determine the corresponding row based on physical_address_id in branch
                for add_index, address in address_cols.iterrows():
                    if address["id"] == workcenter["physical_address_id"]:
                        print("Getting branch id...")
                        # Get the newly created Branch by its old_id
                        branch_id = self.spms_get_dbca_branch_by_old_id(
                            cursor=cursor,
                            connection=connection,
                            old_id=workcenter["id"],
                        )
                        pobox = (
                            None if self.pd.isna(address["extra"]) else address["extra"]
                        )

                        print(f"Executing SQL for {workcenter['name']}...")
                        cursor.execute(
                            new_address_sql,
                            (
                                current_datetime,
                                current_datetime,
                                (
                                    None
                                    if self.pd.isna(address["street"])
                                    else address["street"]
                                ),
                                None,  # suburb
                                (
                                    None
                                    if self.pd.isna(address["city"])
                                    else address["city"]
                                ),
                                (
                                    None
                                    if self.pd.isna(address["zipcode"])
                                    else address["zipcode"]
                                ),
                                (
                                    None
                                    if self.pd.isna(address["state"])
                                    else address["state"]
                                ),
                                (
                                    None
                                    if self.pd.isna(address["country"])
                                    else address["country"]
                                ),
                                pobox,
                                branch_id,  # Branch ID (of just created branch)
                                None,  # Not using agency for branch (agency can only have one address)
                            ),
                        )

                        connection.commit()

                        try:
                            address_id = self.spms_get_address_by_branch_id(
                                connection=connection,
                                cursor=cursor,
                                branch_id=branch_id,
                            )

                            cursor.execute(
                                new_branch_contact_sql,
                                (
                                    current_datetime,
                                    current_datetime,
                                    None,
                                    None,
                                    None,
                                    None,
                                    address_id,
                                    branch_id,  # Branch ID (of just created branch)
                                ),
                            )
                        except Exception as e:
                            self.misc.nli(
                                f"{self.misc.bcolors.FAIL}Error Creating Branch Contact ({workcenter['name']}):\n{str(e)}{self.misc.bcolors.ENDC}"
                            )
                            # Rollback the transaction
                            connection.rollback()

                        else:
                            self.misc.nls(
                                f"{self.misc.bcolors.OKGREEN}Contact for Branch ({workcenter['name']}) Created!{self.misc.bcolors.ENDC}"
                            )

                        finally:
                            connection.commit()

            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error Creating Branch Address ({workcenter['name']}):\n{str(e)}{self.misc.bcolors.ENDC}"
                )
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Address for Branch ({workcenter['name']}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

        # TODO: At the end of all operations remove old_id from branches table in django

        # Commit the changes and close the cursor and connection
        cursor.close()
        connection.close()

        print("Branch Load operation finished.")

    def spms_create_dbca_business_areas(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating DBCA Business Areas...{self.misc.bcolors.ENDC}"
        )

        # Load the business area file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_program.csv"
            )
            ba_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the user with the name "jp" if it exists
        # And set the manager_id value to the id of that row.
        superuser_id = self.spms_get_superuser(connection=connection, cursor=cursor)

        # Get the DBCA Agency
        dbca_id = self.spms_get_dbca_agency(connection=connection, cursor=cursor)

        # Get the current date and time
        current_datetime = dt.now()

        # Establish columns we want to use in workcenter df
        ba_columns = ba_df[
            [
                "id",
                "name",
                "slug",
                "published",
                "program_leader_id",
                "cost_center",
                "finance_admin_id",
                "data_custodian_id",
                "focus",
                "introduction",
                "image",
            ]
        ]

        # Cost center gets created AND COMPARED AGAINST THIS VALUE TO ASSIGN COST CENTER ID

        # Insert data from the DataFrame into the BA model
        # Try the Query
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL query...{self.misc.bcolors.ENDC}"
        )

        # Construct the SQL query
        sql = """
            BEGIN;
            INSERT INTO agencies_businessarea (
                old_id, created_at, updated_at, division_id, name, slug, cost_center, published, is_active, focus, introduction, agency_id, data_custodian_id, finance_admin_id, leader_id, old_leader_id, old_finance_admin_id, old_data_custodian_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        # old_id, %s,
        # Create an entry for each branch in the csv
        for index, business_area in ba_columns.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating entry for {business_area['name']}...{self.misc.bcolors.ENDC}"
            )
            try:
                # Start a transaction
                cursor = connection.cursor()

                # array = [
                #     current_datetime,
                #     current_datetime,
                #     business_area["name"],
                #     business_area["slug"],
                #     business_area["cost_center"],
                #     business_area["published"],
                #     True,
                #     business_area["focus"],
                #     business_area["introduction"],
                #     dbca_id,
                #     superuser_id,
                #     superuser_id,
                #     None,
                #     superuser_id,
                #     0
                #     if self.pd.isna(business_area["program_leader_id"]) == None
                #     else business_area["program_leader_id"],
                #     0
                #     if self.pd.isna(business_area["finance_admin_id"]) == None
                #     else business_area["finance_admin_id"],
                #     0
                #     if self.pd.isna(business_area["data_custodian_id"]) == None
                #     else business_area["data_custodian_id"],
                # ]
                # for item in array:
                #     print(f"{type(item)}: {item}")
                pl_value = (
                    None
                    if self.pd.isna(business_area["program_leader_id"])
                    else business_area["program_leader_id"]
                )
                fa_value = (
                    (
                        None
                        if self.pd.isna(business_area["finance_admin_id"])
                        else business_area["finance_admin_id"]
                    ),
                )
                dc_value = (
                    (
                        None
                        if self.pd.isna(business_area["data_custodian_id"])
                        else business_area["data_custodian_id"]
                    ),
                )

                cursor.execute(
                    sql,
                    (
                        business_area["id"],  # old_id,
                        current_datetime,
                        current_datetime,
                        None,
                        business_area["name"],
                        business_area["slug"],
                        (
                            None
                            if self.pd.isna(business_area["cost_center"])
                            else business_area["cost_center"]
                        ),
                        business_area["published"],
                        True,
                        (
                            None
                            if self.pd.isna(business_area["focus"])
                            else business_area["focus"]
                        ),
                        (
                            None
                            if self.pd.isna(business_area["introduction"])
                            else business_area["introduction"]
                        ),
                        dbca_id,
                        superuser_id,  # data custodian id
                        superuser_id,  # finance_admin_id
                        # None,  # images are locked behind auth wall
                        # business_area["image"],
                        superuser_id,  # leader_id
                        pl_value,
                        fa_value,
                        dc_value,
                        # business_area["program_leader_id"],  # old leader id
                        # business_area["finance_admin_id"],  # old finance admin id
                        # business_area["data_custodian_id"],  # old data custodian id
                    ),
                )

            except Exception as e:
                print(
                    (
                        business_area["id"],  # old_id,
                        current_datetime,
                        current_datetime,
                        business_area["name"],
                        business_area["slug"],
                        (
                            None
                            if self.pd.isna(business_area["cost_center"])
                            else business_area["cost_center"]
                        ),
                        business_area["published"],
                        True,
                        (
                            None
                            if self.pd.isna(business_area["focus"])
                            else business_area["focus"]
                        ),
                        (
                            None
                            if self.pd.isna(business_area["introduction"])
                            else business_area["introduction"]
                        ),
                        dbca_id,
                        superuser_id,  # data custodian id
                        superuser_id,  # finance_admin_id
                        None,  # images are locked behind auth wall
                        # business_area["image"],
                        superuser_id,  # leader_id
                        pl_value,
                        fa_value,
                        dc_value,
                        # business_area["program_leader_id"],  # old leader id
                        # business_area["finance_admin_id"],  # old finance admin id
                        # business_area["data_custodian_id"],  # old data custodian id
                    ),
                )
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating DBCA BA ({business_area['name']}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}DBCA BA ({business_area['name']}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

                try:
                    self.misc.nls("Creating Business Area Image...")
                    ba_id = self.spms_get_ba_by_old_program_id(
                        connection=connection, cursor=cursor, old_id=business_area["id"]
                    )
                    # image_link = (
                    #     self.spms_set_media_file(business_area["image"])
                    #     if not self.pd.isna(business_area["image"])
                    #     else None
                    # )

                    # In the dumped_media folder
                    if not self.pd.isna(business_area["image"]):
                        image_file_directory = os.path.join(
                            self.django_project_path,
                            "dumped_media",
                            business_area["image"],
                        )
                        print(image_file_directory)
                        save_location = os.path.join(
                            self.django_project_path, "files", "business_areas"
                        )
                        saved_file = self.create_local_image(
                            original_image_path=image_file_directory,
                            folder_to_save_to=save_location,
                        )

                        ba_image_sql = """
                        BEGIN;
                        INSERT INTO medias_businessareaphoto (
                            created_at, updated_at, file, business_area_id, uploader_id
                        ) VALUES (%s, %s, %s, %s, %s);
                        COMMIT;
                        """
                        # , old_file %s,
                        cursor.execute(
                            ba_image_sql,
                            (
                                current_datetime,
                                current_datetime,
                                saved_file,
                                # image_link,
                                # None,
                                ba_id,
                                superuser_id,
                            ),
                        )
                except Exception as e:
                    self.misc.nli(
                        f"{self.misc.bcolors.FAIL}Failed to create Business Area Image! {e}{self.misc.bcolors.ENDC}"
                    )
                    connection.rollback()

                else:
                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}Created Business Area Image!{self.misc.bcolors.ENDC}"
                    )
                    connection.commit()

        # TODO: At the end of all operations remove old_id & old_director_id from divisions table in django

        # Commit the changes and close the cursor and connection
        cursor.close()
        connection.close()

        print("BA Load operation finished.")

        # def spms_create_business_areas(self):
        #     BusinessArea = self.import_model("agencies", "BusinessArea")
        #     agency = self.import_model("agencies", "agency")
        #     User = self.import_model("users", "User")
        #     BusinessAreaPhoto = self.import_model("medias", "BusinessAreaPhoto")

        #     # Load the file into a data frame
        #     file_path = self.os.path.join(
        #         self.file_handler.clean_directory, "pythia_program.csv"
        #     )
        #     df = self.file_handler.read_csv_and_prepare_df(file_path)

        #     # Display the columns available in file
        #     self.display_columns_available_in_df(df)

        #     # Check if continuing with these columns or not
        #     df = self.alter_column_check(df)

        #     # Establish DB connection
        #     (
        #         cursor,
        #         connection,
        #     ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        #     # Get the agency with the name "DBCA" if it exists
        #     try:
        #         dbca_agency = agency.objects.get(name="DBCA")
        #     except agency.DoesNotExist:
        #         # If the agency does not exist, create it
        #         user, _ = User.objects.get_or_create(
        #             email="jarid.prince@dbca.wa.gov.au", username="jp"
        #         )
        #         user.set_password("1")
        #         user.is_superuser = True
        #         user.is_staff = True
        #         user.save()

        #         dbca_agency = agency.objects.create(name="DBCA", key_stakeholder=user)

        #     # Insert data from the DataFrame into the BusinessArea model
        #     try:
        #         for row in df.itertuples(index=False):
        #             # Calculate the current year
        #             current_year = dt.now().year

        #             # Create the BusinessArea object
        #             business_area = BusinessArea(
        #                 old_pk=row.id,
        #                 agency_id=dbca_agency.id,
        #                 name=row.name,
        #                 slug=row.slug,
        #                 published=row.published,
        #                 is_active=row.is_active,
        #                 leader=row.leader_id,
        #                 finance_admin=row.finance_admin_id,
        #                 data_custodian=row.data_custodian_id,
        #                 focus=row.focus,
        #                 introduction=row.introduction,
        #                 image=None
        #                 # image=row.image,
        #             )

        #             business_area.save()

        #             # Save the BusinessArea object first
        #             business_area.save()

        #             # Create or get the BusinessAreaPhoto object
        #             business_area_photo, created = BusinessAreaPhoto.objects.get_or_create(
        #                 file=row.image,
        #                 defaults={
        #                     "year": current_year,
        #                     "business_area": business_area,
        #                     "uploader": dbca_agency.key_stakeholder,
        #                 },
        #             )

        #             # Assign the BusinessAreaPhoto to the BusinessArea
        #             business_area.image = business_area_photo
        #             business_area.save()

        #     except Exception as e:
        #         print(e)

        #     # Commit the changes and close the cursor and connection
        #     connection.commit()
        #     cursor.close()
        #     connection.close()

        #     print("Business Area Load operation finished.")
        pass

    # def spms_create_dbca_research_functions(self):
    #     self.misc.nls(
    #         f"{self.misc.bcolors.OKBLUE}Creating DBCA Research Functions...{self.misc.bcolors.ENDC}"
    #     )

    #     # Load the research functions file into a data frame
    #     try:
    #         file_path = self.os.path.join(
    #             self.file_handler.clean_directory, "projects_researchfunction.csv"
    #         )
    #         rf_df = self.file_handler.read_csv_and_prepare_df(file_path)
    #     except Exception as e:
    #         self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
    #     else:
    #         print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

    #     # Establishing connection:
    #     (
    #         cursor,
    #         connection,
    #     ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
    #     connection.autocommit = False

    #     # # Get the user with the name "jp" if it exists
    #     # superuser_id = self.spms_get_superuser(connection=connection, cursor=cursor)

    #     # # Get the DBCA Agency
    #     # dbca_id = self.spms_get_dbca_agency(connection=connection, cursor=cursor)

    #     # Get the current date and time
    #     current_datetime = dt.now()

    #     # Establish columns we want to use in workcenter df
    #     rf_columns = rf_df[
    #         [
    #             "id",
    #             "name",
    #             "description",
    #             "leader_id",
    #             "association",
    #             "active",
    #         ]
    #     ]

    #     # Insert data from the DataFrame into the RF model
    #     # Try the Query
    #     print(
    #         f"{self.misc.bcolors.WARNING}Beginning SQL query...{self.misc.bcolors.ENDC}"
    #     )

    #     # Construct the SQL query
    #     sql = """
    #         BEGIN;
    #         INSERT INTO projects_researchfunction (
    #             old_id, created_at, updated_at, name, description, leader_id, association, is_active
    #         ) VALUES (%s, %s, %s, %s, %s,%s, %s, %s);
    #         COMMIT;
    #     """

    #     # Create an entry for each branch in the csv
    #     for index, research_function in rf_columns.iterrows():
    #         print(
    #             f"{self.misc.bcolors.WARNING}Creating entry for {research_function['name']}...{self.misc.bcolors.ENDC}"
    #         )

    #         # Get the new leader if there was an old one
    #         if self.pd.isna(research_function["leader_id"]):
    #             new_leader_id = None
    #         else:
    #             new_leader_id = self.spms_get_user_by_old_id(
    #                 connection=connection,
    #                 cursor=cursor,
    #                 old_id=research_function["leader_id"],
    #             )

    #         try:
    #             # Start a transaction
    #             cursor = connection.cursor()

    #             cursor.execute(
    #                 sql,
    #                 (
    #                     research_function["id"],  # old_id,
    #                     current_datetime,
    #                     current_datetime,
    #                     research_function["name"],
    #                     None
    #                     if self.pd.isna(research_function["description"])
    #                     else research_function["description"],
    #                     new_leader_id,  # leader id based on old pk
    #                     None
    #                     if self.pd.isna(research_function["association"])
    #                     else research_function["association"],
    #                     research_function["active"],
    #                 ),
    #             )

    #         except Exception as e:
    #             self.misc.nli(
    #                 f"{self.misc.bcolors.FAIL}Error creating DBCA RF ({research_function['name']}): {str(e)}{self.misc.bcolors.ENDC}"
    #             )
    #             # Print the complete traceback information
    #             traceback_str = traceback.format_exc()
    #             print(traceback_str)
    #             # Rollback the transaction
    #             connection.rollback()

    #         else:
    #             self.misc.nls(
    #                 f"{self.misc.bcolors.OKGREEN}DBCA RF ({research_function['name']}) Created!{self.misc.bcolors.ENDC}"
    #             )

    #         finally:
    #             connection.commit()

    #     # TODO: At the end of all operations remove old_id & old_director_id from divisions table in django

    #     # Commit the changes and close the cursor and connection
    #     cursor.close()
    #     connection.close()

    #     print("RF Load operation finished.")

    #     # def spms_create_business_areas(self):
    #     #     BusinessArea = self.import_model("agencies", "BusinessArea")
    #     #     agency = self.import_model("agencies", "agency")
    #     #     User = self.import_model("users", "User")
    #     #     BusinessAreaPhoto = self.import_model("medias", "BusinessAreaPhoto")

    #     #     # Load the file into a data frame
    #     #     file_path = self.os.path.join(
    #     #         self.file_handler.clean_directory, "pythia_program.csv"
    #     #     )
    #     #     df = self.file_handler.read_csv_and_prepare_df(file_path)

    #     #     # Display the columns available in file
    #     #     self.display_columns_available_in_df(df)

    #     #     # Check if continuing with these columns or not
    #     #     df = self.alter_column_check(df)

    #     #     # Establish DB connection
    #     #     (
    #     #         cursor,
    #     #         connection,
    #     #     ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

    #     #     # Get the agency with the name "DBCA" if it exists
    #     #     try:
    #     #         dbca_agency = agency.objects.get(name="DBCA")
    #     #     except agency.DoesNotExist:
    #     #         # If the agency does not exist, create it
    #     #         user, _ = User.objects.get_or_create(
    #     #             email="jarid.prince@dbca.wa.gov.au", username="jp"
    #     #         )
    #     #         user.set_password("1")
    #     #         user.is_superuser = True
    #     #         user.is_staff = True
    #     #         user.save()

    #     #         dbca_agency = agency.objects.create(name="DBCA", key_stakeholder=user)

    #     #     # Insert data from the DataFrame into the BusinessArea model
    #     #     try:
    #     #         for row in df.itertuples(index=False):
    #     #             # Calculate the current year
    #     #             current_year = dt.now().year

    #     #             # Create the BusinessArea object
    #     #             business_area = BusinessArea(
    #     #                 old_pk=row.id,
    #     #                 agency_id=dbca_agency.id,
    #     #                 name=row.name,
    #     #                 slug=row.slug,
    #     #                 published=row.published,
    #     #                 is_active=row.is_active,
    #     #                 leader=row.leader_id,
    #     #                 finance_admin=row.finance_admin_id,
    #     #                 data_custodian=row.data_custodian_id,
    #     #                 focus=row.focus,
    #     #                 introduction=row.introduction,
    #     #                 image=None
    #     #                 # image=row.image,
    #     #             )

    #     #             business_area.save()

    #     #             # Save the BusinessArea object first
    #     #             business_area.save()

    #     #             # Create or get the BusinessAreaPhoto object
    #     #             business_area_photo, created = BusinessAreaPhoto.objects.get_or_create(
    #     #                 file=row.image,
    #     #                 defaults={
    #     #                     "year": current_year,
    #     #                     "business_area": business_area,
    #     #                     "uploader": dbca_agency.key_stakeholder,
    #     #                 },
    #     #             )

    #     #             # Assign the BusinessAreaPhoto to the BusinessArea
    #     #             business_area.image = business_area_photo
    #     #             business_area.save()

    #     #     except Exception as e:
    #     #         print(e)

    #     #     # Commit the changes and close the cursor and connection
    #     #     connection.commit()
    #     #     cursor.close()
    #     #     connection.close()

    #     #     print("Business Area Load operation finished.")

    #     pass

    def spms_create_dbca_divisions(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating DBCA Divisions...{self.misc.bcolors.ENDC}"
        )

        # Load the divisions file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_division.csv"
            )
            ds_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Establish columns we want to use in df
        ds_columns = ds_df[
            [
                "id",
                "created",
                "modified",
                # "creator_id",
                # "modifier_id",
                "director_id",
                "approver_id",
                "slug",
                "name",
            ]
        ]

        # Insert data from the DataFrame into the model
        # Try the Query
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL query for divisions...{self.misc.bcolors.ENDC}"
        )

        # Construct the SQL query
        # creator_id,
        # modifier_id,
        division_sql = """
            BEGIN;
            INSERT INTO agencies_division (
                old_id, 
                created_at,
                updated_at,

                director_id, 
                approver_id,
                name,
                slug
            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        # Create an entry for each branch in the csv
        for index, division in ds_columns.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating entry for Division: {division['name']}...{self.misc.bcolors.ENDC}"
            )

            old_id = division["id"]

            # Get the new director_id if there was an old one
            if self.pd.isna(division["director_id"]):
                new_director_id = None
            else:
                new_director_id = self.spms_get_user_by_old_id(
                    connection=connection,
                    cursor=cursor,
                    old_id=division["director_id"],
                )

            # Get the new approver_id if there was an old one
            if self.pd.isna(division["director_id"]):
                new_approver_id = None
            else:
                new_approver_id = self.spms_get_user_by_old_id(
                    connection=connection,
                    cursor=cursor,
                    old_id=division["approver_id"],
                )

            # # Get the new modifier_id
            # if self.pd.isna(division["modifier_id"]):
            #     new_modifier_id = None
            # else:
            #     new_modifier_id = self.spms_get_user_by_old_id(
            #         connection=connection,
            #         cursor=cursor,
            #         old_id=division["modifier_id"],
            #     )

            # # Get the new creator_id
            # if self.pd.isna(division["creator_id"]):
            #     new_creator_id = None
            # else:
            #     new_creator_id = self.spms_get_user_by_old_id(
            #         connection=connection,
            #         cursor=cursor,
            #         old_id=division["creator_id"],
            #     )

            try:
                # Start a transaction
                cursor = connection.cursor()

                cursor.execute(
                    division_sql,
                    (
                        old_id,
                        division["created"],
                        division["modified"],
                        # new_creator_id,
                        # new_modifier_id,
                        new_director_id,
                        new_approver_id,
                        None if self.pd.isna(division["name"]) else division["name"],
                        None if self.pd.isna(division["slug"]) else division["slug"],
                    ),
                )

            except Exception as e:
                print(
                    old_id,
                    division["created"],
                    division["modified"],
                    # new_creator_id,
                    # new_modifier_id,
                    new_director_id,
                    new_approver_id,
                    None if self.pd.isna(division["name"]) else division["name"],
                    None if self.pd.isna(division["slug"]) else division["slug"],
                )
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating DBCA Division: {division['name']}: {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}DBCA Division: {division['name']} Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

        # TODO: At the end of all operations remove old_id & old_director_id from divisions table in django

        # Commit the changes and close the cursor and connection
        cursor.close()
        # connection.close()

    def spms_create_dbca_departmental_services(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating DBCA Departmental Services...{self.misc.bcolors.ENDC}"
        )

        # Load the services file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_service.csv"
            )
            ds_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Establish columns we want to use in df
        ds_columns = ds_df[
            [
                "id",
                "name",
                "director_id",
                "created",
                "modified",
            ]
        ]

        # Insert data from the DataFrame into the model
        # Try the Query
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL query for Services...{self.misc.bcolors.ENDC}"
        )

        # Construct the SQL query
        sql = """
            BEGIN;
            INSERT INTO agencies_departmentalservice (
                old_id, created_at, updated_at, name, director_id
            ) VALUES (%s, %s, %s, %s, %s);
            COMMIT;
        """

        # Create an entry for each branch in the csv
        for index, dept_service in ds_columns.iterrows():
            if dept_service["name"] == "Data migration placeholder":
                continue
            print(
                f"{self.misc.bcolors.WARNING}Creating entry for {dept_service['name']}...{self.misc.bcolors.ENDC}"
            )

            # Get the new director_id if there was an old one
            if self.pd.isna(dept_service["director_id"]):
                new_director_id = None
            else:
                new_director_id = self.spms_get_user_by_old_id(
                    connection=connection,
                    cursor=cursor,
                    old_id=dept_service["director_id"],
                )

            try:
                # Start a transaction
                cursor = connection.cursor()

                cursor.execute(
                    sql,
                    (
                        dept_service["id"],  # old_id,
                        dept_service["created"],
                        dept_service["modified"],
                        dept_service["name"],
                        new_director_id,  # director id based on old pk
                    ),
                )

            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Service ({dept_service['name']}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Service ({dept_service['name']}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

        # TODO: At the end of all operations remove old_id & old_director_id from divisions table in django

        # Commit the changes and close the cursor and connection
        cursor.close()
        # connection.close()

    def spms_create_locations(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Locations...{self.misc.bcolors.ENDC}"
        )

        # Load the areas file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_area.csv"
            )
            areas_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establishing connection:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the current date and time
        current_datetime = dt.now()

        # Establish columns we want to use in df
        areas_columns = areas_df[
            [
                "id",
                "area_type",
                "name",
                # "source_id",
                # "northern_extent",
                # "mpoly",
            ]
        ]

        # Insert data from the DataFrame into the areas model
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL query...{self.misc.bcolors.ENDC}"
        )

        # Construct the SQL query
        sql = """
            BEGIN;
            INSERT INTO locations_area (
                old_id, created_at, updated_at, name, area_type
                
            ) VALUES (%s, %s, %s, %s, %s);
            COMMIT;
        """

        # , source_id, northern_extent, spatial_extent

        # Create an entry for each area in the csv
        for index, area in areas_columns.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating entry for Area {area['name']}...{self.misc.bcolors.ENDC}"
            )

            # Determins area_type based on name
            area_type = self.spms_determine_area_type(name=area["area_type"])

            try:
                # Start a transaction
                cursor = connection.cursor()

                new_name = (
                    "All NRM Regions"
                    if area["name"] == "All Regions" and area_type == "nrm"
                    else (
                        "All DBCA Regions"
                        if area["name"] == "All Regions" and area_type == "dbcaregion"
                        else (
                            "All DBCA Districts"
                            if area["name"] == "All DPaW Districts"
                            else area["name"]
                        )
                    )
                )
                cursor.execute(
                    sql,
                    (
                        area["id"],  # old_id,
                        current_datetime,
                        current_datetime,
                        new_name,
                        area_type,
                        # source_id,
                        # area["northern_extent"],  # northern extent
                        # area["mpoly"],  # renamed mpoly to spatial_extent
                    ),
                )

            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Area ({area['name']}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Area ({area['name']}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

        # TODO: At the end of all operations remove old_id & old_director_id from divisions table in django

        # Commit the changes and close the cursor and connection
        cursor.close()
        # connection.close()

    def spms_create_project_details(self, connection, cursor, old_id, new_id):
        pass

    def spms_create_external_project_details(self):
        pass

    def spms_create_student_project_details(self):
        pass

    def spms_create_projects(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Projects...{self.misc.bcolors.ENDC}"
        )
        # Establishing connection and fetching some necessary data:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the user with the name "jp" if it exists
        superuser_id = self.spms_get_superuser(connection=connection, cursor=cursor)

        # Get the current date and time
        current_datetime = dt.now()

        # ======================================================================================
        # CORE FUNCTIONS

        # Load the core functions file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "projects_corefunctionproject.csv"
            )
            cf_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        cf_columns = cf_df[["project_ptr_id"]]

        # ======================================================================================
        # STUDENT PROJECTS

        # Load the student projects file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "projects_studentproject.csv"
            )
            stup_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        studentp_columns = stup_df[
            [
                "project_ptr_id",
                "level",
                "organisation",
                "student_list_plain",
                "academic_list_plain",
                "academic_list_plain_no_affiliation",
            ]
        ]

        # ======================================================================================
        # SCIENCE PROJECTS

        # Load the science projects file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "projects_scienceproject.csv"
            )
            sp_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        sp_columns = sp_df[["project_ptr_id"]]

        # ======================================================================================
        # EXTERNAL PROJECTS

        # Load the external projects file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "projects_collaborationproject.csv"
            )
            ep_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        ep_columns = ep_df[
            [
                "project_ptr_id",
                "name",
                "budget",
                "staff_list_plain",
                "aims",
                "description",
            ]
        ]

        # ======================================================================================
        # PROJECTS FILE

        # Load the projects csv file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "projects_project.csv"
            )
            project_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        project_df = project_df[
            [
                # Base Details
                "id",  # old id
                "created",  # date
                "modified",  # date
                # "type",         # not necessary as we only have core functions
                "status",  # updated, completed, updating etc.
                "year",
                "number",
                "title",
                "comments",  # rename tro summary or description
                "tagline",
                "keywords",
                "start_date",
                "end_date",
                # FK with users
                "creator_id",  # user
                "modifier_id",  # user
                "project_owner_id",
                "data_custodian_id",
                "site_custodian_id",
                "team_list_plain",
                "supervising_scientist_list_plain",
                # FK &                 # Area Information
                "program_id",
                "output_program_id",
                "image",
                "area_list_dpaw_region",
                "area_list_dpaw_district",
                "area_list_ibra_imcra_region",
                "area_list_nrm_region",
            ]
        ]
        # "research_function_id",

        # ======================================================================================

        # Merge dfs where id matches project_ptr_id

        core_functions = self.pd.merge(
            project_df, cf_columns, left_on="id", right_on="project_ptr_id"
        )
        student_projects = self.pd.merge(
            project_df, studentp_columns, left_on="id", right_on="project_ptr_id"
        )
        science_projects = self.pd.merge(
            project_df, sp_columns, left_on="id", right_on="project_ptr_id"
        )
        external_projects = self.pd.merge(
            project_df, ep_columns, left_on="id", right_on="project_ptr_id"
        )

        # Try the Query
        print(
            f"{self.misc.bcolors.WARNING}Beginning SQL queries for projects...{self.misc.bcolors.ENDC}"
        )

        # ======================================================================================

        # Create a base entry for each project in the csv
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Setting Base Project details...{self.misc.bcolors.ENDC}"
        )

        self.spms_project_setter(
            type="core_function",
            dataframe=core_functions,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            superuser_id=superuser_id,
        )

        self.spms_project_setter(
            type="science",
            dataframe=science_projects,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            superuser_id=superuser_id,
        )

        self.spms_project_setter(
            type="student",
            dataframe=student_projects,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            superuser_id=superuser_id,
        )

        self.spms_project_setter(
            type="external",
            dataframe=external_projects,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            superuser_id=superuser_id,
        )

        # ======================================================================================

        # Create secondary entries for each project in the csv

        # image_link, current_datetime, project_id, uploader

        # self.spms_create_project_image(
        #     connection=connection,
        #     cursor=cursor,
        #     current_datetime=current_datetime,
        #     project_id=project_id,
        #     uploader=superuser_id,
        # )

        # project_key_members_sql = """
        #     BEGIN;
        #     INSERT INTO projects_projectdetail; (
        #         created_at,
        #         udpated_at,
        #         project_id,
        #         creator_id,
        #         modifier_id,
        #         project_owner_id,
        #         data_custodian_id,
        #         team_list_plain,
        #         supervising_scientist_list_plain
        #     ) VALUES (%s, %s, %s, %s, %s);
        #     COMMIT;
        # """

        # project_further_details_sql = """
        #     BEGIN;
        #     INSERT INTO projects_projectdetail; (
        #         research_function_id,
        #         output_program_id,
        #         area_list_dpaw_region,
        #         area_list_dpaw_district,
        #         area_list_ibra_imcra_region,
        #         area_list_nrm_region,

        #     ) VALUES (%s, %s, %s, %s, %s);
        #     COMMIT;
        # """
        # ======================================================================================

        # ======================================================================================

        # Create entries specific to student projects

        # Create entries specific to external projects

        # NOTE: Science and core function projects do not require extra data

        # ======================================================================================

        cursor.close()
        # connection.close()

    def spms_get_business_area_of_project_lead(
        self, project_lead_id, cursor, connection
    ):
        try:
            # Use a SQL SELECT query to retrieve the business_area_id based on project_lead_id
            query = "SELECT business_area_id FROM users_userwork WHERE user_id = %s"
            cursor.execute(query, (project_lead_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                # If the result is not empty, return the business_area_id
                return result[0]
            else:
                # If no result is found, you may choose to return a default value or raise an exception
                # You can modify this part based on your requirements
                return None  # or raise an exception indicating no result found

        except Exception as e:
            # Handle exceptions (e.g., database connection issues, SQL errors)
            print(f"Error in spms_get_business_area_of_project_lead: {e}")
            return None  # or raise an exception

        finally:
            # Make sure to commit the changes and close the cursor
            connection.commit()
            cursor.close()

    def spms_project_setter(
        self, type, dataframe, cursor, connection, current_datetime, superuser_id
    ):
        # Construct the SQL query for base
        project_sql = """
            BEGIN;
            INSERT INTO projects_project (
                old_id, 
                created_at, 
                updated_at,
                kind, 
                status, 
                year, 
                number, 
                title, 
                description, 
                tagline, 
                keywords,
                start_date, 
                end_date,
                business_area_id                 
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        remote_sensing_ba = self.spms_get_ba_by_old_program_id(
            connection=connection, cursor=cursor, old_id=19
        )

        for index, project in dataframe.iterrows():
            proj_title = self.spms_check_if_project_with_name_exists(
                cursor=cursor, name=project["title"]
            )

            print(
                f"{self.misc.bcolors.WARNING}Creating {type} entry for {proj_title}...{self.misc.bcolors.ENDC}"
            )

            print(f"Getting id of business area belong to project {proj_title}")
            if self.pd.isna(project["program_id"]):
                project_lead_id = self.spms_get_user_by_old_id(
                    connection=connection, cursor=cursor, old_id=project["creator_id"]
                )
                business_area_id = self.spms_get_business_area_of_project_lead(
                    connection=connection,
                    cursor=cursor,
                    project_lead_id=project_lead_id,
                )
            else:
                business_area_id = self.spms_get_ba_by_old_program_id(
                    cursor=cursor, connection=connection, old_id=project["program_id"]
                )

            start_date = (
                project["start_date"]
                if not self.pd.isna(project["start_date"])
                else project["created"]
            )

            if project["status"] == "closure requested":
                new_status = "closure_requested"
            elif project["status"] == "final update":
                new_status = "final_update"
            else:
                new_status = project["status"]
            try:
                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    project_sql,
                    (
                        project["id"],  # old_id,
                        project["created"],  # created at
                        project["modified"],  # updated at
                        type,  # kind
                        new_status,
                        project["year"],
                        project["number"],
                        proj_title,
                        (
                            None
                            if self.pd.isna(project["comments"])
                            else project["comments"]
                        ),  # description
                        (
                            None
                            if self.pd.isna(project["tagline"])
                            else project["tagline"]
                        ),
                        (
                            ""
                            if self.pd.isna(project["keywords"])
                            else project["keywords"]
                        ),
                        start_date,
                        # else None,
                        (
                            project["end_date"]
                            if not self.pd.isna(project["end_date"])
                            else start_date
                        ),
                        # else None,
                        (
                            remote_sensing_ba
                            if str(project["year"]) == "2022"
                            and str(project["number"]) == "18"
                            else business_area_id
                        ),  # address a project without ba set
                        # image_id,
                    ),
                )
            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating {type} Project ({proj_title}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}{type} ({proj_title}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # Set the project image
            if not self.pd.isna(project["image"]):
                proj_id_for_image = self.spms_get_project_by_old_id(
                    connection=connection, cursor=cursor, old_id=project["id"]
                )
                image_id = self.spms_create_project_image(
                    image_file=project["image"],
                    current_datetime=current_datetime,
                    connection=connection,
                    cursor=cursor,
                    project_id=proj_id_for_image,
                    uploader=superuser_id,
                    image_link=f"http://scienceprojects.dbca.wa.gov.au/media/{project['image']}",
                )

            self.misc.nls(
                f"{self.misc.bcolors.WARNING}Setting Additional Project details...{self.misc.bcolors.ENDC}"
            )

            self.spms_project_details_setter(
                connection=connection,
                cursor=cursor,
                current_datetime=current_datetime,
                df_project=project,
            )  # Creates additional info for all projects

            if type == "external":
                self.misc.nls(
                    f"{self.misc.bcolors.WARNING}Setting External Project details ({project['id']})...{self.misc.bcolors.ENDC}"
                )
                self.spms_external_project_setter(
                    connection=connection,
                    cursor=cursor,
                    current_datetime=current_datetime,
                    df_project=project,
                )
            if type == "student":
                self.misc.nls(
                    f"{self.misc.bcolors.WARNING}Setting Student Project details ({project['id']})...{self.misc.bcolors.ENDC}"
                )
                self.spms_student_project_setter(
                    connection=connection,
                    cursor=cursor,
                    current_datetime=current_datetime,
                    df_project=project,
                )

            connection.commit()
        # connection.close()
        # cursor.close()

    def spms_set_project_leaders(self):
        # Title
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Setting leaders for projects...{self.misc.bcolors.ENDC}"
        )

        # Establishing connection and fetching necessary data
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        try:
            # SQL query to fetch project details and their corresponding members
            cursor.execute(
                """
                SELECT pd.id AS project_id, pd.creator_id AS creator_id, pd.owner_id AS owner_id,
                pm.id AS member_id, pm.user_id AS member_user_id, pm.is_leader AS is_leader, pm.role AS role
                FROM projects_projectdetail pd
                LEFT JOIN projects_projectmember pm ON pd.id = pm.project_id
                ORDER BY pd.id, pm.id;
                """
            )

            # Initialize variables to keep track of the current project and its members
            current_project_id = None
            members = []

            for row in cursor.fetchall():
                (
                    project_id,
                    creator_id,
                    owner_id,
                    member_id,
                    member_user_id,
                    is_leader,
                    role,
                ) = row

                # Skip ineligible members with roles 'externalcol', 'group', 'externalpeer', 'consulted', and 'student'
                if role in [
                    "externalcol",
                    "group",
                    "externalpeer",
                    "consulted",
                    "student",
                ]:
                    continue

                # Check if we have moved to a new project
                if current_project_id != project_id:
                    # Determine if there are existing leaders in the project
                    existing_leaders = [
                        member for member in members if member["is_leader"]
                    ]

                    # Check if there are no leaders in the project
                    if not existing_leaders:
                        # Check for members with roles "supervising" or "academicsuper"
                        supervising_members = [
                            member
                            for member in members
                            if member["role"] in ["supervising", "academicsuper"]
                        ]

                        # Set the first member with role "supervising" or "academicsuper" as the leader
                        if supervising_members:
                            first_supervising_member = supervising_members[0]
                            cursor.execute(
                                """
                                UPDATE projects_projectmember
                                SET is_leader = TRUE,
                                    position = 1  -- Set the position to 1 for the leader
                                WHERE id = %s;
                                """,
                                (first_supervising_member["member_id"],),
                            )
                        else:
                            # Check if creator or owner is in the project members
                            creator_or_owner_members = [
                                member
                                for member in members
                                if member["member_user_id"] in {creator_id, owner_id}
                            ]

                            # Set the project owner as the leader if available, else set the creator
                            if any(
                                member["member_user_id"] == owner_id
                                for member in creator_or_owner_members
                            ):
                                owner_member = next(
                                    (
                                        member
                                        for member in creator_or_owner_members
                                        if member["member_user_id"] == owner_id
                                    ),
                                    None,
                                )
                                if owner_member:
                                    cursor.execute(
                                        """
                                        UPDATE projects_projectmember
                                        SET is_leader = TRUE,
                                            position = 1  -- Set the position to 1 for the leader
                                        WHERE id = %s;
                                        """,
                                        (owner_member["member_id"],),
                                    )
                            elif any(
                                member["member_user_id"] == creator_id
                                for member in creator_or_owner_members
                            ):
                                creator_member = next(
                                    (
                                        member
                                        for member in creator_or_owner_members
                                        if member["member_user_id"] == creator_id
                                    ),
                                    None,
                                )
                                if creator_member:
                                    cursor.execute(
                                        """
                                        UPDATE projects_projectmember
                                        SET is_leader = TRUE,
                                            position = 1  -- Set the position to 1 for the leader
                                        WHERE id = %s;
                                        """,
                                        (creator_member["member_id"],),
                                    )

                            else:
                                # Set the first member as the leader if no eligible members found
                                if members:
                                    first_member = members[0]
                                    cursor.execute(
                                        """
                                        UPDATE projects_projectmember
                                        SET is_leader = TRUE,
                                            position = 1  -- Set the position to 1 for the leader
                                        WHERE id = %s;
                                        """,
                                        (first_member["member_id"],),
                                    )

                    # Reset the members list for the next project
                    members = []

                # Add the current row to the members list
                members.append(
                    {
                        "member_id": member_id,
                        "member_user_id": member_user_id,
                        "is_leader": is_leader,
                        "role": role,
                    }
                )

                # Update the current_project_id for comparison in the next iteration
                current_project_id = project_id

            connection.commit()
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Successfully set leaders for projects.{self.misc.bcolors.ENDC}"
            )

        except Exception as e:
            connection.rollback()
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error occurred while setting leaders for projects: {e}{self.misc.bcolors.ENDC}"
            )
        finally:
            cursor.close()
            connection.close()

    def spms_project_members_setter(self):
        # Title
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Memberships for Projects...{self.misc.bcolors.ENDC}"
        )

        # Establishing connection and fetching some necessary data:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the current date and time
        current_datetime = dt.now()

        # Open the team membership csv and save as a separate dataframe
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "projects_projectmembership.csv"
            )
            membership_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        membership_df = membership_df[
            [
                "id",  # old_id
                "project_id",  # old_project_id
                "user_id",  # old_user_id
                "role",  # old_role_number
                "time_allocation",
                # "position", = position column appears to be dropped in latest data
                "comments",
                "short_code",
            ]
        ]

        # Establish how roles will be remapped
        roles = [
            {1: "supervising"},
            {2: "research"},
            {3: "technical"},
            {4: "externalpeer"},
            {5: "consulted"},
            {6: "academicsuper"},
            {7: "student"},
            {8: "externalcol"},
            {9: "group"},
        ]

        # Helper function to reallocate int values to roles
        def set_new_role(old_role_number):
            for role in roles:
                if old_role_number in role:
                    return role[old_role_number]
            return None  # Handle the case when no matching role is found

        # Construct the SQL query for base
        membership_sql = """
            BEGIN;
            INSERT INTO projects_projectmember (
                old_id, 
                created_at, 
                updated_at,
                project_id, 
                user_id, 
                role, 
                time_allocation, 
                position, 
                short_code, 
                is_leader,
                comments               
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        # Execute sql per row
        for index, member in membership_df.iterrows():
            # proj_title = self.spms_check_if_project_with_name_exists(
            #     cursor=cursor, name=project["title"]
            # )

            print(
                f"{self.misc.bcolors.WARNING}Creating membership entry for {member['user_id']}...{self.misc.bcolors.ENDC}"
            )

            # Get new values related to each membership entry
            old_id = member["id"]
            new_proj_id = self.spms_get_project_by_old_id(
                old_id=member["project_id"], cursor=cursor, connection=connection
            )
            new_user_id = self.spms_get_user_by_old_id(
                old_id=member["user_id"], cursor=cursor, connection=connection
            )
            new_role = set_new_role(member["role"])

            new_time_allocation = (
                0
                if self.pd.isna(member["time_allocation"])
                else member["time_allocation"]
            )
            new_position = (
                100
                # if self.pd.isna(member["position"]) else member["position"]
            )
            is_leader_val = False
            try:
                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    membership_sql,
                    (
                        old_id,  # old_id,
                        current_datetime,  # created at
                        current_datetime,  # updated at
                        new_proj_id,  # kind
                        new_user_id,
                        new_role,
                        new_time_allocation,
                        # 100,
                        new_position,
                        (
                            None
                            if self.pd.isna(member["short_code"])
                            else member["short_code"]
                        ),
                        is_leader_val,
                        (
                            None
                            if self.pd.isna(member["comments"])
                            else member["comments"]
                        ),
                    ),
                )
            except psycopg2.IntegrityError as e:
                error_message = str(e)
                if "duplicate key value violates unique constraint" in error_message:
                    print(f"Duplicate key violation: {error_message}")
                    connection.rollback()
                    continue
                else:
                    raise e

            except Exception as e:
                print(old_id)

                print(current_datetime)
                print(current_datetime)
                print(new_proj_id)
                print(new_user_id)
                print(new_role)
                print(new_time_allocation)
                print(new_position)
                print(
                    None if self.pd.isna(member["short_code"]) else member["short_code"]
                )
                print(None if self.pd.isna(member["comments"]) else member["comments"])

                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Project Team Member (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN} Project Member (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )
                connection.commit()

            # finally:
            #     connection.commit()
            # connection.close()
            # cursor.close()

    def spms_project_areas_setter(self):
        # Title
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Setting Project Areas...{self.misc.bcolors.ENDC}"
        )

        # Establishing connection and fetching some necessary data:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the current date and time
        current_datetime = dt.now()

        # Open the team membership csv and save as a separate dataframe
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "projects_project_areas.csv"
            )
            project_area_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        project_area_df = project_area_df[
            [
                "id",  # old_id
                "project_id",  # old_project_id
                "area_id",  # old_area_id
            ]
        ]

        # Construct the SQL query for base (updates areas on conflict)
        project_area_sql = """
            BEGIN;
            INSERT INTO projects_projectarea (
                created_at, 
                updated_at,
                project_id, 
                areas
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE
            SET areas = excluded.areas;
            COMMIT;
        """

        # area_id
        new_df = self.pd.DataFrame(columns=["project_id", "areas"])

        # Initialize an empty list to hold the new rows
        new_rows = []

        # Generate rows
        cursor = connection.cursor()
        for index, projectarea in project_area_df.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating area entry for Project Area: {projectarea['id']}...{self.misc.bcolors.ENDC}"
            )
            # Get new values related to each project area entry
            old_id = int(projectarea["id"])
            new_proj_id = self.spms_get_project_by_old_id(
                old_id=projectarea["project_id"], cursor=cursor, connection=connection
            )
            new_area_id = self.spms_get_area_by_old_id(
                old_id=projectarea["area_id"], cursor=cursor, connection=connection
            )

            # Check if the new_proj_id is already in the new_df
            # Check if the new_proj_id is already in the new_df
            existing_row = new_df.loc[new_df["project_id"] == new_proj_id]

            if not existing_row.empty:
                # Get the existing 'areas' value (should be a set or convert to a set if it's a single int)
                existing_areas = existing_row["areas"].values[0]
                if not isinstance(existing_areas, set):
                    existing_areas = {existing_areas}

                # Add the new_area_id to the existing set
                existing_areas.add(new_area_id)

                # Update the 'areas' value in the existing row
                new_df.loc[new_df["project_id"] == new_proj_id, "areas"] = [
                    existing_areas
                ]
            else:
                # Create a new row with the 'project_id' and an empty set for 'areas'
                new_row = {"project_id": new_proj_id, "areas": [{new_area_id}]}
                new_df = self.pd.concat([new_df, self.pd.DataFrame(new_row)])

        # Reset the index of the DataFrame
        new_df.reset_index(drop=True, inplace=True)

        try:
            # Start a transaction
            cursor = connection.cursor()
            for index, row in new_df.iterrows():
                cursor.execute(
                    project_area_sql,
                    (
                        current_datetime,  # created at
                        current_datetime,  # updated at
                        row["project_id"],
                        list(row["areas"]),  # areas as a list of primary keys
                    ),
                )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error creating Project Area: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Print the complete traceback information
            traceback_str = traceback.format_exc()
            print(traceback_str)

            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN} Project Area Created!{self.misc.bcolors.ENDC}"
            )

        finally:
            connection.commit()

        # Create empty array entries for projects without areas to avoid null values
        # Fetch all project IDs from the Project model
        cursor.execute("SELECT id FROM projects_project")
        all_project_ids = [row[0] for row in cursor.fetchall()]

        # Fetch all project IDs from the ProjectArea model
        cursor.execute("SELECT project_id FROM projects_projectarea")
        existing_project_area_ids = [row[0] for row in cursor.fetchall()]

        # Identify projects without ProjectArea entries
        projects_without_project_area = set(all_project_ids) - set(
            existing_project_area_ids
        )

        # Create empty entries for projects without ProjectArea entries
        for project_id in projects_without_project_area:
            print(
                f"{self.misc.bcolors.WARNING}Creating empty Project Area entry for Project ID: {project_id}...{self.misc.bcolors.ENDC}"
            )
            try:
                # Start a transaction
                cursor.execute(
                    project_area_sql,
                    (
                        current_datetime,  # created at
                        current_datetime,  # updated at
                        project_id,
                        [],  # Empty list for areas as there are no areas
                    ),
                )
            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating empty Project Area: {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

        # Commit the transaction for empty entries
        connection.commit()

    def spms_project_comments_setter(self, projects_df, cursor, connection):
        pass
        # # Title
        # self.misc.nls(
        #     f"{self.misc.bcolors.OKBLUE}Setting Project Comments...{self.misc.bcolors.ENDC}"
        # )

        # # Establishing connection and fetching some necessary data:
        # (
        #     cursor,
        #     connection,
        # ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        # connection.autocommit = False

        # # Get the current date and time
        # current_datetime = dt.now()

        # # Open the team membership csv and save as a separate dataframe
        # try:
        #     file_path = self.os.path.join(
        #         self.file_handler.clean_directory, "projects_project_areas.csv"
        #     )
        #     project_area_df = self.file_handler.read_csv_and_prepare_df(file_path)
        # except Exception as e:
        #     self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        # else:
        #     print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # # Establish columns we want to use in df
        # project_area_df = project_area_df[
        #     [
        #         "id",  # old_id
        #         "project_id",  # old_project_id
        #         "area_id",  # old_area_id
        #     ]
        # ]

        # # Construct the SQL query for base
        # project_area_sql = """
        #     BEGIN;
        #     INSERT INTO projects_projectarea (
        #         created_at,
        #         updated_at,
        #         old_id,
        #         project_id,
        #         area_id
        #     ) VALUES (%s, %s, %s, %s, %s);
        #     COMMIT;
        # """

        # # Execute sql per row
        # for index, projectarea in project_area_df.iterrows():
        #     print(
        #         f"{self.misc.bcolors.WARNING}Creating area entry for Project Area: {projectarea['id']}...{self.misc.bcolors.ENDC}"
        #     )

        #     # Get new values related to each project area entry
        #     old_id = int(projectarea["id"])
        #     new_proj_id = self.spms_get_project_by_old_id(
        #         old_id=projectarea["project_id"], cursor=cursor, connection=connection
        #     )
        #     new_area_id = self.spms_get_area_by_old_id(
        #         old_id=projectarea["area_id"], cursor=cursor, connection=connection
        #     )

        #     try:
        #         # Start a transaction
        #         cursor = connection.cursor()
        #         cursor.execute(
        #             project_area_sql,
        #             (
        #                 current_datetime,  # created at
        #                 current_datetime,  # updated at
        #                 old_id,  # old_id,
        #                 new_proj_id,  #
        #                 new_area_id,
        #             ),
        #         )
        #     except Exception as e:
        #         print(old_id)
        #         print(current_datetime)
        #         print(current_datetime)
        #         print(new_proj_id)
        #         print(new_area_id)
        #         self.misc.nli(
        #             f"{self.misc.bcolors.FAIL}Error creating Project Area (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
        #         )
        #         # Print the complete traceback information
        #         traceback_str = traceback.format_exc()
        #         print(traceback_str)

        #         # Rollback the transaction
        #         connection.rollback()

        #     else:
        #         self.misc.nls(
        #             f"{self.misc.bcolors.OKGREEN} Project Area (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
        #         )

        #     finally:
        #         connection.commit()
        #         connection.close()
        #         cursor.close()

    def spms_project_details_setter(
        self, connection, cursor, current_datetime, df_project
    ):
        # Construct the SQL query for project details
        project_detail_sql = """
            BEGIN;
            INSERT INTO projects_projectdetail (
                created_at,
                updated_at,
                project_id,
                creator_id,
                modifier_id,
                owner_id,
                data_custodian_id,
                site_custodian_id,
                old_output_program_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        # research_function_id,

        # service_id,

        # area list and superivsing scientist list removed

        print(
            f"{self.misc.bcolors.WARNING}Creating Details entry for {df_project['title']}...{self.misc.bcolors.ENDC}"
        )

        try:
            created_at = current_datetime
            updated_at = current_datetime
            new_project_id = self.spms_get_project_by_old_id(
                old_id=df_project["id"],
                cursor=cursor,
                connection=connection,
            )
            new_creator_id = self.spms_get_user_by_old_id(
                old_id=df_project["creator_id"],
                cursor=cursor,
                connection=connection,
            )
            new_modifier_id = self.spms_get_user_by_old_id(
                old_id=df_project["modifier_id"],
                cursor=cursor,
                connection=connection,
            )
            new_project_owner_id = self.spms_get_user_by_old_id(
                old_id=df_project["project_owner_id"],
                cursor=cursor,
                connection=connection,
            )
            new_data_custodian_id = (
                new_creator_id
                if self.pd.isna(df_project["data_custodian_id"])
                else self.spms_get_user_by_old_id(
                    old_id=df_project["data_custodian_id"],
                    cursor=cursor,
                    connection=connection,
                )
            )
            new_site_custodian_id = (
                None
                if self.pd.isna(df_project["site_custodian_id"])
                else self.spms_get_user_by_old_id(
                    old_id=df_project["site_custodian_id"],
                    cursor=cursor,
                    connection=connection,
                )
            )
            # new_research_function_id = (
            #     None
            #     if self.pd.isna(df_project["research_function_id"])
            #     else self.spms_get_research_function_by_old_id(
            #         old_id=df_project["research_function_id"],
            #         cursor=cursor,
            #         connection=connection,
            #     )
            # )

            # new_service_id = (
            #     None
            #     if self.pd.isna(df_project["service_id"])
            #     else self.spms_get_service_by_old_id(
            #         old_id=df_project["service_id"],
            #         cursor=cursor,
            #         connection=connection,
            #     )
            # )

            old_output_program_id = (
                None
                if self.pd.isna(df_project["output_program_id"])
                else int(df_project["output_program_id"])
            )

            # if new_research_function_id == None:
            #     filename = "ProjectsWithNoRFs.txt"
            #     rfs_dir = os.path.join(self.django_project_path, filename)
            #     if not os.path.exists(rfs_dir):
            #         with open(rfs_dir, "w") as file:
            #             pass
            #     # Read existing content from the file
            #     with open(rfs_dir, "r", encoding="utf-8") as file:
            #         existing_content = file.read()
            #     # Check if the content already exists
            #     if (
            #         f"https://scienceprojects-test.dbca.wa.gov.au/projects/{new_project_id}\n"
            #         not in existing_content
            #     ):
            #         # Get the project lead nasme
            #         lead_name = self.spms_get_user_name_old_id(
            #             connection=connection,
            #             cursor=cursor,
            #             old_id=df_project["project_owner_id"],
            #         )
            #         title = df_project["title"]
            #         status = df_project["status"]
            #         # Get the project title
            #         # project_title = self.spms_get_project_title_by_
            #         # Append to the file
            #         with open(rfs_dir, "a", encoding="utf-8") as file:
            #             file.write(
            #                 f"{lead_name}\n{status}\n{title}\nhttps://scienceprojects-test.dbca.wa.gov.au/projects/{new_project_id}\n\n"
            #             )
            #     else:
            #         print("Content already exists in the file.")

            # Start a transaction
            cursor = connection.cursor()
            cursor.execute(
                project_detail_sql,
                (
                    created_at,
                    updated_at,  # creator_id
                    new_project_id,  # modifier_id
                    new_creator_id,  # new user id
                    new_modifier_id,
                    new_project_owner_id,
                    new_data_custodian_id,
                    new_site_custodian_id,
                    # new_service_id,
                    old_output_program_id,
                ),
                # new_research_function_id,
            )
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error Creating Details entry for {df_project['title']}: {str(e)}{self.misc.bcolors.ENDC}"
            )

            # Print the complete traceback information
            traceback_str = traceback.format_exc()
            print(traceback_str)
            self.misc.nli(
                f"\
                    {created_at}\n,\
                    {updated_at}\n,  \
                    {new_project_id}\n,  \
                    {new_creator_id}\n,  \
                    {new_modifier_id}\n,\
                    {new_project_owner_id}\n,\
                    {new_data_custodian_id}\n,\
                    {new_site_custodian_id}\n,\
                    {old_output_program_id}\n,"
            )
            # {new_research_function_id}\n, \
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN} Details entry for {df_project['title']} Created!{self.misc.bcolors.ENDC}"
            )

        finally:
            connection.commit()

    def spms_external_project_setter(
        self,
        connection,
        cursor,
        current_datetime,
        df_project,
    ):
        # Construct the SQL query for external project details
        external_details_sql = """
            BEGIN;
            INSERT INTO projects_externalprojectdetails (
                project_id,
                collaboration_with,
                budget,
                description,
                aims,
                old_id
            ) VALUES (%s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        # area list and superivsing scientist list removed

        print(
            f"{self.misc.bcolors.WARNING}Creating EXTERNAL Details entry for {df_project['title']}...{self.misc.bcolors.ENDC}"
        )

        try:
            new_project_id = self.spms_get_project_by_old_id(
                old_id=df_project["id"],
                cursor=cursor,
                connection=connection,
            )
            collaboration_with = (
                None if self.pd.isna(df_project["name"]) else df_project["name"]
            )
            budget = (
                None if self.pd.isna(df_project["budget"]) else df_project["budget"]
            )
            description = (
                None
                if self.pd.isna(df_project["description"])
                else df_project["description"]
            )
            aims = None if self.pd.isna(df_project["aims"]) else df_project["aims"]
            old_id = int(df_project["id"])

            # Start a transaction
            cursor = connection.cursor()

            # Skip empties
            if not (
                collaboration_with == None
                and description == None
                and budget == None
                and aims == None
            ):
                cursor.execute(
                    external_details_sql,
                    (
                        new_project_id,
                        collaboration_with,
                        budget,
                        description,
                        aims,
                        old_id,
                    ),
                )
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error Creating EXTERNAL Details entry for {df_project['title']}: {str(e)}{self.misc.bcolors.ENDC}"
            )

            # Print the complete traceback information
            traceback_str = traceback.format_exc()
            print(traceback_str)
            self.misc.nli(
                f"\
                    {new_project_id}\n,\
                    {collaboration_with}\n,  \
                    {budget}\n,  \
                    {description}\n,  \
                    {aims}\n,\
                    {old_id}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN} EXTERNAL Details entry for {df_project['title']} Created!{self.misc.bcolors.ENDC}"
            )

        finally:
            connection.commit()

    def spms_student_project_setter(
        self,
        connection,
        cursor,
        current_datetime,
        df_project,
    ):
        # Construct the SQL query for student project details
        student_details_sql = """
            BEGIN;
            INSERT INTO projects_studentprojectdetails (
                project_id,
                level,
                organisation,
                old_id
            ) VALUES (%s, %s, %s, %s);
            COMMIT;
        """

        # area list and superivsing scientist list removed

        print(
            f"{self.misc.bcolors.WARNING}Creating STUDENT Details entry for {df_project['title']}...{self.misc.bcolors.ENDC}"
        )

        def determine_new_level(old_level):
            if self.pd.isna(old_level):
                return None
            old_level = int(old_level)
            switch_dict = {
                0: "phd",
                1: "msc",
                2: "honours",
                3: "fourth_year",
                4: "third_year",
                5: "undergrad",
                6: "pd",
            }

            new_level = switch_dict.get(old_level, None)
            print(f"{old_level} to {new_level}")

            return new_level

        try:
            new_project_id = self.spms_get_project_by_old_id(
                old_id=df_project["id"],
                cursor=cursor,
                connection=connection,
            )
            level = determine_new_level(df_project["level"])
            organisation = (
                None
                if self.pd.isna(df_project["organisation"])
                else df_project["organisation"]
            )
            old_id = int(df_project["id"])

            # Start a transaction
            cursor = connection.cursor()
            cursor.execute(
                student_details_sql,
                (
                    new_project_id,
                    level,
                    organisation,
                    old_id,
                ),
            )
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error Creating STUDENT Details entry for {df_project['title']}: {str(e)}{self.misc.bcolors.ENDC}"
            )

            # Print the complete traceback information
            traceback_str = traceback.format_exc()
            print(traceback_str)
            self.misc.nli(
                f"\
                    {new_project_id}\n,\
                    {level}\n,  \
                    {organisation}\n,  \
                    {old_id}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN} STUDENT Details entry for {df_project['title']} Created!{self.misc.bcolors.ENDC}"
            )

        finally:
            connection.commit()

    def spms_create_project_documents(self):
        # Title
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Documents for Projects...{self.misc.bcolors.ENDC}"
        )

        # Establishing connection and fetching some necessary data:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the current date and time
        current_datetime = dt.now()

        # Open the documents_document csv and save as a separate dataframe
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "documents_document.csv"
            )
            project_document_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df for documents_document
        project_document_df = project_document_df[
            [
                "id",  # old_id
                "project_id",  # old_project_id
                "creator_id",  # old_creator_id
                "modifier_id",  # old_modifier_id
                "created",  # created_at
                "modified",  # updated_at
                "status",  # old_status
                "pdf",  # old_pdf
            ]
        ]

        # Establish how status will be remapped (if necessary)

        # Helper function to reallocate values to status based on statuses dict
        def set_new_status(old_status):
            if old_status == None:
                return "new"
            else:
                # if old_status == "new" and created < updated:
                #         return "revising"
                return old_status
            # statuses = [
            #     # For brand new docs
            #     {"new": "new"},  # "New document"
            #     # For when a doc is sent back for revision or a change made to new doc
            #     {"revising": "revising"},  # Revising
            #     # For when a revised/new doc is in review
            #     {"inreview": "inreview"},  # In Review
            #     # For when the revised doc is approved by reviewer, and finally sent to directorate
            #     {"inapproval": "inapproval"},  # Seeking Approval
            #     # When a doc receives final approval. Only progress reports in this state added to report
            #     {"approved": "approved"},  # Approved
            # ]

            # for item in statuses:
            #     if old_status in status_dict:
            #         new_status = status_dict[old_status]
            #         if new_status == "new" and created < updated:
            #             return "revising"
            #         return new_status

            # print(old_status)
            # return None  # Handle the case when no matching status is found

        # Joining on id, to create new dataframes for each document file.
        # ======================================================================================
        # CONCEPT PLANS

        # Open file, create df, and join on id for concept plans
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "documents_conceptplan.csv"
            )
            concept_plan_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        concepts_columns = concept_plan_df[
            [
                "document_ptr_id",
                "summary",
                "outcome",
                "collaborations",
                "strategic",
                "staff",
                "budget",
                "background",
            ]
        ]

        # ======================================================================================
        # PROJECT PLANS

        # Open file, create df, and join on id for project plans
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "documents_projectplan.csv"
            )
            project_plan_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        project_plan_columns = project_plan_df[
            [
                "document_ptr_id",
                "related_projects",
                "background",
                "aims",
                "outcome",
                "knowledge_transfer",
                "project_tasks",
                "references",
                "methodology",
                "bm_endorsement",
                "involves_plants",
                "no_specimens",
                "hc_endorsement",
                "involves_animals",
                "ae_endorsement",
                "data_management",
                "data_manager_endorsement",
                "operating_budget",
                "operating_budget_external",
            ]
        ]

        # ======================================================================================
        # PROGRESS REPORTS

        # Open file, create df, and join on id for progress reports
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "documents_progressreport.csv"
            )
            progressreport_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        progress_report_columns = progressreport_df[
            [
                "document_ptr_id",
                "is_final_report",
                "year",
                "report_id",
                "context",
                "aims",
                "progress",
                "implications",
                "future",
            ]
        ]

        # ======================================================================================
        # STUDENT REPORTS

        # Open file, create df, and join on id for studentreport
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "documents_studentreport.csv"
            )
            student_report_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        student_report_columns = student_report_df[
            [
                "document_ptr_id",
                "year",
                "progress_report",
                "report_id",
            ]
        ]

        # ======================================================================================
        # PROJECT CLOSURES

        # Open file, create df, and join on id for projectclosure
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "documents_projectclosure.csv"
            )
            project_closure_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        project_closure_columns = project_closure_df[
            [
                "document_ptr_id",
                "scientific_outputs",
                "knowledge_transfer",
                "data_location",
                "hardcopy_location",
                "backup_location",
                "goal",
                "reason",
            ]
        ]

        # ======================================================================================
        # MERGE DATAFRAMES

        concept_plans = self.pd.merge(
            project_document_df,
            concepts_columns,
            left_on="id",
            right_on="document_ptr_id",
        )
        project_plans = self.pd.merge(
            project_document_df,
            project_plan_columns,
            left_on="id",
            right_on="document_ptr_id",
        )
        progress_reports = self.pd.merge(
            project_document_df,
            progress_report_columns,
            left_on="id",
            right_on="document_ptr_id",
        )
        student_reports = self.pd.merge(
            project_document_df,
            student_report_columns,
            left_on="id",
            right_on="document_ptr_id",
        )
        project_closures = self.pd.merge(
            project_document_df,
            project_closure_columns,
            left_on="id",
            right_on="document_ptr_id",
        )

        # ======================================================================================

        # As original file does not list document type, we must create the document in each sub function,
        # then create the document type details in the subfunction.

        # Run each sub-function with the relevant dataframes to create base doc and extra information per type

        self.spms_concept_plan_setter(
            dataframe=concept_plans,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            set_new_status=set_new_status,
        )

        self.spms_project_plan_setter(
            dataframe=project_plans,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            set_new_status=set_new_status,
        )

        self.spms_progress_report_setter(
            dataframe=progress_reports,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            set_new_status=set_new_status,
        )

        self.spms_student_report_setter(
            dataframe=student_reports,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            set_new_status=set_new_status,
        )

        self.spms_project_closure_setter(
            dataframe=project_closures,
            cursor=cursor,
            connection=connection,
            current_datetime=current_datetime,
            set_new_status=set_new_status,
        )

        # ===============================
        cursor.close()
        connection.close()

    def spms_concept_plan_setter(
        self,
        dataframe,
        cursor,
        connection,
        current_datetime,
        set_new_status,
    ):
        # Title
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Concept Plans for Projects...{self.misc.bcolors.ENDC}"
        )

        # Construct the SQL query for conceptplans

        concept_plan_sql = """
            BEGIN;
            INSERT INTO documents_conceptplan (
                document_id, 
                project_id,
                background, 
                aims,
                outcome, 
                collaborations, 
                strategic_context, 
                staff_time_allocation, 
                budget            
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        # Construct SQL for base document
        base_sql = """
            BEGIN;
            INSERT INTO documents_projectdocument (
                old_id,    
                creator_id,
                modifier_id,     
                created_at, 
                updated_at,
                project_id, 
                status, 
                kind,
                pdf_generation_in_progress,
                directorate_approval_granted,
                project_lead_approval_granted,
                business_area_lead_approval_granted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        #                 pdf

        # Execute sql per row
        for index, concept_plan in dataframe.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating Concept Plan Base({concept_plan['id']})...{self.misc.bcolors.ENDC}"
            )

            # Get new values related to each base document entry
            old_id = int(concept_plan["id"])
            created_at = concept_plan["created"]
            updated_at = (
                concept_plan["created"]
                if not self.pd.isna(concept_plan["created"])
                and self.pd.isna(concept_plan["modified"])
                else (
                    concept_plan["modified"]
                    if not self.pd.isna(concept_plan["modified"])
                    else current_datetime
                )
            )
            status = set_new_status(
                old_status=concept_plan["status"],
                # created=created_at,
                # updated=updated_at,
            )
            creator = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=concept_plan["creator_id"],
            )
            modifier = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=concept_plan["modifier_id"],
            )
            new_proj_id = self.spms_get_project_by_old_id(
                old_id=concept_plan["project_id"],
                cursor=cursor,
                connection=connection,
            )

            pdf_generation_in_progress = False
            directorate_approval_granted = True if status == "approved" else False
            business_area_lead_approval_granted = (
                True
                if (directorate_approval_granted) or status == "inapproval"
                else False
            )
            project_lead_approval_granted = (
                True
                if (status != "new")
                or business_area_lead_approval_granted
                or directorate_approval_granted
                else False
            )  # set all non-news to approved

            # directorate_approval_granted = True if status == "approved" else False
            # business_area_lead_approval_granted = True if (directorate_approval_granted) else False
            # project_lead_approval_granted = True if (status != "new") or business_area_lead_approval_granted or directorate_approval_granted else False # set all non-news to approved

            kind = "concept"
            pdf = None if self.pd.isna(concept_plan["pdf"]) else concept_plan["pdf"]
            print(pdf)
            try:
                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    base_sql,
                    (
                        old_id,  # old_id,
                        creator,
                        modifier,
                        created_at,  # created
                        updated_at,  # modified
                        new_proj_id,
                        status,
                        kind,
                        pdf_generation_in_progress,
                        directorate_approval_granted,
                        project_lead_approval_granted,
                        business_area_lead_approval_granted,
                        # pdf,
                    ),
                )
            except Exception as e:
                print(old_id)
                print(created_at)
                print(updated_at)
                print(new_proj_id)
                print(concept_plan["status"])
                print(kind)
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Concept Plan Base (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN} Concept Plan Base (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # Create the concept plan details that correspond with document

            try:
                print(
                    f"{self.misc.bcolors.WARNING}Creating Concept Plan Details({old_id})...{self.misc.bcolors.ENDC}"
                )

                # Get new values related to each concept plan details entry

                new_document_id = self.spms_get_document_id_by_old_id(
                    cursor=cursor,
                    connection=connection,
                    old_id=old_id,
                )
                background = (
                    None
                    if self.pd.isna(concept_plan["background"])
                    else concept_plan["background"]
                )
                aims = (
                    None
                    if self.pd.isna(concept_plan["summary"])
                    else concept_plan["summary"]
                )
                outcome = (
                    None
                    if self.pd.isna(concept_plan["outcome"])
                    else concept_plan["outcome"]
                )
                collaborations = (
                    None
                    if self.pd.isna(concept_plan["collaborations"])
                    else concept_plan["collaborations"]
                )
                strategic_context = (
                    None
                    if self.pd.isna(concept_plan["strategic"])
                    else concept_plan["strategic"]
                )
                staff_time_allocation = (
                    None
                    if self.pd.isna(concept_plan["staff"])
                    else concept_plan["staff"]
                )
                budget = (
                    None
                    if self.pd.isna(concept_plan["budget"])
                    else concept_plan["budget"]
                )

                cursor.execute(
                    concept_plan_sql,
                    (
                        new_document_id,  # document_id,
                        new_proj_id,
                        background,
                        aims,  # summary
                        outcome,
                        collaborations,
                        strategic_context,  # strategic
                        staff_time_allocation,  # staff
                        budget,
                    ),
                )

            except Exception as e:
                print(new_document_id)
                print(background)
                print(aims)
                print(outcome)
                print(collaborations)
                print(strategic_context)
                print(staff_time_allocation)
                print(budget)
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Concept Plan Details (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN} Concept Plan Details (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # self.spms_create_tasks_for_document(
            #     connection=connection,
            #     cursor=cursor,
            #     document_id=new_document_id,
            #     doc_status=status,
            #     doc_type="Concept Plan",
            # )

            if pdf != None:
                file_directory = os.path.join(
                    self.django_project_path, "dumped_media", pdf
                )
                print(file_directory)
                with open(file_directory, "rb") as file:
                    # Create an InMemoryUploadedFile
                    uploaded_file = InMemoryUploadedFile(
                        file,
                        None,
                        os.path.basename(file_directory),
                        "application/pdf",  # Adjust the content type based on your file type
                        len(file.read()),  # Pass the file content length
                        None,
                    )

                    saved_file = default_storage.save(
                        f"project_documents/{uploaded_file.name}", uploaded_file
                    )

                    try:
                        self.create_project_document_pdf(
                            connection=connection,
                            cursor=cursor,
                            related_document_id=new_document_id,
                            related_project_id=new_proj_id,
                            data=saved_file,
                        )

                    except Exception as e:
                        print(e)
                        continue

    def spms_project_plan_setter(
        self,
        dataframe,
        cursor,
        connection,
        current_datetime,
        set_new_status,
    ):
        # Construct SQL for base document
        base_sql = """
            BEGIN;
            INSERT INTO documents_projectdocument (
                old_id,    
                creator_id,
                modifier_id,     
                created_at, 
                updated_at,
                project_id, 
                status, 
                kind,
                pdf_generation_in_progress,
                directorate_approval_granted,
                project_lead_approval_granted,
                business_area_lead_approval_granted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        #                 pdf

        # Execute sql per row
        for index, project_plan in dataframe.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating Project Plan Base({project_plan['id']})...{self.misc.bcolors.ENDC}"
            )

            # Get new values related to each base document entry
            old_id = int(project_plan["id"])
            created_at = project_plan["created"]
            updated_at = (
                project_plan["created"]
                if not self.pd.isna(project_plan["created"])
                and self.pd.isna(project_plan["modified"])
                else (
                    project_plan["modified"]
                    if not self.pd.isna(project_plan["modified"])
                    else current_datetime
                )
            )
            status = set_new_status(
                old_status=project_plan["status"],
                # created=created_at,
                # updated=updated_at,
            )
            creator = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=project_plan["creator_id"],
            )
            modifier = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=project_plan["modifier_id"],
            )
            new_proj_id = self.spms_get_project_by_old_id(
                old_id=project_plan["project_id"],
                cursor=cursor,
                connection=connection,
            )
            kind = "projectplan"
            pdf = None if self.pd.isna(project_plan["pdf"]) else project_plan["pdf"]
            print(pdf)

            pdf_generation_in_progress = False
            directorate_approval_granted = True if status == "approved" else False
            business_area_lead_approval_granted = (
                True
                if (directorate_approval_granted) or status == "inapproval"
                else False
            )
            project_lead_approval_granted = (
                True
                if (status != "new")
                or business_area_lead_approval_granted
                or directorate_approval_granted
                else False
            )  # set all non-news to approved

            try:
                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    base_sql,
                    (
                        old_id,  # old_id,
                        creator,
                        modifier,
                        created_at,  # created
                        updated_at,  # modified
                        new_proj_id,
                        status,
                        kind,
                        pdf_generation_in_progress,
                        directorate_approval_granted,
                        project_lead_approval_granted,
                        business_area_lead_approval_granted,
                        # pdf,
                    ),
                )
            except Exception as e:
                print(old_id)
                print(created_at)
                print(updated_at)
                print(new_proj_id)
                print(status)
                print(kind)
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Project Plan Base (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Project Plan Base (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # Create the project plan details that correspond with document
            project_plan_sql = """
                BEGIN;
                INSERT INTO documents_projectplan (
                    document_id, 
                    project_id,
                    background, 
                    aims,
                    outcome, 
                    knowledge_transfer,
                    project_tasks,
                    listed_references,
                    methodology,
                    operating_budget,
                    operating_budget_external,
                    related_projects
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                COMMIT;
            """
            #            involves_plants,
            # involves_animals,

            try:
                print(
                    f"{self.misc.bcolors.WARNING}Creating Project Plan Details({old_id})...{self.misc.bcolors.ENDC}"
                )

                # Get new values related to each concept plan details entry

                new_document_id = self.spms_get_document_id_by_old_id(
                    cursor=cursor,
                    connection=connection,
                    old_id=old_id,
                )

                background = (
                    None
                    if self.pd.isna(project_plan["background"])
                    else project_plan["background"]
                )

                aims = (
                    None if self.pd.isna(project_plan["aims"]) else project_plan["aims"]
                )
                outcome = (
                    None
                    if self.pd.isna(project_plan["outcome"])
                    else project_plan["outcome"]
                )
                knowledge_transfer = (
                    None
                    if self.pd.isna(project_plan["knowledge_transfer"])
                    else project_plan["knowledge_transfer"]
                )
                project_tasks = (
                    None
                    if self.pd.isna(project_plan["project_tasks"])
                    else project_plan["project_tasks"]
                )
                listed_references = (
                    None
                    if self.pd.isna(project_plan["references"])
                    else project_plan["references"]
                )
                methodology = (
                    None
                    if self.pd.isna(project_plan["methodology"])
                    else project_plan["methodology"]
                )

                operating_budget = (
                    None
                    if self.pd.isna(project_plan["operating_budget"])
                    else project_plan["operating_budget"]
                )

                operating_budget_external = (
                    None
                    if self.pd.isna(project_plan["operating_budget_external"])
                    else project_plan["operating_budget_external"]
                )

                related_projects = (
                    None
                    if self.pd.isna(project_plan["related_projects"])
                    else project_plan["related_projects"]
                )
                cursor.execute(
                    project_plan_sql,
                    (
                        new_document_id,
                        new_proj_id,
                        background,
                        aims,
                        outcome,
                        knowledge_transfer,
                        project_tasks,
                        listed_references,  # renamed as references is a reserved word that causes errors
                        methodology,
                        operating_budget,
                        operating_budget_external,
                        related_projects,
                    ),
                )

            except Exception as e:
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Project Plan Details (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                print(
                    new_document_id,
                    new_proj_id,
                    background,
                    aims,
                    outcome,
                    knowledge_transfer,
                    project_tasks,
                    listed_references,  # renamed as references is a reserved word that causes errors
                    methodology,
                    # involves_plants,
                    # involves_animals,
                    operating_budget,
                    operating_budget_external,
                    related_projects,
                )
                #  document_id,
                #         project_id,
                #         background,
                #         aims,
                #         outcome,
                #         knowledge_transfer,
                #         project_tasks,
                #         listed_references,
                #         methodology,
                #         operating_budget,
                #         operating_budget_external,
                #         related_projects

                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN} Project Plan Details (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            endorsements_sql = """
                BEGIN;
                INSERT INTO documents_endorsement (
                    project_plan_id, 
                    ae_endorsement_required, 
                    ae_endorsement_provided,
                    data_management,
                    no_specimens
                ) VALUES (%s, %s, %s, %s, %s);
                COMMIT;
            """
# %s, %s, %s, %s, 
#             bm_endorsement_required, 
#                     bm_endorsement_provided,
#                     hc_endorsement_required,
#                     hc_endorsement_provided,
            # Endorsement

            try:
                print(
                    f"{self.misc.bcolors.WARNING}Creating Endorsements for Project Plan...{self.misc.bcolors.ENDC}"
                )

                project_plan_detail_id = self.spms_get_project_plan_details_by_new_id(
                    new_id=new_document_id,
                    cursor=cursor,
                    connection=connection,
                )
                # involves_plants = (
                #     False
                #     if self.pd.isna(project_plan["involves_plants"])
                #     else project_plan["involves_plants"]
                # )

                # involves_animals = (
                #     False
                #     if self.pd.isna(project_plan["involves_animals"])
                #     else project_plan["involves_animals"]
                # )
                # bm_endorsement_required = (
                #     False
                #     if (
                #         self.pd.isna(project_plan["bm_endorsement"])
                #         or project_plan["bm_endorsement"] == "not required"
                #     )
                #     else True
                # )
                # bm_endorsement_provided = (
                #     True
                #     if (
                #         (project_plan["bm_endorsement"] == "granted")
                #         or (
                #             bm_endorsement_required == True
                #             and project_plan["status"] == "approved"
                #         )
                #     )
                #     else False
                # )
                # hc_endorsement_required = (
                #     False
                #     if (
                #         self.pd.isna(project_plan["hc_endorsement"])
                #         or project_plan["hc_endorsement"] == "not required"
                #     )
                #     else True
                # )
                # hc_endorsement_provided = (
                #     True
                #     if (
                #         (project_plan["hc_endorsement"] == "granted")
                #         or (
                #             hc_endorsement_required == True
                #             and project_plan["status"] == "approved"
                #         )
                #     )
                #     else False
                # )
                ae_endorsement_required = (
                    False
                    if (
                        self.pd.isna(project_plan["ae_endorsement"])
                        or project_plan["ae_endorsement"] == "not required"
                    )
                    else True
                )
                ae_endorsement_provided = (
                    True
                    if (
                        (project_plan["ae_endorsement"] == "granted")
                        or (
                            ae_endorsement_required == True
                            and project_plan["status"] == "approved"
                        )
                    )
                    else False
                )

                data_management = (
                    None
                    if self.pd.isna(project_plan["data_management"])
                    else project_plan["data_management"]
                )

                no_specimens = (
                    None
                    if self.pd.isna(project_plan["no_specimens"])
                    else project_plan["no_specimens"]
                )

                cursor.execute(
                    endorsements_sql,
                    (
                        project_plan_detail_id,
                        # new_proj_id,
                        # bm_endorsement_required,
                        # bm_endorsement_provided,
                        # hc_endorsement_required,
                        # hc_endorsement_provided,
                        ae_endorsement_required,
                        ae_endorsement_provided,
                        data_management,
                        no_specimens,
                    ),
                )

            except Exception as e:
                print(
                    project_plan_detail_id,
                    # new_proj_id,
                    # bm_endorsement_required,
                    # bm_endorsement_provided,
                    # hc_endorsement_required,
                    # hc_endorsement_provided,
                    ae_endorsement_required,
                    ae_endorsement_provided,
                    data_management,
                    no_specimens,
                )
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Endorsements ({project_plan_detail_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN} Endorsements ({project_plan_detail_id})Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # self.spms_create_tasks_for_document(
            #     connection=connection,
            #     cursor=cursor,
            #     document_id=new_document_id,
            #     doc_status=status,
            #     doc_type="Project Plan",
            # )

            if pdf != None:
                file_directory = os.path.join(
                    self.django_project_path, "dumped_media", pdf
                )
                print(file_directory)
                with open(file_directory, "rb") as file:
                    # Create an InMemoryUploadedFile
                    uploaded_file = InMemoryUploadedFile(
                        file,
                        None,
                        os.path.basename(file_directory),
                        "application/pdf",  # Adjust the content type based on your file type
                        len(file.read()),  # Pass the file content length
                        None,
                    )

                    saved_file = default_storage.save(
                        f"project_documents/{uploaded_file.name}", uploaded_file
                    )

                    try:
                        self.create_project_document_pdf(
                            connection=connection,
                            cursor=cursor,
                            related_document_id=new_document_id,
                            related_project_id=new_proj_id,
                            data=saved_file,
                        )
                    except Exception as e:
                        print(e)
                        continue

    def spms_progress_report_setter(
        self, dataframe, cursor, connection, current_datetime, set_new_status
    ):
        # Construct SQL for base document
        base_sql = """
            BEGIN;
            INSERT INTO documents_projectdocument (
                old_id,    
                creator_id,
                modifier_id,     
                created_at, 
                updated_at,
                project_id, 
                status, 
                kind,
                pdf_generation_in_progress,
                directorate_approval_granted,
                project_lead_approval_granted,
                business_area_lead_approval_granted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        #                 pdf

        # Execute sql per row
        for index, progress_report in dataframe.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating Progress Report Base({progress_report['id']})...{self.misc.bcolors.ENDC}"
            )

            # Get new values related to each base document entry
            old_id = int(progress_report["id"])
            created_at = progress_report["created"]
            updated_at = (
                progress_report["created"]
                if not self.pd.isna(progress_report["created"])
                and self.pd.isna(progress_report["modified"])
                else (
                    progress_report["modified"]
                    if not self.pd.isna(progress_report["modified"])
                    else current_datetime
                )
            )
            status = set_new_status(
                old_status=progress_report["status"],
                # created=created_at,
                # updated=updated_at,
            )
            creator = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=progress_report["creator_id"],
            )
            modifier = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=progress_report["modifier_id"],
            )
            new_proj_id = self.spms_get_project_by_old_id(
                old_id=progress_report["project_id"],
                cursor=cursor,
                connection=connection,
            )
            # status = progress_report["status"]
            kind = "progressreport"
            pdf = (
                None if self.pd.isna(progress_report["pdf"]) else progress_report["pdf"]
            )
            print(pdf)

            pdf_generation_in_progress = False
            directorate_approval_granted = True if status == "approved" else False
            business_area_lead_approval_granted = (
                True
                if (directorate_approval_granted) or status == "inapproval"
                else False
            )
            project_lead_approval_granted = (
                True
                if (status != "new")
                or business_area_lead_approval_granted
                or directorate_approval_granted
                else False
            )  # set all non-news to approved

            try:
                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    base_sql,
                    (
                        old_id,  # old_id,
                        creator,
                        modifier,
                        created_at,  # created
                        updated_at,  # modified
                        new_proj_id,
                        status,
                        kind,
                        pdf_generation_in_progress,
                        directorate_approval_granted,
                        project_lead_approval_granted,
                        business_area_lead_approval_granted,
                        # pdf,
                    ),
                )
            except Exception as e:
                print(old_id)
                print(created_at)
                print(updated_at)
                print(new_proj_id)
                print(status)
                print(kind)
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Progress Report Base (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Progress Report Base (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

                # finally:
                connection.commit()

            # Construct the SQL query for progressreports

            try:
                year = (
                    None
                    if self.pd.isna(progress_report["year"])
                    else progress_report["year"]
                )
                is_final_report = (
                    None
                    if self.pd.isna(progress_report["is_final_report"])
                    else progress_report["is_final_report"]
                )
                context = (
                    None
                    if self.pd.isna(progress_report["context"])
                    else progress_report["context"]
                )
                aims = (
                    None
                    if self.pd.isna(progress_report["aims"])
                    else progress_report["aims"]
                )
                progress = (
                    None
                    if self.pd.isna(progress_report["progress"])
                    else progress_report["progress"]
                )
                implications = (
                    None
                    if self.pd.isna(progress_report["implications"])
                    else progress_report["implications"]
                )
                future = (
                    None
                    if self.pd.isna(progress_report["future"])
                    else progress_report["future"]
                )
                new_document_id = self.spms_get_document_id_by_old_id(
                    cursor=cursor,
                    connection=connection,
                    old_id=old_id,
                )

                report_id = (
                    None
                    if self.pd.isna(progress_report["report_id"])
                    else self.spms_calculate_new_report_id(
                        doc=progress_report, old_report_id=progress_report["report_id"]
                    )
                )

                if report_id is None:
                    report_id = self.spms_get_new_report_id_by_year(
                        year=year, connection=connection, cursor=cursor
                    )

                print(f"NEW DOC ID: {new_document_id}")
                print(f"NEW REPORT ID: {report_id}")
                print(f"NEW PROJ ID: {new_proj_id}")

                progress_report_sql = """
                    BEGIN;
                    INSERT INTO documents_progressreport (
                        document_id, 
                        project_id,
                        report_id, 
                        year, 
                        is_final_report,
                        context, 
                        aims, 
                        progress, 
                        implications, 
                        future        
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    COMMIT;
                """

                if report_id is not None:
                    # Start a transaction
                    # cursor = connection.cursor()
                    cursor.execute(
                        progress_report_sql,
                        (
                            new_document_id,
                            new_proj_id,
                            report_id,
                            year,
                            is_final_report,
                            context,
                            aims,
                            progress,
                            implications,
                            future,
                            # pdf,
                        ),
                    )
            except Exception as e:
                print(
                    new_document_id,
                    report_id,
                    year,
                    is_final_report,
                    context,
                    aims,
                    progress,
                    implications,
                    future,
                    # pdf,
                ),
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Progress Report Base (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Progress Report Base (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # self.spms_create_tasks_for_document(
            #     connection=connection,
            #     cursor=cursor,
            #     document_id=new_document_id,
            #     doc_status=status,
            #     doc_type="Progress Report",
            # )

            if (pdf != None) and (report_id != None):
                file_directory = os.path.join(
                    self.django_project_path, "dumped_media", pdf
                )
                print(file_directory)
                with open(file_directory, "rb") as file:
                    # Create an InMemoryUploadedFile
                    uploaded_file = InMemoryUploadedFile(
                        file,
                        None,
                        os.path.basename(file_directory),
                        "application/pdf",  # Adjust the content type based on your file type
                        len(file.read()),  # Pass the file content length
                        None,
                    )

                    saved_file = default_storage.save(
                        f"project_documents/{uploaded_file.name}", uploaded_file
                    )

                    try:
                        self.create_project_document_pdf(
                            connection=connection,
                            cursor=cursor,
                            related_document_id=new_document_id,
                            related_project_id=new_proj_id,
                            data=saved_file,
                        )
                    except Exception as e:
                        print(e)
                        continue

    def spms_student_report_setter(
        self, dataframe, cursor, connection, current_datetime, set_new_status
    ):
        # Construct SQL for base document
        base_sql = """
            BEGIN;
            INSERT INTO documents_projectdocument (
                old_id,    
                creator_id,
                modifier_id,     
                created_at, 
                updated_at,
                project_id, 
                status, 
                kind,
                pdf_generation_in_progress,
                directorate_approval_granted,
                project_lead_approval_granted,
                business_area_lead_approval_granted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        #                 pdf

        # Execute sql per row
        for index, student_report in dataframe.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating Student Report Base({student_report['id']})...{self.misc.bcolors.ENDC}"
            )

            # Get new values related to each base document entry
            old_id = int(student_report["id"])
            created_at = student_report["created"]
            updated_at = (
                student_report["created"]
                if not self.pd.isna(student_report["created"])
                and self.pd.isna(student_report["modified"])
                else (
                    student_report["modified"]
                    if not self.pd.isna(student_report["modified"])
                    else current_datetime
                )
            )
            status = set_new_status(
                old_status=student_report["status"],
                # created=created_at,
                # updated=updated_at,
            )
            creator = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=student_report["creator_id"],
            )
            modifier = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=student_report["modifier_id"],
            )
            new_proj_id = self.spms_get_project_by_old_id(
                old_id=student_report["project_id"],
                cursor=cursor,
                connection=connection,
            )
            # status = student_report["status"]
            kind = "studentreport"
            pdf = None if self.pd.isna(student_report["pdf"]) else student_report["pdf"]
            print(pdf)

            pdf_generation_in_progress = False
            directorate_approval_granted = True if status == "approved" else False
            business_area_lead_approval_granted = (
                True
                if (directorate_approval_granted) or status == "inapproval"
                else False
            )
            project_lead_approval_granted = (
                True
                if (status != "new")
                or business_area_lead_approval_granted
                or directorate_approval_granted
                else False
            )  # set all non-news to approved

            try:
                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    base_sql,
                    (
                        old_id,  # old_id,
                        creator,
                        modifier,
                        created_at,  # created
                        updated_at,  # modified
                        new_proj_id,
                        status,
                        kind,
                        pdf_generation_in_progress,
                        directorate_approval_granted,
                        project_lead_approval_granted,
                        business_area_lead_approval_granted,
                        # pdf,
                    ),
                )
            except Exception as e:
                print(old_id)
                print(created_at)
                print(updated_at)
                print(new_proj_id)
                print(status)
                print(kind)
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Studebt Report Base (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Student Report Base (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # Construct the SQL query for studentreports
            student_report_sql = """
                BEGIN;
                INSERT INTO documents_studentreport (
                    document_id, 
                    project_id, 
                    report_id, 
                    progress_report,
                    year         
                ) VALUES (%s, %s, %s, %s, %s);
                COMMIT;
            """

            try:
                document_id = self.spms_get_document_id_by_old_id(
                    cursor=cursor, connection=connection, old_id=student_report["id"]
                )
                report_id = (
                    None
                    if self.pd.isna(student_report["report_id"])
                    else self.spms_calculate_new_report_id(
                        doc=student_report, old_report_id=student_report["report_id"]
                    )
                )
                reported_info = (
                    None
                    if self.pd.isna(student_report["progress_report"])
                    else student_report["progress_report"]
                )
                year = (
                    None
                    if self.pd.isna(student_report["year"])
                    else student_report["year"]
                )

                if report_id is None:
                    report_id = self.spms_get_new_report_id_by_year(
                        connection=connection, cursor=cursor, year=year
                    )

                # Start a transaction
                # cursor = connection.cursor()
                cursor.execute(
                    student_report_sql,
                    (
                        document_id,
                        new_proj_id,
                        report_id,
                        reported_info,
                        year,
                    ),
                )
            except Exception as e:
                print(
                    document_id,
                    report_id,
                    reported_info,
                    year,
                )
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Student Report Detail (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Student Report Detail (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # self.spms_create_tasks_for_document(
            #     connection=connection,
            #     cursor=cursor,
            #     document_id=document_id,
            #     doc_status=status,
            #     doc_type="Student Report",
            # )

            if pdf != None:
                file_directory = os.path.join(
                    self.django_project_path, "dumped_media", pdf
                )
                print(file_directory)
                with open(file_directory, "rb") as file:
                    # Create an InMemoryUploadedFile
                    uploaded_file = InMemoryUploadedFile(
                        file,
                        None,
                        os.path.basename(file_directory),
                        "application/pdf",  # Adjust the content type based on your file type
                        len(file.read()),  # Pass the file content length
                        None,
                    )

                    saved_file = default_storage.save(
                        f"project_documents/{uploaded_file.name}", uploaded_file
                    )
                    try:
                        self.create_project_document_pdf(
                            connection=connection,
                            cursor=cursor,
                            related_document_id=document_id,
                            related_project_id=new_proj_id,
                            data=saved_file,
                        )
                    except Exception as e:
                        print(e)
                        continue

    def spms_project_closure_setter(
        self, dataframe, cursor, connection, current_datetime, set_new_status
    ):
        # Construct SQL for base document
        base_sql = """
            BEGIN;
            INSERT INTO documents_projectdocument (
                old_id,    
                creator_id,
                modifier_id,     
                created_at, 
                updated_at,
                project_id, 
                status, 
                kind,
                pdf_generation_in_progress,
                directorate_approval_granted,
                project_lead_approval_granted,
                business_area_lead_approval_granted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """
        # pdf

        # Execute sql per row
        for index, proj_closure in dataframe.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating Project Closure Base({proj_closure['id']})...{self.misc.bcolors.ENDC}"
            )

            # Get new values related to each base document entry
            old_id = int(proj_closure["id"])
            created_at = proj_closure["created"]
            updated_at = (
                proj_closure["created"]
                if not self.pd.isna(proj_closure["created"])
                and self.pd.isna(proj_closure["modified"])
                else (
                    proj_closure["modified"]
                    if not self.pd.isna(proj_closure["modified"])
                    else current_datetime
                )
            )
            status = set_new_status(
                old_status=proj_closure["status"],
                # created=created_at,
                # updated=updated_at,
            )
            creator = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=proj_closure["creator_id"],
            )
            modifier = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=proj_closure["modifier_id"],
            )
            new_proj_id = self.spms_get_project_by_old_id(
                old_id=proj_closure["project_id"],
                cursor=cursor,
                connection=connection,
            )

            # Get project to check status
            proj_status = self.spms_get_new_project_status(
                connection=connection, new_proj_id=new_proj_id
            )

            # status = proj_closure["status"]
            kind = "projectclosure"
            pdf = None if self.pd.isna(proj_closure["pdf"]) else proj_closure["pdf"]

            pdf_generation_in_progress = False
            if status != "approved":
                directorate_approval_granted = False
            else:
                directorate_approval_granted = True
            business_area_lead_approval_granted = (
                True
                if (directorate_approval_granted) or status == "inapproval"
                else False
            )
            project_lead_approval_granted = (
                True
                if (status != "new")
                or business_area_lead_approval_granted
                or directorate_approval_granted
                else False
            )  # set all non-news to approved

            # directorate_approval_granted = True if status == "approved" else False
            # business_area_lead_approval_granted = True if (directorate_approval_granted == True or status == "inapproval") else False
            # project_lead_approval_granted = True if (
            #     status == "inreview" or status == "revising" or
            #     business_area_lead_approval_granted == True or
            #     directorate_approval_granted == True
            # ) else False # set all non-news to approved

            print(pdf)
            try:
                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    base_sql,
                    (
                        old_id,  # old_id,
                        creator,
                        modifier,
                        created_at,  # created
                        updated_at,  # modified
                        new_proj_id,
                        status,
                        kind,
                        pdf_generation_in_progress,
                        directorate_approval_granted,
                        project_lead_approval_granted,
                        business_area_lead_approval_granted,
                        # pdf,
                    ),
                )
            except Exception as e:
                print(old_id)
                print(created_at)
                print(updated_at)
                print(new_proj_id)
                print(status)
                print(kind)
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Project Closure Base (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Project Closure Base (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            try:
                document_id = self.spms_get_document_id_by_old_id(
                    cursor=cursor, connection=connection, old_id=proj_closure["id"]
                )
                intended_outcome = (
                    None if self.pd.isna(proj_closure["goal"]) else proj_closure["goal"]
                )
                reason = (
                    None
                    if self.pd.isna(proj_closure["reason"])
                    else proj_closure["reason"]
                )
                scientific_outputs = (
                    None
                    if self.pd.isna(proj_closure["scientific_outputs"])
                    else proj_closure["scientific_outputs"]
                )

                knowledge_transfer = (
                    None
                    if self.pd.isna(proj_closure["knowledge_transfer"])
                    else proj_closure["knowledge_transfer"]
                )
                data_location = (
                    None
                    if self.pd.isna(proj_closure["data_location"])
                    else proj_closure["data_location"]
                )
                hardcopy_location = (
                    None
                    if self.pd.isna(proj_closure["hardcopy_location"])
                    else proj_closure["hardcopy_location"]
                )
                backup_location = (
                    None
                    if self.pd.isna(proj_closure["backup_location"])
                    else proj_closure["backup_location"]
                )
                # Start a transaction
                # cursor = connection.cursor()
                #                Construct the SQL query for projectclosure
                project_closure_sql = """
                    BEGIN;
                    INSERT INTO documents_projectclosure (
                        document_id, 
                        project_id, 
                        intended_outcome, 
                        reason,
                        scientific_outputs, 
                        knowledge_transfer,
                        data_location,
                        hardcopy_location, 
                        backup_location          
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    COMMIT;
                """
                if intended_outcome == "force_completed":
                    intended_outcome = "completed"
                cursor.execute(
                    project_closure_sql,
                    (
                        document_id,
                        new_proj_id,
                        intended_outcome,
                        reason,
                        scientific_outputs,
                        knowledge_transfer,
                        data_location,
                        hardcopy_location,
                        backup_location,
                    ),
                )
            except Exception as e:
                print(
                    document_id,
                    new_proj_id,
                    intended_outcome,
                    reason,
                    scientific_outputs,
                    knowledge_transfer,
                    data_location,
                    hardcopy_location,
                    backup_location,
                ),
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Project Closure Detail (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Project Closure Detail (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            # self.spms_create_tasks_for_document(
            #     connection=connection,
            #     cursor=cursor,
            #     document_id=document_id,
            #     doc_status=status,
            #     doc_type="Project Closure",
            # )

            if pdf != None:
                file_directory = os.path.join(
                    self.django_project_path, "dumped_media", pdf
                )
                print(file_directory)
                with open(file_directory, "rb") as file:
                    # Create an InMemoryUploadedFile
                    uploaded_file = InMemoryUploadedFile(
                        file,
                        None,
                        os.path.basename(file_directory),
                        "application/pdf",  # Adjust the content type based on your file type
                        len(file.read()),  # Pass the file content length
                        None,
                    )

                    saved_file = default_storage.save(
                        f"project_documents/{uploaded_file.name}", uploaded_file
                    )

                    try:
                        self.create_project_document_pdf(
                            connection=connection,
                            cursor=cursor,
                            related_document_id=document_id,
                            related_project_id=new_proj_id,
                            data=saved_file,
                        )

                    except Exception as e:
                        print(e)
                        continue

    def spms_get_new_project_status(
        self,
        connection,
        new_proj_id,
    ):
        try:
            cursor = connection.cursor()

            # Convert the old_id value to a regular Python integer
            new_proj_id = int(new_proj_id)

            # Construct the SQL query
            sql = """
                SELECT id FROM projects_project WHERE id = %s
            """
            print(f"Seeking id {new_proj_id} in project table")

            # Execute the query with the user name
            cursor.execute(sql, (new_proj_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                status = result[0]  # Return the status
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error retrieving project: {str(e)}{self.misc.bcolors.ENDC}"
            )
            print(f"RESULT: {result}, RESULT[0]: {result[0]}")
            # Rollback the transaction
            connection.rollback()
            return None
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Project Status ({status})!{self.misc.bcolors.ENDC}"
            )
            return status

    def spms_create_project_task(
        self,
        connection,
        cursor,
        task_type,
        user_id,
        task_name,
        task_description,
        project_id,
    ):
        # Construct the SQL
        sql = """
        INSERT INTO tasks_task (
            created_at, 
            updated_at, 
            creator_id,
            user_id, 
            project_id,
            document_id, 
            name, 
            description, 
            notes, 
            status, 
            task_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        document_id = None
        creator_id = self.spms_get_superuser(connection=connection, cursor=cursor)
        # Get the time of creation
        created_time = dt.now()
        status = "todo"
        notes = None
        # Execute the raw SQL query with the given parameters
        cursor.execute(
            sql,
            (
                created_time,  # created
                created_time,  # udpated
                creator_id,
                user_id,  # user
                project_id,
                document_id,  # docid
                task_name,
                task_description,
                notes,  # notes
                status,  # status
                task_type,
            ),
        )

        # Fetch the newly inserted task's ID using the 'RETURNING' clause
        task_id = cursor.fetchone()[0]

        # Commit the changes to the database
        connection.commit()

        # Return the ID of the newly created task
        return task_id

    def spms_create_superuser_todos(self):
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        superuser_id = self.spms_get_superuser(connection=connection, cursor=cursor)
        todos = [
            {
                "name": "(TODO) Rewire frontend with backend",
                "description": "Work on integrating frontend with backend functionality",
            },
            {
                "name": "(TODO) Creating Modern Tasks component",
                "description": "Develop a modern task component for the application",
            },
            {
                "name": "(TODO) Adjust TaskCard for Dash button styling for hover and darkmode",
                "description": "Update TaskCard appearance for better styling on hover and dark mode",
            },
            {
                "name": "(TODO) Work on how tasks are autocompleted/autoadded for front and backend based on actions",
                "description": "Implement auto-completion/auto-addition of tasks based on user actions",
            },
            {
                "name": "(TODO) Update or remove minimum width of task cards",
                "description": "Modify task card minimum width to avoid overflow in dashboard grid",
            },
            {
                "name": "(TODO) Update Page responsiveness on modern version to account for sidebar being open and closed",
                "description": "Adjust page responsiveness for modern version to handle sidebar open and closed state",
            },
            {
                "name": "(TODO) Fix dashboard",
                "description": "Resolve issues and improve functionality in the dashboard",
            },
            {
                "name": "(TODO) Add additional filters for projects",
                "description": "Enhance project filtering options with additional filters",
            },
            {
                "name": "(TODO) Add a User Manual Section to the website (/howto), accessible via Navitar",
                "description": "Create a user manual section on the website accessible through Navitar",
            },
            {
                "name": "(TODO) Create the How To page and make it fully functional",
                "description": "Develop and fully functionalize the How To page",
            },
            {
                "name": "(TODO) Create a chatbot that scans the how to page to provide answers",
                "description": "Build a chatbot that scans the How To page and offers assistance",
            },
            {
                "name": "(TODO) Make email fields lowercase when creating a user and checking if a user exists with that email.",
                "description": "Ensure email fields are in lowercase for user creation and checks",
            },
            {
                "name": "(TODO) Fix Modals button location not always at the bottom",
                "description": "Adjust modal button location to be consistently at the bottom",
            },
            {
                "name": "(TODO) Fix navigating away issue (still occurring)",
                "description": "Resolve issue with navigation that is still occurring",
            },
            {
                "name": "(TODO) Refresh the cache in react tanstack query for users when a new user is created (and soft reload)",
                "description": "Implement cache refresh for users when a new user is created",
            },
            {
                "name": "(TODO) Code Cleanup, comments and refactor (migrator, frontend, & backend)",
                "description": "Perform code cleanup, add comments, and refactor code in migrator, frontend, and backend",
            },
            {
                "name": "(TODO) Set executives role as Executive so they show as orange with Executive tag",
                "description": "Assign 'Executive' role to executives to display as orange with the Executive tag",
            },
            {
                "name": "(TODO) Update the Modal for Profile on the Account page (Design)",
                "description": "Design and update the Modal for Profile on the Account page",
            },
            {
                "name": "(TODO) Update the Modal for Organisation on the Account page (Design)",
                "description": "Design and update the Modal for Organisation on the Account page",
            },
            {
                "name": "(TODO) Connecting API with Modals and backend (API)",
                "description": "Establish API connection between Modals and backend",
            },
            {
                "name": "(TODO) Make account drawer modals functional",
                "description": "Implement functionality for account drawer modals",
            },
        ]

        for todo in todos:
            task_name = todo["name"].replace("(TODO) ", "")
            task_description = todo["description"]
            self.spms_create_task(
                connection=connection,
                cursor=cursor,
                task_name=task_name,
                task_description=task_description,
                task_type="personal",
                user_id=superuser_id,
                document_id=None,
            )

        # Close the database connection
        cursor.close()
        connection.close()

    def spms_create_task(
        self,
        connection,
        cursor,
        task_type,
        user_id,
        task_name,
        task_description,
        document_id,
    ):
        # Construct the SQL
        sql = """
        INSERT INTO tasks_task (
            created_at, 
            updated_at, 
            creator_id,
            user_id, 
            project_id,
            document_id, 
            name, 
            description, 
            notes, 
            status, 
            task_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        # Get the time of creation
        created_time = dt.now()
        status = "todo"
        creator_id = self.spms_get_superuser(connection=connection, cursor=cursor)
        project_id = self.spms_get_project_by_document_id(
            connection=connection, cursor=cursor, document_id=document_id
        )
        notes = None
        # Execute the raw SQL query with the given parameters
        cursor.execute(
            sql,
            (
                created_time,  # created
                created_time,  # udpated
                creator_id,
                user_id,  # user
                project_id,
                document_id,  # docid
                task_name,
                task_description,
                notes,  # notes
                status,  # status
                task_type,
            ),
        )

        print(f"task:{task_name}, description:{task_description}, user: {user_id}")

        # Fetch the newly inserted task's ID using the 'RETURNING' clause
        task_id = cursor.fetchone()[0]

        # Commit the changes to the database
        connection.commit()

        # Return the ID of the newly created task
        return task_id

    def spms_create_tasks_for_document(
        self, connection, cursor, document_id, doc_status, doc_type
    ):
        # Get the project the document belongs to
        project = self.spms_get_project_details_based_on_doc_id(
            cursor=cursor,
            connection=connection,
            document_id=document_id,
        )

        # If the status of the project is completed, terminated, suspended etc, return - there is nothing to do.
        done_array = ["completed", "terminated", "suspended"]

        print("Checking if in done array")

        if project["status"] in done_array:
            return

        else:
            # Get the status of the document
            status = doc_status
            # If the status is approved, return - there is no to dos to add (will be added to the report)
            if status == "approved":
                return
            # If the status is inreview, create an assigned task for the leader of the business area
            elif status == "inreview":
                print("In Review. Getting BA Leader")
                try:
                    ba_leader = self.spms_get_ba_leader_from_project_ba(
                        connection=connection,
                        cursor=cursor,
                        business_area_id=project["business_area_id"],
                    )
                except Exception as e:
                    input(e)
                else:
                    print("Assigning Task to Leader")
                    try:
                        self.spms_create_task(
                            connection=connection,
                            cursor=cursor,
                            task_type="assigned",
                            document_id=document_id,
                            user_id=ba_leader,
                            task_name=f"Review {doc_type}",
                            task_description=f"Decide on whether the {doc_type} for this project ({project['title']}) needs further revisions before being sent for final approval.",
                        )
                    except Exception as e:
                        input(e)

            # If the status is inapproval, create an assigned task for the directorate
            elif status == "inapproval":
                print("In Approval. Getting Directorate")
                try:
                    directorate = self.spms_get_directorate_id(
                        connection=connection,
                        cursor=cursor,
                    )
                except Exception as e:
                    input(e)
                else:
                    try:
                        print("Assigning Task to Leader")
                        self.spms_create_task(
                            connection=connection,
                            cursor=cursor,
                            task_type="assigned",
                            document_id=document_id,
                            user_id=directorate,
                            task_name=f"Review {doc_type} for Final Approval",
                            task_description=(
                                f"Decide on whether the {doc_type} for this project is okay to be included in the Annual Report. Project: {project['title']}"
                                if doc_type == "Progress Report"
                                else f"Decide on whether the {doc_type} for this project is satisfactory. Project: {project['title']}"
                            ),
                        )
                    except Exception as e:
                        input(e)

            # If the status is revising or new
            elif status == "revising" or status == "new":
                print("New or Revising. Getting Members")

                # Get the members of that project
                try:
                    members = self.spms_get_project_members(
                        connection=connection, cursor=cursor, project_id=project["id"]
                    )
                except Exception as e:
                    input(e)
                else:
                    # input(members)
                    # If members is empty, create a personal task for the business area leader to add them
                    if members == []:
                        print("No members, creating personal add members task for BA")
                        ba_leader = self.spms_get_ba_leader_from_project_ba(
                            connection=connection,
                            cursor=cursor,
                            business_area_id=project["business_area_id"],
                        )

                        self.spms_create_project_task(
                            connection=connection,
                            cursor=cursor,
                            task_type="assigned",
                            project_id=project["id"],
                            user_id=ba_leader,
                            task_name=f"Add Project Members",
                            task_description=f"The project has no members. Please add them or remove the project.",
                        )
                    else:
                        # For each member, create an assigned task depending on the state of the document.
                        for member in members:
                            # Ignore external members
                            if not member["is_staff"]:
                                continue
                            # Use new_sql to create task for staff members
                            if status == "new":
                                try:
                                    print("New. Assigning task to members.")

                                    self.spms_create_task(
                                        connection=connection,
                                        cursor=cursor,
                                        task_type="assigned",
                                        document_id=document_id,
                                        user_id=member["id"],
                                        task_name=f"New {doc_type} Assigned",
                                        task_description=f"A new {doc_type} is assigned to you for this project. Please review and take appropriate action. Project: {project['title']}",
                                    )
                                except Exception as e:
                                    input(e)
                            elif status == "revising":
                                try:
                                    print("Revising. Assigning task to members.")

                                    self.spms_create_task(
                                        connection=connection,
                                        cursor=cursor,
                                        task_type="assigned",
                                        document_id=document_id,
                                        user_id=member["id"],
                                        task_name=f"{doc_type} Revision Required",
                                        task_description=f"Your input is required for revising the {doc_type} of this project. Please review and make necessary changes. Project: {project['title']}",
                                    )
                                except Exception as e:
                                    input(e)

    def spms_get_project_members(self, connection, cursor, project_id):
        # Construct the SQL
        sql = """
        SELECT user_id FROM projects_projectmember
        WHERE project_id = %s;
        """

        # Execute the raw SQL query with the given parameters
        cursor.execute(sql, (project_id,))

        # Fetch all rows (project members' user_id) from the cursor
        rows = cursor.fetchall()

        # If no rows are returned, return empty array
        if not rows:
            print("No members apparently. Returning Empty array..")
            return []

        # Extract the user_ids from the result
        user_ids = [row[0] for row in rows]

        # Construct the SQL for fetching user details based on the user_ids
        user_sql = """
        SELECT id, is_staff FROM users_user 
        WHERE id = ANY(%s);
        """

        # Execute the raw SQL query with the given parameters to fetch user details
        cursor.execute(user_sql, (user_ids,))

        # Fetch all rows (users) from the cursor
        user_rows = cursor.fetchall()

        # Use pandas to convert the result into a DataFrame
        df = self.pd.DataFrame(user_rows, columns=["id", "is_staff"])

        # Convert DataFrame to list of dictionaries
        users = []
        for _, row in df.iterrows():
            user = {
                "id": row["id"],
                "is_staff": row["is_staff"],
            }
            users.append(user)

        print("Users have been fetched!")

        return users

    def spms_calculate_new_report_id(self, old_report_id, doc):
        report_dict = {
            1: 1,  # 2014
            2: 2,  # 2015
            5: 3,  # 2016
            6: 4,  # 2017
            7: 5,  # 2018
            8: 6,  # 2019
            9: 7,  # 2020
            10: 8,  # 2021
            11: 9,  # 2022
            12: 10,  # 2023
        }

        new_value = report_dict[old_report_id]
        print(f"Old report_id: {old_report_id} (Year: {doc['year']})")
        print(f"New report_id: {new_value} (Year: {doc['year']})")
        return new_value

    def spms_create_document_comments(self):
        print("Setting Comments for each document")

        # Open the file and create the dataframe
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "django_comments.csv"
            )
            comments = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        comment_df = comments[
            [
                "id",
                "content_type_id",
                "object_pk",
                "user_id",
                "comment",
                "submit_date",
                "ip_address",
                "is_public",
                "is_removed",
            ]
        ]

        # Open a connection to the database
        # updated_at,

        # Construct SQL for base document comment
        # old_id, %s,

        sql = """
            BEGIN;
            INSERT INTO communications_comment (
                created_at,
                updated_at,
                user_id,
                document_id,
                text,
                ip_address,
                is_public,
                is_removed
            ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        content_type_dict = {
            19: "progressreport",
            20: "studentreport",
            21: "projectclosure",
            22: "projectplan",
            24: "conceptplan",
        }

        def assign_new_content_type(old_content_type):
            new_val = content_type_dict[old_content_type]
            return new_val

        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()

        # Execute sql per row
        for index, comment in comment_df.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating Project Document Comment ({comment['id']})...{self.misc.bcolors.ENDC}"
            )
            new_document_id = self.spms_get_document_id_by_old_id(
                connection=connection, cursor=cursor, old_id=comment["object_pk"]
            )

            # Get new values related to each base document entry
            old_id = int(comment["id"])
            created_at = comment["submit_date"]
            updated_at = dt.now()
            print("Getting new user...")
            new_user_id = self.spms_get_user_by_old_id(
                cursor=cursor,
                connection=connection,
                old_id=comment["user_id"],
            )
            # content_type = assign_new_content_type(comment['content_type_id'])
            print("Getting new document...")

            text = None if self.pd.isna(comment["comment"]) else comment["comment"]
            ip_address = (
                None if self.pd.isna(comment["ip_address"]) else comment["ip_address"]
            )
            is_public = comment["is_public"]
            is_removed = comment["is_removed"]

            # updated_at = (
            #     current_datetime
            #     if self.pd.isna(comment["modified"])
            #     else comment["modified"]
            # )

            try:
                if new_document_id is not None:
                    # Start a transaction
                    cursor = connection.cursor()
                    cursor.execute(
                        sql,
                        (
                            # old_id,
                            created_at,
                            updated_at,
                            new_user_id,
                            new_document_id,
                            text,
                            ip_address,
                            is_public,
                            is_removed,
                        ),
                    )
            except Exception as e:
                print(
                    # old_id,
                    created_at,
                    new_user_id,
                    new_document_id,
                    text,
                    ip_address,
                    is_public,
                    is_removed,
                )
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Doc Comment (OLD ID: {old_id}): {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)

                # Rollback the transaction
                connection.rollback()

            else:
                if new_document_id is not None:
                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}Doc Comment (OLD ID: {old_id}) Created!{self.misc.bcolors.ENDC}"
                    )
                else:
                    f"{self.misc.bcolors.WARNING}Doc Comment (OLD ID: {old_id}) Skipped...{self.misc.bcolors.ENDC}"

            finally:
                if new_document_id is not None:
                    connection.commit()

    def spms_check_if_project_with_name_exists(self, cursor, name):
        # Convert the name to lowercase for case-insensitive comparison
        lowercase_name = name.lower()

        # Execute the query to check if a project with the given title exists
        cursor.execute(
            "SELECT COUNT(*) FROM projects_project WHERE LOWER(title) = %s",
            (lowercase_name,),
        )
        count = cursor.fetchone()[0]

        if count == 0:
            # No project with the given title exists, set project_name to the name
            project_name = name
        else:
            # A project with the given title exists, find the next available project name
            check_num = 1
            while True:
                new_name = f"(DUPLICATE {check_num}) {name}"
                lowercase_new_name = new_name.lower()
                cursor.execute(
                    "SELECT COUNT(*) FROM projects_project WHERE LOWER(title) = %s",
                    (lowercase_new_name,),
                )
                count = cursor.fetchone()[0]
                if count == 0:
                    project_name = new_name
                    break
                check_num += 1

        # Return the project_name with the desired case sensitivity
        return project_name

    def spms_create_annual_reports(self):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Reports...{self.misc.bcolors.ENDC}"
        )
        # Establishing connection and fetching some necessary data:
        (
            cursor,
            connection,
        ) = self.spms_establish_dest_db_connection_and_return_cursor_conn()
        connection.autocommit = False

        # Get the user with the name "jp" if it exists, in case we need
        superuser_id = self.spms_get_superuser(connection=connection, cursor=cursor)

        # Get the current date and time
        current_datetime = dt.now()

        # ======================================================================================
        # OPENING REPORTS FILE

        # Load the reports csv file into a data frame
        try:
            file_path = self.os.path.join(
                self.file_handler.clean_directory, "pythia_ararreport.csv"
            )
            reports_df = self.file_handler.read_csv_and_prepare_df(file_path)
        except Exception as e:
            self.misc.nli(f"{self.misc.bcolors.FAIL}Error: {e}{self.misc.bcolors.ENDC}")
        else:
            print(f"{self.misc.bcolors.OKGREEN}File loaded!{self.misc.bcolors.ENDC}")

        # Establish columns we want to use in df
        reports_df = reports_df[
            [
                "id",
                "creator_id",
                "modifier_id",
                "created",
                "modified",
                "year",
                "dm",
                "pub",
                "date_open",
                "date_closed",
                "research_intro",
                "student_intro",
                "sds_intro",
                "sds_chapterimage",
                "sds_orgchart",
                "research_chapterimage",
                "partnerships_chapterimage",
                "studentprojects_chapterimage",
                "publications_chapterimage",
                "collaboration_chapterimage",
                "pdf",
                "coverpage",
                "rearcoverpage",
            ]
        ]

        # ======================================================================================

        # Create a entry for each row in csv
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Creating ARAR entries...{self.misc.bcolors.ENDC}"
        )

        # Divisions missing for now
        reports_sql = """
            BEGIN;
            INSERT INTO documents_annualreport (
                old_id, 
                creator_id,
                modifier_id,
                created_at, 
                updated_at,
                service_delivery_intro,
                research_intro,
                student_intro,
                publications,
                date_open,
                date_closed,
                year, 
                dm,
                is_published,
                pdf_generation_in_progress
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            COMMIT;
        """

        # Rearrange the DataFrame based on the "year" column to ensure pk starts at lowest one.
        reports_df.sort_values("year", inplace=True)

        for index, report in reports_df.iterrows():
            print(
                f"{self.misc.bcolors.WARNING}Creating entry for {report['year']}...{self.misc.bcolors.ENDC}"
            )

            try:
                old_id = report["id"]
                new_creator_id = (
                    report["creator_id"]
                    if report["creator_id"] == 101073
                    else self.spms_get_user_by_old_id(
                        connection=connection,
                        cursor=cursor,
                        old_id=report["creator_id"],
                    )
                )
                new_modifier_id = (
                    report["modifier_id"]
                    if report["creator_id"] == 101073
                    else self.spms_get_user_by_old_id(
                        connection=connection,
                        cursor=cursor,
                        old_id=report["modifier_id"],
                    )
                )
                # NOTE: New table doesnt have divisions
                # create a new dictionary that repopulates divisions with new divisions
                # new_divisions_ids = report["divisions"]  # departmental_services

                is_published = True if report["year"] != 2023 else False

                # Start a transaction
                cursor = connection.cursor()
                cursor.execute(
                    reports_sql,
                    (
                        old_id,
                        new_creator_id,
                        new_modifier_id,
                        report["created"],
                        report["modified"],
                        (
                            report["sds_intro"]
                            if not self.pd.isna(report["sds_intro"])
                            else None
                        ),
                        (
                            report["research_intro"]
                            if not self.pd.isna(report["research_intro"])
                            else None
                        ),
                        (
                            report["student_intro"]
                            if not self.pd.isna(report["student_intro"])
                            else None
                        ),
                        (
                            report["pub"] if not self.pd.isna(report["pub"]) else None
                        ),  # publications
                        report["date_open"],
                        report["date_closed"],
                        report["year"],
                        report["dm"] if not self.pd.isna(report["dm"]) else None,
                        is_published,
                        False,
                    ),
                )
            except Exception as e:
                print(
                    old_id,
                    new_creator_id,
                    new_modifier_id,
                    report["created"],
                    report["modified"],
                    report["date_open"],
                    report["date_closed"],
                    report["year"],
                )
                self.misc.nli(
                    f"{self.misc.bcolors.FAIL}Error creating Report ({report['year']}: {str(e)}{self.misc.bcolors.ENDC}"
                )
                # Print the complete traceback information
                traceback_str = traceback.format_exc()
                print(traceback_str)
                # Rollback the transaction
                connection.rollback()

            else:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Report ({report['year']}) Created!{self.misc.bcolors.ENDC}"
                )

            finally:
                connection.commit()

            related_report_id = self.spms_get_new_report_id_by_year(
                connection=connection, cursor=cursor, year=report["year"]
            )

            # Create the media (images/pdfs)
            self.misc.nls(
                f"{self.misc.bcolors.WARNING}Creating Report Media{self.misc.bcolors.ENDC}"
            )

            old_media_kinds = [
                "rearcoverpage",
                "coverpage",
                "collaboration_chapterimage",
                "publications_chapterimage",
                "studentprojects_chapterimage",
                "partnerships_chapterimage",
                "research_chapterimage",
                "sds_orgchart",
                "sds_chapterimage",
                "pdf",
            ]

            # Convert back to df from series to run below logic
            if isinstance(report, self.pd.Series):
                report = self.pd.DataFrame(report).T  # Convert Series to DataFrame

            # Load the settings
            print(
                f"{self.misc.bcolors.WARNING}Setting the DJANGO_SETTINGS_MODULE...{self.misc.bcolors.ENDC}"
            )
            # Set the DJANGO_SETTINGS_MODULE environment variable
            self.os.environ.setdefault(
                "DJANGO_SETTINGS_MODULE", f"{self.django_project_path}.config.settings"
            )

            print(self.os.getenv("DJANGO_SETTINGS_MODULE"))

            # Configure Django settings
            # settings.configure()

            for media_column in report.columns:
                if media_column in old_media_kinds:
                    media_value = report[media_column]
                    kind = (
                        media_column
                        if not self.pd.isna(media_value.values[0])
                        else None
                    )
                    if kind == None:
                        continue
                    else:
                        new_kind_value = self.spms_assign_new_report_media_kind(kind)
                        file_path = os.path.join(
                            self.django_project_path,
                            "dumped_media",
                            media_value.values[0],
                        )
                        print(file_path)
                        if kind != "pdf":
                            with open(file_path, "rb") as file:
                                # Create an InMemoryUploadedFile
                                uploaded_file = InMemoryUploadedFile(
                                    file,
                                    None,
                                    os.path.basename(file_path),
                                    "image/jpeg",  # Adjust the content type based on your file type
                                    len(file.read()),  # Pass the file content length
                                    None,
                                )

                                # Save the file to the default storage
                                saved_file = default_storage.save(
                                    f"annual_reports/images/{uploaded_file.name}",
                                    uploaded_file,
                                )

                                self.spms_create_report_media(
                                    connection=connection,
                                    cursor=cursor,
                                    data=saved_file,
                                    kind=new_kind_value,
                                    related_report_id=related_report_id,
                                )
                        else:
                            with open(file_path, "rb") as file:
                                # Create an InMemoryUploadedFile
                                uploaded_file = InMemoryUploadedFile(
                                    file,
                                    None,
                                    os.path.basename(file_path),
                                    "application/pdf",  # Adjust the content type based on your file type
                                    len(file.read()),  # Pass the file content length
                                    None,
                                )

                                # Save the file to the default storage
                                saved_file = default_storage.save(
                                    f"annual_reports/pdfs/{uploaded_file.name}",
                                    uploaded_file,
                                )

                                self.spms_create_report_pdf(
                                    connection=connection,
                                    cursor=cursor,
                                    data=saved_file,
                                    # kind=new_kind_value,
                                    related_report_id=related_report_id,
                                )

        cursor.close()
        # connection.close()

    def spms_assign_new_report_media_kind(self, old_kind_value):
        new_kind_dict = {
            "rearcoverpage": "rear_cover",
            "coverpage": "cover",
            "collaboration_chapterimage": "collaborations",
            "publications_chapterimage": "publications",
            "studentprojects_chapterimage": "student_projects",
            "partnerships_chapterimage": "partnerships",
            "research_chapterimage": "research",
            "sds_orgchart": "sdchart",
            "sds_chapterimage": "service_delivery",
            "pdf": "pdf",
        }

        new_value = new_kind_dict[old_kind_value]
        return new_value

    #  medias = [
    #             cover_page,
    #             sds_chapter_image,
    #             sds_org_chart,
    #             research_chapter_image,
    #             partnerships_chapter_image,
    #             student_projects_chapter_image,
    #             publications_chapter_image,
    #             collaboration_chapter_image,
    #             pdf,
    #             rear_cover_page,
    #         ]

    def create_project_document_pdf(
        self, connection, cursor, related_project_id, related_document_id, data
    ):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Project Doc PDF for DOC ID {related_document_id}...{self.misc.bcolors.ENDC}"
        )
        print(f"Proj: {related_project_id}")

        try:
            project_document_pdf_sql = """
                BEGIN;
                INSERT INTO medias_projectdocumentpdf (
                    created_at,
                    updated_at,
                    file, 
                    document_id,
                    project_id
                ) VALUES ( %s, %s, %s, %s, %s);
                COMMIT;
            """

            # old_file, %s,
            # old_file = data
            # kind = kind
            # old_file,
            # kind,

            created_at = dt.now()
            updated_at = dt.now()
            file = data
            document = related_document_id
            project = related_project_id
            # uploader = self.spms_get_superuser(connection, cursor)

            # Check if pdf matching doc already exists (data issues)
            already_present = self.spms_check_proj_pdf_exists(
                doc_id=document, cursor=cursor, connection=connection
            )
            if already_present == False:
                cursor.execute(
                    project_document_pdf_sql,
                    (
                        created_at,
                        updated_at,
                        file,
                        document,
                        project,
                    ),
                )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Error Creating Project Document PDF for Doc ID {related_document_id}: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Project Document PDF Created!{self.misc.bcolors.ENDC}"
            )
            connection.commit()
        # finally:

    def spms_create_report_pdf(self, connection, cursor, related_report_id, data):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Report PDF for NEW REPORT ID {related_report_id}...{self.misc.bcolors.ENDC}"
        )

        try:
            annual_report_media_sql = """
                BEGIN;
                INSERT INTO medias_annualreportpdf (
                    created_at,
                    updated_at,
                    file, 
                    report_id,
                    creator_id
                ) VALUES ( %s, %s, %s, %s, %s);
                COMMIT;

            """
            # old_file, %s,
            # old_file = data
            # kind = kind
            # old_file,
            # kind,

            created_at = dt.now()
            updated_at = dt.now()
            file = data
            report = related_report_id
            uploader = self.spms_get_superuser(connection, cursor)

            cursor.execute(
                annual_report_media_sql,
                (
                    created_at,
                    updated_at,
                    file,
                    report,
                    uploader,
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Creating Report PDF for NEW REPORT ID {related_report_id}: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Report PDF Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

    def spms_create_report_media(
        self, connection, cursor, kind, related_report_id, data
    ):
        self.misc.nls(
            f"{self.misc.bcolors.OKBLUE}Creating Report Media for NEW REPORT ID {related_report_id}...{self.misc.bcolors.ENDC}"
        )

        try:
            annual_report_media_sql = """
                BEGIN;
                INSERT INTO medias_annualreportmedia (
                    created_at,
                    updated_at,
                    file, 
                    kind,
                    report_id,
                    uploader_id
                ) VALUES ( %s, %s, %s, %s, %s, %s);
                COMMIT;

            """
            # old_file, %s,

            created_at = dt.now()
            updated_at = dt.now()
            # old_file = data
            file = data
            kind = kind
            report = related_report_id
            uploader = self.spms_get_superuser(connection, cursor)

            cursor.execute(
                annual_report_media_sql,
                (
                    created_at,
                    updated_at,
                    # old_file,
                    file,
                    kind,
                    report,
                    uploader,
                ),
            )

        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Creating Report Media for NEW REPORT ID {related_report_id}: {str(e)}{self.misc.bcolors.ENDC}"
            )
            # Rollback the transaction
            connection.rollback()

        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Report Media Created!{self.misc.bcolors.ENDC}"
            )
        finally:
            connection.commit()

    # Get the image upload URL from cloudflare
    def spms_get_cf_images_upload_url(self):
        env = environ.Env()
        account = env("CF_ACCOUNT_ID")
        api_token = env("CF_IMAGES_TOKEN")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account}/images/v2/direct_upload"
        one_time_url = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_token}",
                # "Content-Type": "multipart/form-data",
            },
        )

        one_time_url = one_time_url.json()
        result = one_time_url.get("result")
        print(f"{result}")
        return (result.get("id"), result.get("uploadURL"))

    # Upload the downloaded file to the cloudflare images server and return the link to
    # the new cloudflare image location
    def spms_upload_to_cf_url(self, url, file_path):
        # Read the image file
        with open(file_path, "rb") as file:
            filename = self.os.path.basename(file_path)
            file_content = file.read()
            http = urllib3.PoolManager()
            fields = {"file": (filename, file_content)}
            response = http.request("POST", url, fields=fields)

            # # Generate the boundary
            # boundary = self.generate_boundary()

            # Create the form data with the boundary
            # form_data = {"file": (file_path, image_data, "application/octet-stream")}

            # # Set the headers with the boundary
            # headers = {"Content-Type": "multipart/form-data"}

            # # Make the request
            # response = requests.post(url, files=files, headers=headers)

            # Return
            if response.status == 200:
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}File uploaded{self.misc.bcolors.ENDC}"
                )
                data = json.loads(response.data.decode("utf-8"))
                variants = data["result"]["variants"]
                variants_string = variants[0] if variants else None
                print(f"Variants string: {variants_string}")
                return variants_string

                # return response.json()
            else:
                print(response)
                error_message = response.text
                print(
                    response.status,
                    error_message,
                )
                raise Exception(
                    "Failed to upload file to cloudflare",
                )
