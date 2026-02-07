"""
One-time data migration command to copy caretaker data from adminoptions to caretakers app.

This command:
1. Checks if migration is needed (adminoptions.Caretaker table exists)
2. Copies data from adminoptions_caretaker to caretakers_caretaker
3. Is idempotent - safe to run multiple times
4. Validates data after migration

Usage:
    python manage.py migrate_caretaker_data
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from psycopg2 import sql


class Command(BaseCommand):
    help = "Migrate caretaker data from adminoptions to caretakers app (one-time operation)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("\n=== DRY RUN MODE ==="))

        self.stdout.write("\n=== Caretaker Data Migration ===")

        # Check if source table exists
        if not self._table_exists("adminoptions_caretaker"):
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Source table (adminoptions_caretaker) does not exist"
                )
            )
            self.stdout.write(
                self.style.SUCCESS("✓ Migration already completed or not needed")
            )
            return

        # Check if destination table exists
        if not self._table_exists("caretakers_caretaker"):
            self.stdout.write(
                self.style.ERROR(
                    "✗ Destination table (caretakers_caretaker) does not exist"
                )
            )
            self.stdout.write(
                self.style.ERROR("✗ Run migrations first: python manage.py migrate")
            )
            return

        # Get counts
        source_count = self._get_table_count("adminoptions_caretaker")
        dest_count_before = self._get_table_count("caretakers_caretaker")

        self.stdout.write(f"Source table records: {source_count}")
        self.stdout.write(f"Destination table records (before): {dest_count_before}")

        if source_count == 0:
            self.stdout.write(
                self.style.SUCCESS("✓ No data to migrate (source table empty)")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nWould migrate {source_count} records".format(
                        source_count=source_count
                    )
                )
            )
            self.stdout.write(
                self.style.WARNING("Run without --dry-run to perform migration")
            )
            return

        # Perform migration
        try:
            with transaction.atomic():
                copied, updated = self._migrate_data()

                dest_count_after = self._get_table_count("caretakers_caretaker")

                self.stdout.write(
                    self.style.SUCCESS("\n✓ Migration completed successfully")
                )
                self.stdout.write(self.style.SUCCESS(f"✓ Copied {copied} new records"))
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Updated {updated} existing records")
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Total records in destination: {dest_count_after}"
                    )
                )

                # Validate
                if dest_count_after < source_count:
                    self.stdout.write(
                        self.style.WARNING(
                            "⚠ Warning: Destination has fewer records than source"
                        )
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            "  This may be expected if duplicates were merged"
                        )
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Migration failed: {str(e)}"))
            raise

    def _table_exists(self, table_name):
        """Check if a table exists in the database."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                );
            """,
                [table_name],
            )
            return cursor.fetchone()[0]

    def _get_table_count(self, table_name):
        """Get the number of records in a table."""
        with connection.cursor() as cursor:
            # Use SQL identifier to prevent injection (table_name is hardcoded but bandit flags it)
            cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name))
            )
            return cursor.fetchone()[0]

    def _migrate_data(self):
        """
        Migrate data from adminoptions_caretaker to caretakers_caretaker.
        Returns (copied_count, updated_count).
        """
        with connection.cursor() as cursor:
            # Insert new records that don't exist in destination
            cursor.execute(
                """
                INSERT INTO caretakers_caretaker
                    (id, user_id, caretaker_id, end_date, reason, notes, created_at, updated_at)
                SELECT
                    src.id,
                    src.user_id,
                    src.caretaker_id,
                    src.end_date,
                    src.reason,
                    src.notes,
                    src.created_at,
                    src.updated_at
                FROM adminoptions_caretaker src
                WHERE NOT EXISTS (
                    SELECT 1 FROM caretakers_caretaker dest
                    WHERE dest.user_id = src.user_id
                    AND dest.caretaker_id = src.caretaker_id
                )
                ON CONFLICT (user_id, caretaker_id) DO NOTHING;
            """
            )
            copied_count = cursor.rowcount

            # Update existing records to ensure data is current
            cursor.execute(
                """
                UPDATE caretakers_caretaker dest
                SET
                    end_date = src.end_date,
                    reason = src.reason,
                    notes = src.notes,
                    created_at = src.created_at,
                    updated_at = src.updated_at
                FROM adminoptions_caretaker src
                WHERE dest.user_id = src.user_id
                AND dest.caretaker_id = src.caretaker_id
                AND (
                    dest.end_date IS DISTINCT FROM src.end_date OR
                    dest.reason IS DISTINCT FROM src.reason OR
                    dest.notes IS DISTINCT FROM src.notes OR
                    dest.created_at IS DISTINCT FROM src.created_at OR
                    dest.updated_at IS DISTINCT FROM src.updated_at
                );
            """
            )
            updated_count = cursor.rowcount

            return copied_count, updated_count
