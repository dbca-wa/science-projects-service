# region IMPORTS ====================================================================================================

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import (
    NotFound,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)


from .models import UserContact, BranchContact, AgencyContact, Address
from .serializers import (
    BranchContactSerializer,
    TinyBranchContactSerializer,
    UserContactSerializer,
    TinyUserContactSerializer,
    AgencyContactSerializer,
    TinyAgencyContactSerializer,
    AddressSerializer,
    TinyAddressSerializer,
)

# endregion  =================================================================================================


# region Address Views ====================================================================================================


class Addresses(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = Address.objects.all()
        ser = TinyAddressSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.error(msg=f"{req.user} is creating address")
        ser = AddressSerializer(
            data=req.data,
        )
        if ser.is_valid():
            address = ser.save()
            return Response(
                TinyAddressSerializer(address).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AddressDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = Address.objects.get(pk=pk)
        except Address.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        address = self.go(pk)
        ser = AddressSerializer(address)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        address = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is deleting address {address}")

        address.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        address = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updating address {address}")
        ser = AddressSerializer(
            address,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_address = ser.save()
            return Response(
                TinyAddressSerializer(updated_address).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion  =================================================================================================


# region Agency, Branch, User Contact Views ====================================================================================================


class AgencyContacts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = AgencyContact.objects.all()
        ser = TinyAgencyContactSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.error(msg=f"{req.user} is creating agency contact")
        ser = AgencyContactSerializer(
            data=req.data,
        )
        if ser.is_valid():
            Agency_contact = ser.save()
            return Response(
                TinyAgencyContactSerializer(Agency_contact).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class AgencyContactDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = AgencyContact.objects.get(pk=pk)
        except AgencyContact.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        Agency_contact = self.go(pk)
        ser = AgencyContactSerializer(Agency_contact)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        Agency_contact = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting agency contact {Agency_contact}"
        )
        Agency_contact.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        Agency_contact = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is updating agency contact {Agency_contact}"
        )
        ser = AgencyContactSerializer(
            Agency_contact,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_Agency_contact = ser.save()
            return Response(
                TinyAgencyContactSerializer(updated_Agency_contact).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class BranchContacts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = BranchContact.objects.all()
        ser = TinyBranchContactSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(msg=f"{req.user} is creating branch contact")
        ser = BranchContactSerializer(
            data=req.data,
        )
        if ser.is_valid():
            branch_contact = ser.save()
            return Response(
                TinyBranchContactSerializer(branch_contact).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class BranchContactDetail(APIView):
    permission_classes = [IsAuthenticated]

    def go(self, pk):
        try:
            obj = BranchContact.objects.get(pk=pk)
        except BranchContact.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        branch_contact = self.go(pk)
        ser = BranchContactSerializer(branch_contact)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        branch_contact = self.go(pk)
        settings.LOGGER.info(
            msg=f"{req.user} is deleting branch contact {branch_contact}"
        )
        branch_contact.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        branch_contact = self.go(pk)
        settings.LOGGER.error(
            msg=f"{req.user} is updating branch contact {branch_contact}"
        )
        ser = BranchContactSerializer(
            branch_contact,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_branch = ser.save()
            return Response(
                TinyBranchContactSerializer(updated_branch).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class UserContacts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, req):
        all = UserContact.objects.all()
        ser = TinyUserContactSerializer(
            all,
            many=True,
        )
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def post(self, req):
        settings.LOGGER.info(
            msg=f"{req.user} is creating a user contact with {req.data}"
        )
        ser = UserContactSerializer(
            data=req.data,
        )
        if ser.is_valid():
            user_contact = ser.save()
            return Response(
                TinyUserContactSerializer(user_contact).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class UserContactDetail(APIView):
    def go(self, pk):
        try:
            obj = UserContact.objects.get(pk=pk)
        except UserContact.DoesNotExist:
            raise NotFound
        return obj

    def get(self, req, pk):
        uc = self.go(pk)
        ser = UserContactSerializer(uc)
        return Response(
            ser.data,
            status=HTTP_200_OK,
        )

    def delete(self, req, pk):
        uc = self.go(pk)
        settings.LOGGER.error(msg=f"{req.user} is deleting {uc}")
        uc.delete()
        return Response(
            status=HTTP_204_NO_CONTENT,
        )

    def put(self, req, pk):
        uc = self.go(pk)
        settings.LOGGER.info(msg=f"{req.user} is updaing contact details {uc}")
        ser = UserContactSerializer(
            uc,
            data=req.data,
            partial=True,
        )
        if ser.is_valid():
            updated_uc = ser.save()
            return Response(
                TinyUserContactSerializer(updated_uc).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(msg=f"{ser.errors}")
            return Response(
                ser.errors,
                status=HTTP_400_BAD_REQUEST,
            )


# endregion  =================================================================================================
