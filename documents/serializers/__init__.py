"""
Documents serializers
"""
# Base serializers
from .base import (
    TinyProjectDocumentSerializer,
    TinyProjectDocumentSerializerWithUserDocsBelongTo,
    ProjectDocumentSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentUpdateSerializer,
    TinyAnnualReportSerializer,
    MiniAnnualReportSerializer,
    AnnualReportSerializer,
    AnnualReportCreateSerializer,
    AnnualReportUpdateSerializer,
)

# Concept plan serializers
from .concept_plan import (
    TinyConceptPlanSerializer,
    ConceptPlanSerializer,
    ConceptPlanCreateSerializer,
    ConceptPlanUpdateSerializer,
)

# Project plan serializers
from .project_plan import (
    TinyProjectPlanSerializer,
    ProjectPlanSerializer,
    ProjectPlanCreateSerializer,
    ProjectPlanUpdateSerializer,
    TinyEndorsementSerializer,
    MiniEndorsementSerializer,
    EndorsementSerializer,
    EndorsementCreateSerializer,
    EndorsementUpdateSerializer,
)

# Progress report serializers
from .progress_report import (
    TinyProgressReportSerializer,
    ProgressReportSerializer,
    ProgressReportCreateSerializer,
    ProgressReportUpdateSerializer,
)

# Student report serializers
from .student_report import (
    TinyStudentReportSerializer,
    StudentReportSerializer,
    StudentReportCreateSerializer,
    StudentReportUpdateSerializer,
)

# Closure serializers
from .closure import (
    TinyProjectClosureSerializer,
    ProjectClosureSerializer,
    ProjectClosureCreateSerializer,
    ProjectClosureUpdateSerializer,
)

# Custom publication serializers
from .custom_publication import (
    TinyCustomPublicationSerializer,
    CustomPublicationSerializer,
    CustomPublicationCreateSerializer,
    CustomPublicationUpdateSerializer,
    PublicationDocSerializer,
    LibraryPublicationResponseSerializer,
    PublicationResponseSerializer,
)

__all__ = [
    # Base
    'TinyProjectDocumentSerializer',
    'TinyProjectDocumentSerializerWithUserDocsBelongTo',
    'ProjectDocumentSerializer',
    'ProjectDocumentCreateSerializer',
    'ProjectDocumentUpdateSerializer',
    'TinyAnnualReportSerializer',
    'MiniAnnualReportSerializer',
    'AnnualReportSerializer',
    'AnnualReportCreateSerializer',
    'AnnualReportUpdateSerializer',
    # Concept plan
    'TinyConceptPlanSerializer',
    'ConceptPlanSerializer',
    'ConceptPlanCreateSerializer',
    'ConceptPlanUpdateSerializer',
    # Project plan
    'TinyProjectPlanSerializer',
    'ProjectPlanSerializer',
    'ProjectPlanCreateSerializer',
    'ProjectPlanUpdateSerializer',
    'TinyEndorsementSerializer',
    'MiniEndorsementSerializer',
    'EndorsementSerializer',
    'EndorsementCreateSerializer',
    'EndorsementUpdateSerializer',
    # Progress report
    'TinyProgressReportSerializer',
    'ProgressReportSerializer',
    'ProgressReportCreateSerializer',
    'ProgressReportUpdateSerializer',
    # Student report
    'TinyStudentReportSerializer',
    'StudentReportSerializer',
    'StudentReportCreateSerializer',
    'StudentReportUpdateSerializer',
    # Closure
    'TinyProjectClosureSerializer',
    'ProjectClosureSerializer',
    'ProjectClosureCreateSerializer',
    'ProjectClosureUpdateSerializer',
    # Custom publication
    'TinyCustomPublicationSerializer',
    'CustomPublicationSerializer',
    'CustomPublicationCreateSerializer',
    'CustomPublicationUpdateSerializer',
    'PublicationDocSerializer',
    'LibraryPublicationResponseSerializer',
    'PublicationResponseSerializer',
]
