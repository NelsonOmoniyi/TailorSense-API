from django.conf import settings
from django.db import models


class UserProfile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='profile',
	)
	phone = models.CharField(max_length=11)
	bio = models.TextField(blank=True, default='')

	def __str__(self):
		return self.user.email or self.user.get_username()