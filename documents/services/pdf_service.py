"""
PDF service - Document PDF generation using Prince XML
"""
import subprocess
import tempfile
import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError


class PDFService:
    """PDF generation service using Prince XML"""

    @staticmethod
    def generate_document_pdf(document, template_name='project_document.html'):
        """
        Generate PDF for project document
        
        Args:
            document: ProjectDocument instance
            template_name: HTML template to use
            
        Returns:
            ContentFile: Generated PDF file
            
        Raises:
            ValidationError: If PDF generation fails
        """
        settings.LOGGER.info(f"Generating PDF for document {document}")
        
        try:
            # Build context
            context = PDFService._build_document_context(document)
            
            # Render HTML
            html_content = render_to_string(
                f'templates/{template_name}',
                context
            )
            
            # Generate PDF using Prince
            pdf_content = PDFService._html_to_pdf(html_content)
            
            # Create ContentFile
            filename = f'{document.kind}_{document.pk}.pdf'
            return ContentFile(pdf_content, name=filename)
            
        except Exception as e:
            settings.LOGGER.error(f"PDF generation failed for document {document}: {e}")
            raise ValidationError(f"Failed to generate PDF: {e}")

    @staticmethod
    def generate_annual_report_pdf(report, template_name='annual_report.html'):
        """
        Generate PDF for annual report
        
        Args:
            report: AnnualReport instance
            template_name: HTML template to use
            
        Returns:
            ContentFile: Generated PDF file
            
        Raises:
            ValidationError: If PDF generation fails
        """
        settings.LOGGER.info(f"Generating PDF for annual report {report}")
        
        try:
            # Build context
            context = PDFService._build_annual_report_context(report)
            
            # Render HTML
            html_content = render_to_string(
                f'templates/{template_name}',
                context
            )
            
            # Generate PDF using Prince
            pdf_content = PDFService._html_to_pdf(html_content)
            
            # Create ContentFile
            filename = f'annual_report_{report.year}.pdf'
            return ContentFile(pdf_content, name=filename)
            
        except Exception as e:
            settings.LOGGER.error(f"PDF generation failed for report {report}: {e}")
            raise ValidationError(f"Failed to generate PDF: {e}")

    @staticmethod
    def _html_to_pdf(html_content):
        """
        Convert HTML to PDF using Prince XML
        
        Args:
            html_content: HTML string
            
        Returns:
            bytes: PDF content
            
        Raises:
            ValidationError: If conversion fails
        """
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.html',
                delete=False,
                encoding='utf-8'
            ) as html_file:
                html_file.write(html_content)
                html_path = html_file.name
            
            with tempfile.NamedTemporaryFile(
                mode='wb',
                suffix='.pdf',
                delete=False
            ) as pdf_file:
                pdf_path = pdf_file.name
            
            try:
                # Run Prince XML
                prince_cmd = [
                    'prince',
                    html_path,
                    '-o',
                    pdf_path,
                    '--javascript',
                ]
                
                result = subprocess.run(
                    prince_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    raise ValidationError(f"Prince XML failed: {result.stderr}")
                
                # Read PDF content
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                
                return pdf_content
                
            finally:
                # Clean up temporary files
                if os.path.exists(html_path):
                    os.unlink(html_path)
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
                    
        except subprocess.TimeoutExpired:
            raise ValidationError("PDF generation timed out")
        except Exception as e:
            raise ValidationError(f"PDF generation error: {e}")

    @staticmethod
    def _build_document_context(document):
        """
        Build template context for project document
        
        Args:
            document: ProjectDocument instance
            
        Returns:
            dict: Template context
        """
        context = {
            'document': document,
            'project': document.project,
            'business_area': document.project.business_area,
        }
        
        # Add document-specific details
        if document.kind == 'concept':
            if hasattr(document, 'concept_plan_details'):
                context['details'] = document.concept_plan_details.first()
        elif document.kind == 'projectplan':
            if hasattr(document, 'project_plan_details'):
                details = document.project_plan_details.first()
                context['details'] = details
                if details:
                    context['endorsements'] = details.endorsements.all()
        elif document.kind == 'progressreport':
            if hasattr(document, 'progress_report_details'):
                context['details'] = document.progress_report_details.first()
        elif document.kind == 'studentreport':
            if hasattr(document, 'student_report_details'):
                context['details'] = document.student_report_details.first()
        elif document.kind == 'projectclosure':
            if hasattr(document, 'project_closure_details'):
                context['details'] = document.project_closure_details.first()
        
        return context

    @staticmethod
    def _build_annual_report_context(report):
        """
        Build template context for annual report
        
        Args:
            report: AnnualReport instance
            
        Returns:
            dict: Template context
        """
        from ..models import ProjectDocument
        
        # Get all approved documents for the report year
        progress_reports = ProjectDocument.objects.filter(
            kind='progressreport',
            status=ProjectDocument.StatusChoices.APPROVED,
            project__year=report.year,
        ).select_related(
            'project',
            'project__business_area',
        ).prefetch_related(
            'progress_report_details',
        )
        
        student_reports = ProjectDocument.objects.filter(
            kind='studentreport',
            status=ProjectDocument.StatusChoices.APPROVED,
            project__year=report.year,
        ).select_related(
            'project',
            'project__business_area',
        ).prefetch_related(
            'student_report_details',
        )
        
        context = {
            'report': report,
            'progress_reports': progress_reports,
            'student_reports': student_reports,
        }
        
        return context

    @staticmethod
    def cancel_pdf_generation(document):
        """
        Cancel ongoing PDF generation
        
        Args:
            document: ProjectDocument or AnnualReport instance
        """
        settings.LOGGER.info(f"Cancelling PDF generation for {document}")
        
        document.pdf_generation_in_progress = False
        document.save()

    @staticmethod
    def mark_pdf_generation_started(document):
        """
        Mark PDF generation as started
        
        Args:
            document: ProjectDocument or AnnualReport instance
        """
        document.pdf_generation_in_progress = True
        document.save()

    @staticmethod
    def mark_pdf_generation_complete(document):
        """
        Mark PDF generation as complete
        
        Args:
            document: ProjectDocument or AnnualReport instance
        """
        document.pdf_generation_in_progress = False
        document.save()
