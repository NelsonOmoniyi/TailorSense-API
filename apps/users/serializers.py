"""Serializers for user account API requests."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import serializers

from .models import UserProfile


User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
	"""Validate and create a new account plus its required profile row.

	Accepts the browser registration form fields. ``phone`` is required and is
	written to UserProfile in ``create`` because the built-in User model has no
	phone field. Email is used as the username.
	"""

	fullname = serializers.CharField(max_length=150)
	email = serializers.EmailField()
	phone = serializers.RegexField(r'^\d{1,11}$', max_length=11)
	password = serializers.CharField(write_only=True, trim_whitespace=False)
	repeat_password = serializers.CharField(write_only=True, trim_whitespace=False)

	def validate_email(self, email):
		"""Reject an email that already belongs to an account and normalise case."""
		if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
			raise serializers.ValidationError('An account with this email already exists.')
		return email.lower()

	def validate(self, attrs):
		"""Confirm both password fields match and satisfy Django's validators."""
		if attrs['password'] != attrs['repeat_password']:
			raise serializers.ValidationError({'repeat_password': 'Passwords do not match.'})

		candidate = User(username=attrs['email'], email=attrs['email'], first_name=attrs['fullname'])
		try:
			validate_password(attrs['password'], user=candidate)
		except ValidationError as error:
			raise serializers.ValidationError({'password': error.messages}) from error
		return attrs

	def create(self, validated_data):
		"""Create the User, then attach its UserProfile holding the phone number."""
		# User is Django's built-in model and has no phone field; phone lives on UserProfile.
		user = User.objects.create_user(
			username=validated_data['email'],
			email=validated_data['email'],
			first_name=validated_data['fullname'],
			password=validated_data['password'],
		)
		UserProfile.objects.create(user=user, phone=validated_data['phone'])
		return user


class LoginSerializer(serializers.Serializer):
	"""Validate the email/password pair submitted by the sign-in form."""

	email = serializers.EmailField()
	password = serializers.CharField(write_only=True, trim_whitespace=False)