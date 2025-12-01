import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CombinationPasswordValidator:
    """
    Validates that the password contains at least:
    - 8 characters
    - 1 uppercase letter
    - 1 lowercase letter
    - 1 digit
    """

    def validate(self, password, user=None):
        errors = []

        if len(password) < 8:
            errors.append(_("Password must be at least 8 characters long."))

        if not re.search(r"[A-Z]", password):
            errors.append(_("Password must contain at least one uppercase letter."))

        if not re.search(r"[a-z]", password):
            errors.append(_("Password must contain at least one lowercase letter."))

        if not re.search(r"\d", password):
            errors.append(_("Password must contain at least one digit."))

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must be at least 8 characters long and contain "
            "an uppercase letter, a lowercase letter, and a digit."
        )
