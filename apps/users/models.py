from django.db import models

from django.conf import settings


# Stores user information that does not belong in Django's built-in User table.
# Keeping profile data separate lets authentication remain standard while
# TailorSense can later add measurements and style preferences.
class UserProfile(models.Model):
	# One profile belongs to exactly one user. Deleting the user also deletes the
	# profile, preventing abandoned profile records in the database.
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	# Phone numbers are text because they can contain country codes, spaces,
	# punctuation, or leading zeroes that numeric fields would discard.
	phone = models.CharField(max_length=20, blank=True)

	def __str__(self):
		# Use a readable identifier in Django Admin and debugging output.
		return self.user.email or self.user.username