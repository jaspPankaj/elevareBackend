from rest_framework import serializers
from .models import CareerPrediction,CareerSuggestion
from django.contrib.auth import get_user_model
User = get_user_model()

class CareerInputSerializer(serializers.Serializer):
    ug_course = serializers.CharField()
    ug_specialization = serializers.CharField(allow_blank=True, required=False)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    interests = serializers.ListField(child=serializers.CharField(), required=False)
    ug_cgpa = serializers.FloatField(required=False)
    certifications = serializers.ListField(child=serializers.CharField(), required=False)
    experience_years = serializers.IntegerField(required=False)
    # add any other fields you want

class CareerPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerPrediction
        fields = "__all__"

from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    name = serializers.CharField(write_only=True)  # map to first_name

    class Meta:
        model = User
        fields = ["name", "username", "email", "password", "password2"]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        email = data.get('email')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username already exists"})

        if password != password2:
            raise serializers.ValidationError({"password": "Passwords must match"})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email already attached to another account."})

        return data

    def create(self, validated_data):
        validated_data.pop('password2', None)
        name = validated_data.pop("name")

        user = User.objects.create_user(
            first_name=name,  
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        return user
    
class CareerSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerSuggestion
        fields = ["id", "career", "suggestion", "created_at"]
