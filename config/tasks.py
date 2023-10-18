import pypandoc
from celery import shared_task


@shared_task
def generate_pdf(data, pdf_file):
    # Perform the PDF generation as before
    pypandoc.convert_text(data, "pdf", format="latex", outputfile=pdf_file)
