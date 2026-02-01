"""
Management command to fix all user-related primary key sequences.

This fixes the "duplicate key value violates unique constraint" error
that occurs when PostgreSQL sequences are out of sync with actual data.

Usage:
    python manage.py fix_user_sequence
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Reset all user-related sequences to the correct values"

    def handle(self, *args, **options):
        # List of all tables and their sequences that need to be fixed
        tables_to_fix = [
            ("users_user", "users_user_id_seq"),
            ("users_publicstaffprofile", "users_publicstaffprofile_id_seq"),
            ("users_userprofile", "users_userprofile_id_seq"),
            ("users_userwork", "users_userwork_id_seq"),
            ("contacts_usercontact", "contacts_usercontact_id_seq"),
        ]

        with connection.cursor() as cursor:
            for table_name, seq_name in tables_to_fix:
                try:
                    # Get current max ID
                    cursor.execute(f"SELECT MAX(id) FROM {table_name};")
                    max_id = cursor.fetchone()[0] or 0

                    # Get current sequence value
                    cursor.execute(f"SELECT last_value FROM {seq_name};")
                    current_seq = cursor.fetchone()[0]

                    self.stdout.write(f"\n{table_name}:")
                    self.stdout.write(f"  Current max ID: {max_id}")
                    self.stdout.write(f"  Current sequence value: {current_seq}")

                    if current_seq <= max_id:
                        # Reset the sequence
                        new_seq = max_id + 1
                        cursor.execute(f"SELECT setval('{seq_name}', {new_seq});")
                        self.stdout.write(
                            self.style.SUCCESS(f"  Sequence reset to {new_seq}")
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS("  Sequence is already correct")
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Could not fix {table_name}: {e}")
                    )

        self.stdout.write(self.style.SUCCESS("\nAll sequences checked!"))
