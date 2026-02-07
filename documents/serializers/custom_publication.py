"""
Custom publication serializers
"""

from rest_framework import serializers

from users.serializers import TinyUserSerializer

from ..models import CustomPublication


class TinyCustomPublicationSerializer(serializers.ModelSerializer):
    """Minimal custom publication serializer"""

    creator = TinyUserSerializer(read_only=True)

    class Meta:
        model = CustomPublication
        fields = [
            "id",
            "creator",
            "title",
            "year",
        ]


class CustomPublicationSerializer(serializers.ModelSerializer):
    """Standard custom publication serializer"""

    creator = TinyUserSerializer(read_only=True)

    class Meta:
        model = CustomPublication
        fields = "__all__"


class CustomPublicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating custom publications"""

    class Meta:
        model = CustomPublication
        fields = [
            "title",
            "year",
            "citation",
        ]


class CustomPublicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating custom publications"""

    class Meta:
        model = CustomPublication
        fields = [
            "title",
            "year",
            "citation",
        ]


class PublicationDocSerializer(serializers.Serializer):
    """Serializer for library publication documents"""

    DocId = serializers.CharField(allow_blank=True, required=False, default="")
    BiblioText = serializers.CharField(allow_blank=True, required=False, default="")
    staff_only = serializers.BooleanField(required=False, default=False)
    UserName = serializers.CharField(allow_blank=True, required=False, default="")
    recno = serializers.IntegerField(required=False, allow_null=True)
    content = serializers.ListField(
        child=serializers.CharField(allow_blank=True, required=False),
        required=False,
        default=list,
    )
    title = serializers.CharField(allow_blank=True, required=False, default="")
    Material = serializers.CharField(allow_blank=True, required=False, default="")
    publisher = serializers.CharField(allow_blank=True, required=False, default="")
    AuthorBiblio = serializers.CharField(allow_blank=True, required=False, default="")
    year = serializers.CharField(allow_blank=True, required=False, default="")
    documentKey = serializers.CharField(allow_blank=True, required=False, default="")
    UserId = serializers.CharField(allow_blank=True, required=False, default="")
    author = serializers.CharField(allow_blank=True, required=False, default="")
    citation = serializers.CharField(allow_blank=True, required=False, default="")
    place = serializers.CharField(allow_blank=True, required=False, default="")
    BiblioEditors = serializers.CharField(allow_blank=True, required=False, default="")
    link_address = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False, default=list
    )
    link_category = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False, default=list
    )
    link_notes = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False, default=list
    )


class LibraryPublicationResponseSerializer(serializers.Serializer):
    """Serializer for library publication API response"""

    numFound = serializers.IntegerField(required=False, default=0)
    start = serializers.IntegerField(required=False, default=0)
    numFoundExact = serializers.BooleanField(required=False, default=True)
    docs = PublicationDocSerializer(many=True, required=False, default=list)
    isError = serializers.BooleanField(required=False, default=False)
    errorMessage = serializers.CharField(required=False, default="", allow_blank=True)


class PublicationResponseSerializer(serializers.Serializer):
    """Serializer for combined publication response (library + custom)"""

    staffProfilePk = serializers.IntegerField()
    libraryData = LibraryPublicationResponseSerializer()
    customPublications = CustomPublicationSerializer(many=True)
