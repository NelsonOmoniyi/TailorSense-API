"""User-owned profile data kept separate from Django's built-in User model.

The phone number and biography are tailoring-specific, so they live here rather
than on ``auth.User``. Access the row through ``user.profile``; it is a
OneToOneField with ``related_name='profile'``.
"""

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
	"""Extra per-user fields: contact phone and a short style biography.

	The registration flow creates this row for every new account, so code that
	renders a user's phone or bio should read it from ``user.profile``.
	"""

	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='profile',
	)
	phone = models.CharField(max_length=11)
	# Biography shown on the profile page; optional, so an empty string is the default.
	bio = models.TextField(blank=True, default='')

	def __str__(self):
		return self.user.email or self.user.get_username()