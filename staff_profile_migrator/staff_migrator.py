# A program to migrate data from science.dbca.wa.gov.au into this system

# CSV strucutures:

from cgitb import text
from documents.models import Publication
from projects.models import ProjectMember
import users


class StaffSorter(csv_file):
    # For handling any emails that do not match
    def handle_non_matching_email_rows():
        pass

    # For handling any emails that match but are not staff
    def handle_matches_that_arent_staff():
        pass

    # For getting a list of users that are staff and match an email in the Users model
    def create_and_return_matching_email_row_subset():
        pass


# REQUIRED MODELS:
# -Public Profile
#     - user (foreign key to users.User - used to get title (from user.profile), first_name, last_name, and branch (user.work.branch))
#     - dbca_position_title (char field 200)
#     - keyword_tags (textfield)
#     - about_me (textfield)
#     - expertise (textfield)
#     - projects (one to many to ProjectMember.project)
#     - publications (one to many to AdditionalPublicationEntry)
#     - employment (one to many to EmploymentEntry)
#     - education (one to many to EducationEntry)
#     - is_hidden (boolean)
#     - aucode (charfield 50)
#     - created_at
#     - updated_at

#     - Projects (pull directly from SPMS)

#     - Publication (Will pull from library database and reformat)

#     - AdditionalPublication
#         - public_profile, year_published, entry

#     - Employment
#         - public_profile, position_title, start_year, end_year, section, employer,

#     - Education
#         - public_profile, qualification_field, with_honours, qualification_kind, qualification_name, start_year, end_year, institution, city, country


class DatabaseObjectCreator:
    pass

    # first_name

    # staff.csv:
    # ------------------------------
    # id (IGNORE)
    # corporate_user_id (IGNORE)
    # aucode (RETAIN - UID that links to Library data)
    # centreid (USE USER WORK MODEL AND MATCH WITH BRANCH - OR JUST REPLACE WITH BRANCH/BA)
    # title (USE USER PROFILE MODEL)
    # givenname (USE USER MODEL)
    # midinitial (USE USER PROFILE MODEL)
    # surname (USE USER MODEL)
    # namedir (IGNORE)
    # directphone (IGNORE)
    # directfax (IGNORE)
    # email (MATCH ON USER MODEL)
    # profile
    # expertise
    # cv
    # projects
    # publications (make default <p></p>, retain)
    # updated (RETAIN - rename to updated_at)
    # hidden (RETAIN)

    # staff_keywords.csv:
    # ------------------------------
    # id
    # staffid
    # keyword

    # additional_publications.csv:
    # ------------------------------
    # id
    # staffid
    # year_of_publication
    # entry
    # entry_plain
