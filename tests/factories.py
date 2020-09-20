from factory import post_generation
from factory import PostGenerationMethodCall
from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from sampleapp.extensions import db
from sampleapp.models.accounts import User


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""

        abstract = True
        sqlalchemy_session = db.session


class UserFactory(BaseFactory):
    class Meta:
        model = User

    email = Sequence(lambda n: "user{0}@example.com".format(n))
    active = True

    # Notice: PostGenerationMethodCall is easier to use, but as pytest-factoryboy doesn't support it, so that
    #         we have to use post generation hook here
    @post_generation
    def init_password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or "example")


class AdminFactory(UserFactory):
    is_admin = True
