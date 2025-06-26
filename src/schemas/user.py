from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from src.models.user import UserRole


class UserSchema(Schema):
    """Schema for serializing and deserializing User model instances"""

    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(
        load_only=True, required=True, validate=validate.Length(min=8)
    )
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    role = fields.Str(validate=validate.OneOf([role.value for role in UserRole]))
    phone_number = fields.Str()
    license_number = fields.Str()
    is_active = fields.Bool(dump_only=True)
    last_login_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    full_name = fields.Str(dump_only=True)

    @validates("email")
    def validate_email(self, value):
        from src.models.user import User
        from src import db

        # Check if email already exists (for new users only)
        if self.context.get("is_update") is not True:
            if db.session.query(User).filter(User.email == value).first():
                raise ValidationError("Email already exists.")

    @validates("username")
    def validate_username(self, value):
        from src.models.user import User
        from src import db

        # Check if username already exists (for new users only)
        if self.context.get("is_update") is not True:
            if db.session.query(User).filter(User.username == value).first():
                raise ValidationError("Username already exists.")


class UserUpdateSchema(UserSchema):
    """Schema for updating User instances"""

    password = fields.Str(
        load_only=True, validate=validate.Length(min=8), required=False
    )
    username = fields.Str(validate=validate.Length(min=3, max=80))
    email = fields.Email()
    first_name = fields.Str()
    last_name = fields.Str()


class LoginSchema(Schema):
    """Schema for validating login credentials"""

    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class TokenSchema(Schema):
    """Schema for authentication tokens"""

    access_token = fields.Str()
    token_type = fields.Str()
    expires_in = fields.Int()
    refresh_token = fields.Str()
    user = fields.Nested(UserSchema, exclude=["password"])


class PasswordResetRequestSchema(Schema):
    """Schema for password reset requests"""

    email = fields.Email(required=True)


class PasswordResetSchema(Schema):
    """Schema for password reset"""

    token = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    confirm_password = fields.Str(required=True)

    @validates("confirm_password")
    def validate_confirm_password(self, value):
        if value != self.context.get("password"):
            raise ValidationError("Passwords do not match.")
