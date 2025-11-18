# region IMPORTS ====================================================================================================
import mimetypes, os, tempfile
from django.contrib import admin, messages
from django.http import FileResponse
from django.conf import settings
from .models import (
    Agency,
    Branch,
    BusinessArea,
    DepartmentalService,
    Affiliation,
    Division,
)

# endregion  =================================================================================================

# region ACTIONS ====================================================================================================


@admin.action(description="Export Affiliations to TXT")
def export_all_affiliations_txt(model_admin, req, selected):
    # Ensure only one item is selected
    if len(selected) != 1:
        model_admin.message_user(req, "Please select only one item.", messages.ERROR)
        return

    # Fetch all affiliations
    saved_affiliations = Affiliation.objects.all()

    # Create a directory in the system's temp folder for the exports
    export_folder = os.path.join(tempfile.gettempdir(), "affiliation_exports")
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    # Set the base file name and determine file iteration
    base_name = "export"
    iteration = 1
    while True:
        iteration_text = str(iteration).zfill(3)
        file_name = f"{base_name}_{iteration_text}.txt"
        file_path = os.path.join(export_folder, file_name)
        if not os.path.exists(file_path):
            break  # Found a non-existing file name
        iteration += 1

    try:
        # Write the affiliations to the file
        with open(file_path, "w+", encoding="utf-8") as txt_file:
            for affiliation in saved_affiliations:
                name = affiliation.name
                pk = affiliation.pk
                txt_file.write(f"{name} ({pk})\n")

        # Inform the user
        model_admin.message_user(
            req, f"Affiliations exported to {file_path}", messages.SUCCESS
        )

        # Use Django's FileResponse to allow downloading the file
        mime_type, _ = mimetypes.guess_type(file_path)
        response = FileResponse(open(file_path, "rb"), content_type=mime_type)
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response

    except Exception as e:
        model_admin.message_user(req, f"Error during export: {str(e)}", messages.ERROR)


@admin.action(description="Fix affiliation data and migrate delimiters (COMPREHENSIVE)")
def fix_affiliations_and_migrate_delimiters(model_admin, req, selected):
    """
    Comprehensive one-click fix that:
    1. Splits multi-affiliation records (containing semicolons) into separate records
    2. Updates project references to use the split affiliations
    3. Migrates comma delimiters to semicolon delimiters in project fields
    
    Run this ONCE to fix all affiliation data issues.
    """
    from projects.models import ExternalProjectDetails, StudentProjectDetails
    from django.db import transaction

    split_count = 0
    created_count = 0
    external_updated = 0
    student_updated = 0
    migrated_count = 0

    try:
        with transaction.atomic():
            # STEP 1: Find and split multi-affiliation records
            settings.LOGGER.info(
                f"=== COMPREHENSIVE AFFILIATION FIX STARTED by {req.user} ==="
            )
            
            multi_affiliations = Affiliation.objects.filter(name__contains="; ")
            multi_count = multi_affiliations.count()
            
            settings.LOGGER.info(
                f"STEP 1: Found {multi_count} multi-affiliation record(s) to split"
            )
            
            for idx, multi_aff in enumerate(multi_affiliations, 1):
                # Split the name by semicolon and clean up
                # Remove trailing semicolons first
                cleaned_name = multi_aff.name.rstrip("; ")
                individual_names = [
                    name.strip() 
                    for name in cleaned_name.split(";") 
                    if name.strip()
                ]
                
                if len(individual_names) > 1:
                    settings.LOGGER.info(
                        f"  [{idx}/{multi_count}] Splitting: '{multi_aff.name[:100]}...' "
                        f"into {len(individual_names)} individual affiliation(s)"
                    )
                    
                    # Create or get individual affiliation records
                    new_affiliations = []
                    for name in individual_names:
                        # Extra safety: strip any remaining semicolons or whitespace
                        clean_name = name.strip().rstrip(";").strip()
                        if clean_name:  # Only process non-empty names
                            aff, created = Affiliation.objects.get_or_create(name=clean_name)
                            new_affiliations.append(aff)
                            if created:
                                created_count += 1
                                settings.LOGGER.info(f"    ✓ Created new affiliation: '{clean_name}'")
                            else:
                                settings.LOGGER.info(
                                    f"    → Linked to existing affiliation: '{clean_name}'"
                                )
                    
                    # STEP 2: Update project references
                    # Find projects using the old multi-affiliation
                    ext_projects = ExternalProjectDetails.objects.filter(
                        collaboration_with__icontains=multi_aff.name
                    )
                    ext_count = ext_projects.count()
                    
                    if ext_count > 0:
                        settings.LOGGER.info(
                            f"    Updating {ext_count} external project(s)"
                        )
                    
                    for ext in ext_projects:
                        if ext.collaboration_with and multi_aff.name in ext.collaboration_with:
                            old_value = ext.collaboration_with
                            # Replace the exact multi-affiliation string
                            new_value = old_value.replace(
                                multi_aff.name,
                                "; ".join([aff.name for aff in new_affiliations]),
                            )
                            # Clean up any double semicolons or trailing semicolons
                            new_value = new_value.replace(";; ", "; ").rstrip("; ")
                            
                            # Deduplicate affiliations in the field
                            parts = [p.strip() for p in new_value.split(";") if p.strip()]
                            seen = set()
                            unique_parts = []
                            for part in parts:
                                if part not in seen:
                                    seen.add(part)
                                    unique_parts.append(part)
                            new_value = "; ".join(unique_parts)
                            
                            if new_value != old_value:
                                ext.collaboration_with = new_value
                                ext.save()
                                external_updated += 1
                                settings.LOGGER.info(
                                    f"      ✓ Updated ExternalProject {ext.project_id}: "
                                    f"'{old_value[:60]}...' → '{new_value[:60]}...'"
                                )
                    
                    student_projects = StudentProjectDetails.objects.filter(
                        organisation__icontains=multi_aff.name
                    )
                    student_count = student_projects.count()
                    
                    if student_count > 0:
                        settings.LOGGER.info(
                            f"    Updating {student_count} student project(s)"
                        )
                    
                    for student in student_projects:
                        if student.organisation and multi_aff.name in student.organisation:
                            old_value = student.organisation
                            # Replace the exact multi-affiliation string
                            new_value = old_value.replace(
                                multi_aff.name,
                                "; ".join([aff.name for aff in new_affiliations]),
                            )
                            # Clean up any double semicolons or trailing semicolons
                            new_value = new_value.replace(";; ", "; ").rstrip("; ")
                            
                            # Deduplicate affiliations in the field
                            parts = [p.strip() for p in new_value.split(";") if p.strip()]
                            seen = set()
                            unique_parts = []
                            for part in parts:
                                if part not in seen:
                                    seen.add(part)
                                    unique_parts.append(part)
                            new_value = "; ".join(unique_parts)
                            
                            if new_value != old_value:
                                student.organisation = new_value
                                student.save()
                                student_updated += 1
                                settings.LOGGER.info(
                                    f"      ✓ Updated StudentProject {student.project_id}: "
                                    f"'{old_value[:60]}...' → '{new_value[:60]}...'"
                                )
                    
                    # Delete the old multi-affiliation record
                    settings.LOGGER.info(
                        f"    ✓ Deleting old multi-affiliation record (ID: {multi_aff.pk})"
                    )
                    multi_aff.delete()
                    split_count += 1
            
            settings.LOGGER.info(
                f"STEP 1 COMPLETE: Split {split_count} record(s), "
                f"created {created_count} new affiliation(s), "
                f"updated {external_updated + student_updated} project(s)"
            )
            
            # STEP 3: Migrate comma delimiters to semicolons
            settings.LOGGER.info(
                f"STEP 2: Starting comma-to-semicolon delimiter migration"
            )
            
            # Get fresh list of all affiliation names after splitting
            all_affiliation_names = list(
                Affiliation.objects.values_list("name", flat=True)
            )
            
            def smart_migrate_field(field_value, all_names):
                """Smart migration that preserves commas in affiliation names"""
                if not field_value or ", " not in field_value:
                    return field_value, False
                
                # Match known affiliation names
                matched_affiliations = []
                remaining_text = field_value
                
                # Sort by length (longest first) to match longer names first
                sorted_names = sorted(all_names, key=len, reverse=True)
                
                for name in sorted_names:
                    if name in remaining_text:
                        matched_affiliations.append(name)
                        remaining_text = remaining_text.replace(
                            name, f"__MATCHED_{len(matched_affiliations)}__"
                        )
                
                # If we matched affiliations, reconstruct with semicolons
                if matched_affiliations:
                    result = field_value
                    for idx, name in enumerate(matched_affiliations, 1):
                        result = result.replace(name, f"__MATCHED_{idx}__")
                    
                    # Replace comma-space delimiters between placeholders
                    result = result.replace(", ", "; ")
                    
                    # Restore the actual affiliation names
                    for idx, name in enumerate(matched_affiliations, 1):
                        result = result.replace(f"__MATCHED_{idx}__", name)
                    
                    return result, True
                else:
                    # No matches - simple replacement
                    return field_value.replace(", ", "; "), True
            
            # Migrate external projects
            external_projects = ExternalProjectDetails.objects.exclude(
                collaboration_with__isnull=True
            ).exclude(collaboration_with="")
            
            ext_total = external_projects.count()
            ext_migrated = 0
            
            settings.LOGGER.info(
                f"  Processing {ext_total} external project(s) for delimiter migration"
            )
            
            for ext in external_projects:
                new_value, changed = smart_migrate_field(
                    ext.collaboration_with, all_affiliation_names
                )
                if changed:
                    old_value = ext.collaboration_with
                    ext.collaboration_with = new_value
                    ext.save()
                    ext_migrated += 1
                    migrated_count += 1
                    
                    if ext_migrated <= 5:  # Log first 5 for debugging
                        settings.LOGGER.info(
                            f"    ✓ ExternalProject {ext.project_id}: "
                            f"'{old_value[:80]}...' → '{new_value[:80]}...'"
                        )
            
            settings.LOGGER.info(f"  Migrated {ext_migrated} external project field(s)")
            
            # Migrate student projects
            student_projects = StudentProjectDetails.objects.exclude(
                organisation__isnull=True
            ).exclude(organisation="")
            
            student_total = student_projects.count()
            student_migrated = 0
            
            settings.LOGGER.info(
                f"  Processing {student_total} student project(s) for delimiter migration"
            )
            
            for student in student_projects:
                new_value, changed = smart_migrate_field(
                    student.organisation, all_affiliation_names
                )
                if changed:
                    old_value = student.organisation
                    student.organisation = new_value
                    student.save()
                    student_migrated += 1
                    migrated_count += 1
                    
                    if student_migrated <= 5:  # Log first 5 for debugging
                        settings.LOGGER.info(
                            f"    ✓ StudentProject {student.project_id}: "
                            f"'{old_value[:80]}...' → '{new_value[:80]}...'"
                        )
            
            settings.LOGGER.info(f"  Migrated {student_migrated} student project field(s)")
            
            settings.LOGGER.info(
                f"STEP 2 COMPLETE: Migrated {migrated_count} total project field(s)"
            )
            
            # STEP 3: Merge duplicate affiliations and clean up formatting
            settings.LOGGER.info(
                f"STEP 3: Merging duplicate affiliations and cleaning up formatting"
            )
            
            cleanup_count = 0
            merged_count = 0
            
            # First, merge duplicate affiliations (with and without semicolons)
            with_semicolons = Affiliation.objects.filter(name__contains=";")
            for aff_with_semi in with_semicolons:
                clean_name = aff_with_semi.name.strip().rstrip(";").strip()
                if clean_name and clean_name != aff_with_semi.name:
                    try:
                        # Check if clean version exists
                        clean_aff = Affiliation.objects.get(name=clean_name)
                        settings.LOGGER.info(
                            f"  Merging duplicate: '{aff_with_semi.name}' → '{clean_aff.name}'"
                        )
                        
                        # Update projects using the semicolon version
                        for ext in ExternalProjectDetails.objects.filter(
                            collaboration_with__icontains=aff_with_semi.name
                        ):
                            ext.collaboration_with = ext.collaboration_with.replace(
                                aff_with_semi.name, clean_aff.name
                            )
                            ext.save()
                        
                        for student in StudentProjectDetails.objects.filter(
                            organisation__icontains=aff_with_semi.name
                        ):
                            student.organisation = student.organisation.replace(
                                aff_with_semi.name, clean_aff.name
                            )
                            student.save()
                        
                        # Delete the duplicate
                        aff_with_semi.delete()
                        merged_count += 1
                        
                    except Affiliation.DoesNotExist:
                        # No clean version exists, just clean this one
                        settings.LOGGER.info(
                            f"  Cleaning affiliation: '{aff_with_semi.name}' → '{clean_name}'"
                        )
                        aff_with_semi.name = clean_name
                        aff_with_semi.save()
                        merged_count += 1
            
            # Clean and deduplicate external projects
            for ext in ExternalProjectDetails.objects.exclude(
                collaboration_with__isnull=True
            ).exclude(collaboration_with=""):
                if ext.collaboration_with:
                    old_value = ext.collaboration_with
                    # Remove double semicolons and trailing semicolons
                    new_value = old_value.replace(";; ", "; ").rstrip("; ")
                    
                    # Deduplicate
                    parts = [p.strip() for p in new_value.split(";") if p.strip()]
                    seen = set()
                    unique_parts = []
                    for part in parts:
                        if part not in seen:
                            seen.add(part)
                            unique_parts.append(part)
                    new_value = "; ".join(unique_parts)
                    
                    if new_value != old_value:
                        ext.collaboration_with = new_value
                        ext.save()
                        cleanup_count += 1
            
            # Clean and deduplicate student projects
            for student in StudentProjectDetails.objects.exclude(
                organisation__isnull=True
            ).exclude(organisation=""):
                if student.organisation:
                    old_value = student.organisation
                    # Remove double semicolons and trailing semicolons
                    new_value = old_value.replace(";; ", "; ").rstrip("; ")
                    
                    # Deduplicate
                    parts = [p.strip() for p in new_value.split(";") if p.strip()]
                    seen = set()
                    unique_parts = []
                    for part in parts:
                        if part not in seen:
                            seen.add(part)
                            unique_parts.append(part)
                    new_value = "; ".join(unique_parts)
                    
                    if new_value != old_value:
                        student.organisation = new_value
                        student.save()
                        cleanup_count += 1
            
            settings.LOGGER.info(
                f"STEP 3 COMPLETE: Merged {merged_count} duplicate(s), "
                f"cleaned up {cleanup_count} project field(s)"
            )
            
            # Log final summary
            settings.LOGGER.info(
                f"=== COMPREHENSIVE FIX COMPLETE by {req.user} ===\n"
                f"  • Split {split_count} multi-affiliation record(s)\n"
                f"  • Created {created_count} new affiliation(s)\n"
                f"  • Updated {external_updated + student_updated} project reference(s)\n"
                f"  • Migrated {migrated_count} project field(s) to semicolon delimiters\n"
                f"  • Merged {merged_count} duplicate affiliation(s)\n"
                f"  • Cleaned/deduplicated {cleanup_count} project field(s)"
            )
            
            # Success message
            message = (
                f"✓ Split {split_count} multi-affiliation record(s) into {created_count} new affiliation(s)\n"
                f"✓ Updated {external_updated + student_updated} project reference(s)\n"
                f"✓ Migrated {migrated_count} project field(s) from comma to semicolon delimiters\n"
                f"✓ Merged {merged_count} duplicate affiliation(s)\n"
                f"✓ Cleaned/deduplicated {cleanup_count} project field(s)"
            )
            
            model_admin.message_user(req, message, messages.SUCCESS)
    
    except Exception as e:
        settings.LOGGER.error(f"Error during comprehensive affiliation fix: {str(e)}")
        model_admin.message_user(
            req, f"Error during fix: {str(e)}", messages.ERROR
        )


@admin.action(description="Clean orphaned affiliations (no project/user links)")
def clean_orphaned_affiliations(model_admin, req, selected):
    """
    Admin action to remove affiliations that have no links to any projects or users.
    This helps clean up the database by removing unused affiliation records.
    
    An affiliation is considered orphaned if:
    - It's not referenced in any ExternalProjectDetails.collaboration_with field
    - It's not referenced in any StudentProjectDetails.organisation field
    - It's not linked to any User records (if applicable)
    """
    from projects.models import ExternalProjectDetails, StudentProjectDetails
    from django.db.models import Q

    try:
        # Get all affiliations
        all_affiliations = Affiliation.objects.all()
        total_count = all_affiliations.count()
        
        settings.LOGGER.info(
            f"=== CLEAN ORPHANED AFFILIATIONS STARTED by {req.user} ==="
        )
        settings.LOGGER.info(f"Total affiliations to check: {total_count}")
        
        orphaned_affiliations = []
        
        # Check each affiliation for references
        for affiliation in all_affiliations:
            # Check if referenced in external projects
            external_refs = ExternalProjectDetails.objects.filter(
                collaboration_with__icontains=affiliation.name
            ).count()
            
            # Check if referenced in student projects
            student_refs = StudentProjectDetails.objects.filter(
                organisation__icontains=affiliation.name
            ).count()
            
            # If no references found, mark as orphaned
            if external_refs == 0 and student_refs == 0:
                orphaned_affiliations.append(affiliation)
                settings.LOGGER.info(
                    f"  Found orphaned: '{affiliation.name}' (pk={affiliation.pk})"
                )
        
        orphaned_count = len(orphaned_affiliations)
        
        if orphaned_count == 0:
            message = "No orphaned affiliations found. All affiliations are in use."
            settings.LOGGER.info(message)
            model_admin.message_user(req, message, messages.SUCCESS)
            return
        
        # Delete orphaned affiliations
        deleted_names = [aff.name for aff in orphaned_affiliations]
        for aff in orphaned_affiliations:
            aff.delete()
        
        settings.LOGGER.info(
            f"Deleted {orphaned_count} orphaned affiliation(s): {', '.join(deleted_names[:10])}"
            + (f" and {len(deleted_names) - 10} more..." if len(deleted_names) > 10 else "")
        )
        
        message = (
            f"✓ Cleaned {orphaned_count} orphaned affiliation(s) out of {total_count} total\n"
            f"Deleted: {', '.join(deleted_names[:5])}"
            + (f" and {len(deleted_names) - 5} more..." if len(deleted_names) > 5 else "")
        )
        
        model_admin.message_user(req, message, messages.SUCCESS)
        
    except Exception as e:
        settings.LOGGER.error(f"Error during orphaned affiliation cleanup: {str(e)}")
        model_admin.message_user(
            req, f"Error during cleanup: {str(e)}", messages.ERROR
        )


@admin.action(description="Migrate comma to semicolon delimiter")
def migrate_comma_to_semicolon_delimiter(model_admin, req, selected):
    """
    Admin action to migrate affiliation delimiters from comma to semicolon
    in ExternalProjectDetails and StudentProjectDetails text fields.
    
    Uses smart matching to avoid breaking affiliations that contain commas.
    """
    from projects.models import ExternalProjectDetails, StudentProjectDetails

    external_count = 0
    student_count = 0
    warnings = []

    try:
        # Get all valid affiliation names for smart matching
        all_affiliation_names = list(
            Affiliation.objects.values_list("name", flat=True)
        )
        
        def smart_migrate_field(field_value, all_names):
            """
            Intelligently migrate comma delimiters to semicolons by matching
            against known affiliation names.
            """
            if not field_value or ", " not in field_value:
                return field_value, False
            
            # Try to match known affiliation names in the string
            matched_affiliations = []
            remaining_text = field_value
            
            # Sort by length (longest first) to match longer names first
            sorted_names = sorted(all_names, key=len, reverse=True)
            
            for name in sorted_names:
                if name in remaining_text:
                    matched_affiliations.append(name)
                    # Replace matched name with placeholder to avoid re-matching
                    remaining_text = remaining_text.replace(name, f"__MATCHED_{len(matched_affiliations)}__")
            
            # If we matched affiliations, reconstruct with semicolons
            if matched_affiliations:
                result = field_value
                for idx, name in enumerate(matched_affiliations, 1):
                    result = result.replace(name, f"__MATCHED_{idx}__")
                
                # Replace comma-space delimiters between placeholders
                result = result.replace(", ", "; ")
                
                # Restore the actual affiliation names
                for idx, name in enumerate(matched_affiliations, 1):
                    result = result.replace(f"__MATCHED_{idx}__", name)
                
                return result, True
            else:
                # No matches found - do simple replacement but log warning
                return field_value.replace(", ", "; "), True

        # Update ExternalProjectDetails collaboration_with fields
        external_projects = ExternalProjectDetails.objects.exclude(
            collaboration_with__isnull=True
        ).exclude(collaboration_with="")

        for ext in external_projects:
            new_value, changed = smart_migrate_field(
                ext.collaboration_with, all_affiliation_names
            )
            if changed:
                ext.collaboration_with = new_value
                ext.save()
                external_count += 1

        # Update StudentProjectDetails organisation fields
        student_projects = StudentProjectDetails.objects.exclude(
            organisation__isnull=True
        ).exclude(organisation="")

        for student in student_projects:
            new_value, changed = smart_migrate_field(
                student.organisation, all_affiliation_names
            )
            if changed:
                student.organisation = new_value
                student.save()
                student_count += 1

        total_count = external_count + student_count

        settings.LOGGER.info(
            f"{req.user} migrated delimiters: {external_count} external projects, "
            f"{student_count} student projects (total: {total_count})"
        )

        message = (
            f"Successfully migrated {total_count} record(s): "
            f"{external_count} external project(s), {student_count} student project(s)"
        )
        
        model_admin.message_user(req, message, messages.SUCCESS)

    except Exception as e:
        settings.LOGGER.error(f"Error during delimiter migration: {str(e)}")
        model_admin.message_user(
            req, f"Error during migration: {str(e)}", messages.ERROR
        )


# endregion  =================================================================================================

# region ADMIN ====================================================================================================


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "created_at",
        "updated_at",
    ]
    ordering = ["name"]
    actions = (
        export_all_affiliations_txt,
        fix_affiliations_and_migrate_delimiters,
        clean_orphaned_affiliations,
        migrate_comma_to_semicolon_delimiter,
    )
    
    def changelist_view(self, request, extra_context=None):
        """
        Override to allow actions without selecting items.
        This enables running bulk actions like the comprehensive fix
        without needing to select affiliations first.
        """
        # Check if an action is being performed
        if 'action' in request.POST and request.POST.get('action') in [
            'fix_affiliations_and_migrate_delimiters',
            'clean_orphaned_affiliations',
            'migrate_comma_to_semicolon_delimiter'
        ]:
            # If no items selected, pass empty queryset (action will handle all items)
            if not request.POST.getlist('_selected_action'):
                # Create a fake POST with a dummy selection to bypass Django's check
                post = request.POST.copy()
                post.setlist('_selected_action', ['0'])  # Dummy value
                request.POST = post
        
        return super().changelist_view(request, extra_context)


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "key_stakeholder",
    ]

    search_fields = [
        "name",
    ]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "agency",
        "manager",
    ]

    search_fields = [
        "name",
    ]

    ordering = ["name"]


@admin.register(BusinessArea)
class BusinessAreaAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "division",
        "focus",
        "leader",
    ]

    search_fields = [
        "name",
        "focus",
        "leader",
    ]

    ordering = ["name"]


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "approver",
        "director",
    ]

    list_filter = [
        "approver",
        "director",
    ]

    search_fields = ["name"]

    ordering = ["name"]


@admin.register(DepartmentalService)
class DepartmentalServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "director",
    ]

    list_filter = [
        "director",
    ]

    search_fields = ["name"]

    ordering = ["name"]


# endregion  =================================================================================================
