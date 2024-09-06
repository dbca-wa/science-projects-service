# region IMPORTS ==============================================
import tempfile
import os
from django.contrib import admin
from django.core.exceptions import ValidationError
from .serializers import QuoteListSerializer
from .models import Quote

# endregion ==============================================


# region ADMIN ACTION ==============================================


@admin.action(description="Generate Quotes")
def generate_quotes(model_admin, req, selected):
    def clean_quotes():
        print(os.path.dirname(os.path.realpath(__file__)))
        quote_file_location = (
            os.path.dirname(os.path.realpath(__file__)) + "/unique_quotes.txt"
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

    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return
    uniques = clean_quotes()
    try:
        for obj in uniques:
            ser = QuoteListSerializer(data=obj)
            if ser.is_valid():
                ser.save()
            else:
                print(f"ERROR: {ser.errors}")
        print("SUCCESS: GENERATED")
    except Exception as e:
        print(f"ERROR: {e}")


@admin.action(description="Selected to TXT")
def export_selected_quotes_txt(model_admin, req, selected):
    # Use tempfile to create a temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", encoding="utf-8"
    ) as temp_file:
        for quote in selected:
            text = quote.text
            author = quote.author
            temp_file.write(f"{text} - {author}\n")
        temp_file_path = temp_file.name
    try:
        print(f"Exported to {temp_file_path}")
    except Exception as e:
        print(f"ERROR: {e}")


@admin.action(description="All to TXT")
def export_all_quotes_txt(model_admin, req, selected):
    if len(selected) > 1:
        print("PLEASE SELECT ONLY ONE")
        return
    # Use tempfile to create a temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", encoding="utf-8"
    ) as temp_file:
        saved_quotes = Quote.objects.all()
        for quote in saved_quotes:
            text = quote.text
            author = quote.author
            temp_file.write(f"{text} - {author}\n")
        temp_file_path = temp_file.name
    try:
        print(f"Exported to {temp_file_path}")
    except Exception as e:
        print(f"ERROR: {e}")


# endregion ==============================================

# region ADMIN ==============================================


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    actions = (
        generate_quotes,
        export_selected_quotes_txt,
        export_all_quotes_txt,
    )
    list_display = [
        "text",
        "author",
        "created_at",
        "updated_at",
    ]
    list_filter = ["author"]
    search_fields = ["text", "author"]


# endregion ==============================================
