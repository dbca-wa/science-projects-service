import csv, os
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User, PublicStaffProfile, KeywordTag


class Command(BaseCommand):
    help = "Migrate staff data from CSV files"

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(
            os.path.abspath(__file__)
        )  # Get the directory of the current script
        staff_file_path = os.path.join(base_dir, "staff.csv")
        staff_keywords_file_path = os.path.join(base_dir, "staff-keywords.csv")
        unmatched_users_csv_path = os.path.join(base_dir, "unmatched_users.csv")

        self.migrate_staff_data(
            staff_file_path, staff_keywords_file_path, unmatched_users_csv_path
        )

    @transaction.atomic
    def migrate_staff_data(
        self, staff_file_path, staff_keywords_file_path, unmatched_users_csv_path
    ):
        staff_data = {}
        unmatched_users = []
        long_keywords = []

        # Read staff data and store it in a dictionary for quick access
        with open(staff_file_path, newline="") as staff_file:
            staff_reader = csv.DictReader(staff_file)
            fieldnames = staff_reader.fieldnames  # Capture the original fieldnames

            for row in staff_reader:
                staff_id = row["id"]
                email_prefix = row["email"].split("@")[0].lower()
                row["email_prefix"] = (
                    email_prefix  # Store email prefix in each row for later use
                )
                staff_data[staff_id] = row

        # Read keyword data and link to corresponding staff profiles
        with open(staff_keywords_file_path, newline="") as keywords_file:
            keywords_reader = csv.DictReader(keywords_file)

            for row in keywords_reader:
                staff_id = row["staffid"]
                keyword = row["keyword"]

                if staff_id in staff_data:
                    email_prefix = staff_data[staff_id]["email_prefix"]

                    # Find all users matching the email prefix
                    users = User.objects.filter(email__startswith=email_prefix)

                    if users.exists():
                        for user in users:
                            # Get or create the staff profile
                            staff_profile, created = (
                                PublicStaffProfile.objects.get_or_create(
                                    user=user,
                                    defaults={
                                        "aucode": staff_data[staff_id]["aucode"],
                                        "about": staff_data[staff_id]["profile"],
                                        "expertise": staff_data[staff_id]["expertise"],
                                        "updated_at": staff_data[staff_id]["updated"],
                                        "hidden": staff_data[staff_id]["hidden"],
                                    },
                                )
                            )

                            # Split the keyword by commas into individual keywords
                            keywords = [kw.strip() for kw in keyword.split(",")]

                            for kw in keywords:
                                if len(kw) > 50:
                                    long_keywords.append(
                                        {"email": user.email, "keyword": kw}
                                    )

                                # Truncate the keyword if necessary and add it to the profile
                                keyword_tag, _ = KeywordTag.objects.get_or_create(
                                    name=kw[:50]
                                )
                                staff_profile.keyword_tags.add(keyword_tag)
                    else:
                        print(
                            f"No matching user found for email prefix: {email_prefix}"
                        )
                        unmatched_users.append(
                            {
                                k: v
                                for k, v in staff_data[staff_id].items()
                                if k in fieldnames
                            }
                        )
                else:
                    print(f"No staff data found for staff ID: {staff_id}")

        # Write unmatched users to a new CSV
        if unmatched_users:
            with open(unmatched_users_csv_path, mode="w", newline="") as unmatched_file:
                writer = csv.DictWriter(unmatched_file, fieldnames=fieldnames)

                writer.writeheader()
                for row in unmatched_users:
                    writer.writerow(row)

        # Print long keywords at the end
        if long_keywords:
            print("\nKeywords longer than 50 characters:")
            for item in long_keywords:
                print(f"Email: {item['email']}, Keyword: {item['keyword']}")

        print("Staff data migration completed.")
