"""
Common test data factories using factory_boy.

Provides factories for creating test data across all backend apps.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating test users"""

    class Meta:
        model = "users.User"
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation"""
        if create:
            obj.set_password(extracted or "testpass123")
            obj.save()


class SuperuserFactory(UserFactory):
    """Factory for creating superusers"""

    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f"admin{n}")


class AffiliationFactory(DjangoModelFactory):
    """Factory for creating test affiliations"""

    class Meta:
        model = "agencies.Affiliation"
        skip_postgeneration_save = True

    name = factory.Faker("company")


class AgencyFactory(DjangoModelFactory):
    """Factory for creating test agencies"""

    class Meta:
        model = "agencies.Agency"
        skip_postgeneration_save = True

    name = factory.Faker("company")


class DivisionFactory(DjangoModelFactory):
    """Factory for creating test divisions"""

    class Meta:
        model = "agencies.Division"
        skip_postgeneration_save = True

    name = factory.Faker("catch_phrase")
    slug = factory.Faker("slug")


class BranchFactory(DjangoModelFactory):
    """Factory for creating test branches"""

    class Meta:
        model = "agencies.Branch"
        skip_postgeneration_save = True

    name = factory.Faker("bs")
    agency = factory.SubFactory(AgencyFactory)


class BusinessAreaFactory(DjangoModelFactory):
    """Factory for creating test business areas"""

    class Meta:
        model = "agencies.BusinessArea"
        skip_postgeneration_save = True

    name = factory.Faker("company")
    focus = factory.Faker("bs")
    introduction = factory.Faker("paragraph")
    agency = factory.SubFactory(AgencyFactory)
    division = factory.SubFactory(DivisionFactory)
    leader = factory.SubFactory(UserFactory)
    finance_admin = factory.SubFactory(UserFactory)
    data_custodian = factory.SubFactory(UserFactory)


class ProjectFactory(DjangoModelFactory):
    """Factory for creating test projects"""

    class Meta:
        model = "projects.Project"
        skip_postgeneration_save = True

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    year = factory.Faker("year")
    number = factory.Sequence(lambda n: n)
    status = "new"
    kind = "science"  # Set a default kind to avoid NoneType error in __str__
    business_area = factory.SubFactory(BusinessAreaFactory)

    @factory.post_generation
    def members(obj, create, extracted, **kwargs):
        """Add members after project creation"""
        if not create:
            return

        if extracted is not None:
            # If members were passed (even empty list), add them
            for user in extracted:
                is_leader = kwargs.get("leader") == user
                obj.members.create(
                    user=user,
                    is_leader=is_leader,
                    role="supervising",
                )
        else:
            # Create a default leader only if members not specified
            leader = UserFactory()
            obj.members.create(
                user=leader,
                is_leader=True,
                role="supervising",
            )


class ProjectMemberFactory(DjangoModelFactory):
    """Factory for creating test project members"""

    class Meta:
        model = "projects.ProjectMember"
        skip_postgeneration_save = True

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    is_leader = False
    role = "supervising"  # Required field with choices


class CaretakerFactory(DjangoModelFactory):
    """Factory for creating test caretaker relationships"""

    class Meta:
        model = "caretakers.Caretaker"
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    caretaker = factory.SubFactory(UserFactory)
    reason = factory.Faker("sentence")
    notes = factory.Faker("paragraph")


class AdminTaskFactory(DjangoModelFactory):
    """Factory for creating test admin tasks"""

    class Meta:
        model = "adminoptions.AdminTask"
        skip_postgeneration_save = True

    action = "setcaretaker"
    status = "pending"
    primary_user = factory.SubFactory(UserFactory)
    requester = factory.SubFactory(UserFactory)
    reason = factory.Faker("sentence")

    @factory.post_generation
    def secondary_users(obj, create, extracted, **kwargs):
        """Set secondary_users after task creation"""
        if not create:
            return

        if extracted:
            # If secondary_users were passed, use them
            obj.secondary_users = [user.pk for user in extracted]
            obj.save()
        else:
            # Create a default secondary user
            user = UserFactory()
            obj.secondary_users = [user.pk]
            obj.save()


class UserContactFactory(DjangoModelFactory):
    """Factory for creating test user contacts"""

    class Meta:
        model = "contacts.UserContact"
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    email = factory.Faker("email")
    phone = factory.Faker("phone_number")
    alt_phone = factory.Faker("phone_number")
    fax = factory.Faker("phone_number")


class AreaFactory(DjangoModelFactory):
    """Factory for creating test areas (locations)"""

    class Meta:
        model = "locations.Area"
        skip_postgeneration_save = True

    name = factory.Faker("city")
    area_type = "dbcaregion"


class ProjectDocumentFactory(DjangoModelFactory):
    """Factory for creating test project documents"""

    class Meta:
        model = "documents.ProjectDocument"
        skip_postgeneration_save = True

    project = factory.SubFactory(ProjectFactory)
    kind = "concept"
    status = "new"
    creator = factory.SubFactory(UserFactory)
    modifier = factory.SubFactory(UserFactory)
