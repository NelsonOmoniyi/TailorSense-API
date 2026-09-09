"""Serializers for user-related API representations."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


User = get_user_model()


# Defines the safe public representation returned to API clients. Passwords and
# internal Django fields are intentionally excluded from this representation.
class UserSerializer(serializers.ModelSerializer):
	# Read phone through the related profile, but never accept it through this
	# response serializer as an updateable field.
	phone = serializers.CharField(source='profile.phone', read_only=True)

	class Meta:
		# Explicit fields prevent future User model fields from being exposed by
		# accident if Django or the project adds more account data.
		model = User
		fields = ('id', 'email', 'first_name', 'phone')


# Validates the JSON required to create an account. It is a plain Serializer
# because the service creates both User and UserProfile records together.
class RegisterSerializer(serializers.Serializer):
	# full_name is mapped to Django's first_name by the service layer.
	full_name = serializers.CharField(max_length=150)
	# EmailField validates the format before data reaches the service layer.
	email = serializers.EmailField()
	# This value is stored on UserProfile rather than the auth user record.
	phone = serializers.CharField(max_length=20)
	# write_only prevents passwords from appearing in validated output or responses.
	password = serializers.CharField(write_only=True, min_length=8)
	password_confirmation = serializers.CharField(write_only=True, min_length=8)

	def validate_email(self, value):
		# Normalize email because it is also used as the Django username.
		email = value.strip().lower()
		if User.objects.filter(username=email).exists():
			raise serializers.ValidationError('An account with this email already exists.')
		return email

	def validate(self, attrs):
		# Cross-field validation is needed to compare the password pair.
		if attrs['password'] != attrs['password_confirmation']:
			raise serializers.ValidationError({'password_confirmation': 'Passwords do not match.'})
		# Reuse the password rules configured in settings.py.
		validate_password(attrs['password'])
		return attrs


class LoginSerializer(serializers.Serializer):
	email = serializers.EmailField()
	# The password is used only to authenticate and is never returned.
	password = serializers.CharField(write_only=True)