"""Serializers for user account API requests."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import serializers

from .models import UserProfile


User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
	fullname = serializers.CharField(max_length=150)
	email = serializers.EmailField()
	phone = serializers.RegexField(r'^\d{1,11}$', max_length=11)
	password = serializers.CharField(write_only=True, trim_whitespace=False)
	repeat_password = serializers.CharField(write_only=True, trim_whitespace=False)

	def validate_email(self, email):
		if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
			raise serializers.ValidationError('An account with this email already exists.')
		return email.lower()

	def validate(self, attrs):
		if attrs['password'] != attrs['repeat_password']:
			raise serializers.ValidationError({'repeat_password': 'Passwords do not match.'})

		candidate = User(username=attrs['email'], email=attrs['email'], first_name=attrs['fullname'])
		try:
			validate_password(attrs['password'], user=candidate)
		except ValidationError as error:
			raise serializers.ValidationError({'password': error.messages}) from error
		return attrs

	def create(self, validated_data):
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
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True, trim_whitespace=False)