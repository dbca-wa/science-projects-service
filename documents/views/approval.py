"""
Document approval workflow views
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from ..serializers import ProjectDocumentSerializer
from ..services.approval_service import ApprovalService
from ..services.document_service import DocumentService


class DocApproval(APIView):
    """
    Approve document at specified stage

    Original API contract: POST with stage and documentPk in body
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Approve document at specified stage"""
        # Validate request data
        stage = request.data.get("stage")
        document_pk = request.data.get("documentPk")

        if not stage or not document_pk:
            return Response(
                {"error": "stage and documentPk are required"},
                status=HTTP_400_BAD_REQUEST,
            )

        try:
            stage = int(stage)
        except (ValueError, TypeError):
            return Response(
                {"error": "stage must be an integer"}, status=HTTP_400_BAD_REQUEST
            )

        # Get document
        document = DocumentService.get_document(document_pk)

        # Delegate to service based on stage
        if stage == 1:
            ApprovalService.approve_stage_one(document, request.user)
        elif stage == 2:
            ApprovalService.approve_stage_two(document, request.user)
        elif stage == 3:
            ApprovalService.approve_stage_three(document, request.user)
        else:
            return Response(
                {"error": f"Invalid stage: {stage}"}, status=HTTP_400_BAD_REQUEST
            )

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_202_ACCEPTED)


class DocRecall(APIView):
    """
    Recall document from approval process

    Original API contract: POST with stage and documentPk in body
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Recall document"""
        # Validate request data
        stage = request.data.get("stage")
        document_pk = request.data.get("documentPk")
        reason = request.data.get("reason", "")

        if not stage or not document_pk:
            return Response(
                {"error": "stage and documentPk are required"},
                status=HTTP_400_BAD_REQUEST,
            )

        # Get document
        document = DocumentService.get_document(document_pk)

        # Delegate to service
        ApprovalService.recall(document, request.user, reason)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_202_ACCEPTED)


class DocSendBack(APIView):
    """
    Send document back for revision

    Original API contract: POST with stage and documentPk in body
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Send document back for revision"""
        # Validate request data
        stage = request.data.get("stage")
        document_pk = request.data.get("documentPk")
        reason = request.data.get("reason", "")

        if not stage or not document_pk:
            return Response(
                {"error": "stage and documentPk are required"},
                status=HTTP_400_BAD_REQUEST,
            )

        # Get document
        document = DocumentService.get_document(document_pk)

        # Delegate to service
        ApprovalService.send_back(document, request.user, reason)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_202_ACCEPTED)


class RequestApproval(APIView):
    """Request approval for document"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Request approval for document"""
        document = DocumentService.get_document(pk)

        # Delegate to service
        ApprovalService.request_approval(document, request.user)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_200_OK)


class ApproveStageOne(APIView):
    """Approve document at stage 1 (project lead)"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Approve document at stage 1"""
        document = DocumentService.get_document(pk)

        # Delegate to service
        ApprovalService.approve_stage_one(document, request.user)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_200_OK)


class ApproveStageTwo(APIView):
    """Approve document at stage 2 (business area lead)"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Approve document at stage 2"""
        document = DocumentService.get_document(pk)

        # Delegate to service
        ApprovalService.approve_stage_two(document, request.user)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_200_OK)


class ApproveStageThree(APIView):
    """Approve document at stage 3 (directorate)"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Approve document at stage 3 (final approval)"""
        document = DocumentService.get_document(pk)

        # Delegate to service
        ApprovalService.approve_stage_three(document, request.user)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_200_OK)


class SendBack(APIView):
    """Send document back for revision"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Send document back for revision"""
        document = DocumentService.get_document(pk)
        reason = request.data.get("reason", "")

        # Delegate to service
        ApprovalService.send_back(document, request.user, reason)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_200_OK)


class RecallDocument(APIView):
    """Recall document from approval process"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Recall document"""
        document = DocumentService.get_document(pk)
        reason = request.data.get("reason", "")

        # Delegate to service
        ApprovalService.recall(document, request.user, reason)

        # Serialize and return
        serializer = ProjectDocumentSerializer(document)
        return Response(serializer.data, status=HTTP_200_OK)


class BatchApprove(APIView):
    """Batch approve multiple documents"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Batch approve documents"""
        document_ids = request.data.get("document_ids", [])
        stage = request.data.get("stage")

        if not document_ids or not stage:
            return Response(
                {"error": "document_ids and stage are required"},
                status=HTTP_400_BAD_REQUEST,
            )

        # Get documents
        documents = [DocumentService.get_document(doc_id) for doc_id in document_ids]

        # Delegate to service
        results = ApprovalService.batch_approve(
            documents=documents, approver=request.user, stage=int(stage)
        )

        return Response(results, status=HTTP_200_OK)
