"""
Staff profile views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.exceptions import NotFound
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from common.utils import paginate_queryset
from users.models import PublicStaffProfile
from projects.models import ProjectMember
from users.services import ProfileService, ExportService
from users.serializers import (
    StaffProfileSerializer,
    TinyStaffProfileSerializer,
    StaffProfileCreationSerializer,
    StaffProfileEmailListSerializer,
)
from projects.serializers import ProjectDataTableSerializer



class StaffProfiles(APIView):
    """List and create staff profiles"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        """List staff profiles with pagination"""
        search = request.query_params.get('search')
        filters = {
            'is_active': request.query_params.get('is_active'),
            'public': request.query_params.get('public'),
            'business_area': request.query_params.get('business_area'),
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        
        profiles = ProfileService.list_staff_profiles(filters=filters, search=search)
        paginated = paginate_queryset(profiles, request)
        
        serializer = TinyStaffProfileSerializer(paginated['items'], many=True)
        return Response({
            'profiles': serializer.data,
            'total_results': paginated['total_results'],
            'total_pages': paginated['total_pages'],
        })

    def post(self, request):
        """Create staff profile"""
        serializer = StaffProfileCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        profile = ProfileService.create_staff_profile(
            request.user.id,
            serializer.validated_data
        )
        result = StaffProfileSerializer(profile)
        return Response(result.data, status=HTTP_201_CREATED)


class StaffProfileDetail(APIView):
    """Get, update, and delete staff profile"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        """Get staff profile detail"""
        profile = ProfileService.get_staff_profile(pk)
        serializer = StaffProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update staff profile"""
        serializer = StaffProfileSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        profile = ProfileService.update_staff_profile(pk, serializer.validated_data)
        result = StaffProfileSerializer(profile)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete staff profile"""
        ProfileService.delete_staff_profile(pk)
        return Response(status=HTTP_204_NO_CONTENT)


class MyStaffProfile(APIView):
    """Get current user's staff profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ProfileService.get_staff_profile_by_user(request.user.id)
        if profile:
            serializer = StaffProfileSerializer(profile)
            return Response(serializer.data)
        return Response({"error": "No staff profile found"}, status=404)


class TogglePublicVisibility(APIView):
    """Toggle staff profile public visibility"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = ProfileService.toggle_visibility(pk)
        serializer = StaffProfileSerializer(profile)
        return Response(serializer.data, status=HTTP_200_OK)


class ActiveStaffProfileEmails(APIView):
    """Get active staff profile emails"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profiles = ProfileService.get_active_staff_emails()
        serializer = StaffProfileEmailListSerializer(
            [p.user for p in profiles],
            many=True
        )
        return Response(serializer.data)


class CheckStaffProfileAndReturnDataAndActiveState(APIView):
    """Check if staff profile exists and return data"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "User ID required"}, status=400)
        
        result = ProfileService.check_staff_profile_exists(user_id)
        if result['exists']:
            serializer = StaffProfileSerializer(result['profile'])
            return Response({
                'exists': True,
                'is_active': result['is_active'],
                'profile': serializer.data,
            })
        return Response({
            'exists': False,
            'is_active': False,
            'profile': None,
        })


class DownloadBCSStaffCSV(APIView):
    """Download staff profiles as CSV"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return ExportService.generate_staff_csv()


class StaffProfileProjects(APIView):
    """Get staff profile projects"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        """Get all projects for a staff profile, excluding hidden ones"""
        try:
            users_memberships = (
                ProjectMember.objects.filter(user=pk)
                .exclude(project__hidden_from_staff_profiles__contains=[pk])
                .select_related(
                    "project",
                    "project__business_area",
                    "project__image",
                    "user",
                )
            )
        except ProjectMember.DoesNotExist:
            raise NotFound

        if len(users_memberships) > 0:
            user_obj = users_memberships[0].user
            settings.LOGGER.info(
                msg=f"{request.user} is viewing {user_obj} and their projects"
            )
        else:
            settings.LOGGER.info(
                msg=f"{request.user} is viewing user with pk {pk} and their projects (none)"
            )

        projects_with_roles = [
            (membership.project, membership.role) for membership in users_memberships
        ]

        serialized_projects = ProjectDataTableSerializer(
            [proj for proj, _ in projects_with_roles],
            many=True,
            context={"request": request},
        )

        return Response(serialized_projects.data, status=HTTP_200_OK)


class PublicEmailStaffMember(APIView):
    """Send public email to staff member"""
    permission_classes = [AllowAny]

    def post(self, request, pk):
        """Send email to staff member from public"""
        settings.LOGGER.info(
            msg=f"(PUBLIC) {request.user} is attempting to use '{request.data.get('senderEmail')}' to send an email to a staff member"
        )

        try:
            staff_profile = PublicStaffProfile.objects.get(user__pk=pk)
            recipient_name = f"{staff_profile.user.display_first_name} {staff_profile.user.display_last_name}"
            
            # Use public email if available, otherwise use IT asset email
            recipient_email = (
                staff_profile.public_email
                if staff_profile.public_email_on and staff_profile.public_email not in [None, ""]
                else staff_profile.get_it_asset_email()
            )

            settings.LOGGER.warning(
                msg=f"(PUBLIC) {request.data.get('senderEmail')} sent a public email to {recipient_email}"
            )

            # Email details
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [recipient_email]
            template_path = "./email_templates/staff_profile_email.html"

            # Template context
            template_props = {
                "recipient_name": recipient_name,
                "staff_message": request.data.get("message"),
                "public_users_listed_email": request.data.get("senderEmail"),
            }

            # Render the email template
            template_content = render_to_string(template_path, template_props)

            if settings.ENVIRONMENT == "production":
                try:
                    send_mail(
                        "Staff Profile Message",
                        template_content,
                        from_email,
                        to_email,
                        fail_silently=False,
                        html_message=template_content,
                    )
                    return Response({"ok": "Email sent"}, status=HTTP_200_OK)
                except Exception as e:
                    settings.LOGGER.error(
                        msg=f"Email Error: {e}\n If this is a 'getaddrinfo' error, you are likely running outside of OIM's datacenters."
                    )
                    return Response({"error": str(e)}, status=400)
            else:
                # Development/staging - don't actually send
                settings.LOGGER.info(msg=f"DEV: Would send email to {recipient_email}")
                return Response({"ok": "Email would be sent (dev mode)"}, status=HTTP_200_OK)

        except PublicStaffProfile.DoesNotExist:
            return Response({"error": "Staff profile not found"}, status=404)
        except Exception as e:
            settings.LOGGER.error(msg=f"Error sending email: {e}")
            return Response({"error": str(e)}, status=400)
