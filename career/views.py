import os
import json
import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from openai import OpenAI
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CareerPrediction,CareerSuggestion
from .serializers import CareerPredictionSerializer,UserSerializer


# Load OpenAI key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
client = OpenAI(api_key=OPENAI_API_KEY)


# Helper: safely extract JSON from AI output
def extract_json(text):
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r'(\{.*\})', text, re.S)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                return None
    return None


# --- Career Prediction API ---
class CareerPredictView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_data = request.data

            prompt = f"""
            The user has the following profile:
            UG Course: {user_data.get('ug_course')}
            UG Specialization: {user_data.get('ug_specialization')}
            Skills: {user_data.get('skills')}
            Interests: {user_data.get('interests')}
            UG CGPA: {user_data.get('ug_cgpa')}
            Certifications: {user_data.get('certifications')}
            Experience: {user_data.get('experience_years')} years

            Task:
            Suggest 3 suitable career paths.
            Return ONLY valid JSON in this format:
            {{
              "career_paths": [
                {{
                  "title": "string",
                  "description": "string",
                  "required_skills": ["string"],
                  "roadmap": {{
                    "short_term": ["string"],
                    "medium_term": ["string"],
                    "long_term": ["string"]
                  }}
                }}
              ]
            }}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI career counselor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            raw_content = response.choices[0].message.content.strip()

            if raw_content.startswith("```"):
                raw_content = raw_content.replace("```json", "").replace("```", "").strip()

            parsed_json = extract_json(raw_content)
            if not parsed_json:
                return Response(
                    {"error": "Failed to parse JSON from OpenAI response."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            prediction = CareerPrediction.objects.create(
                user=request.user,
                user_input=user_data,
                prediction=parsed_json
            )

            return Response({
                "id": prediction.id,
                "career_paths": parsed_json["career_paths"],
                "created_at": prediction.created_at
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Career History API ---
class CareerHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = CareerPrediction.objects.filter(user=request.user).order_by("-created_at")
        serializer = CareerPredictionSerializer(history, many=True)
        return Response(serializer.data)


# --- Google Authentication API ---
User = get_user_model()

class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("credential")
        if not token:
            return Response({"error": "No credential provided"}, status=400)

        try:
            # verify with Google
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request())
            email = idinfo["email"]
            name = idinfo.get("name", "")
            sub = idinfo["sub"]

            # create or fetch user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": name or email.split("@")[0]}
            )

            # issue JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "email": email,
                "name": name,
                "is_new_user": created
            })

        except Exception as e:
            return Response({"error": str(e)}, status=400)

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user is not None:
            # issue JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "email": user.email,
                "name" : user.first_name
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)
        
class CareerDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            career_name = request.data.get("career")
            if not career_name:
                return Response({"error": "Career field is required."}, status=status.HTTP_400_BAD_REQUEST)

            prompt = f"""
            Task:
            Provide a detailed breakdown for the career: {career_name}.

            The response must be ONLY valid JSON in this format:
            {{
              "career": "{career_name}",
              "required_skills": ["string"],
              "free_courses": [
                {{
                  "title": "string",
                  "platform": "string",
                  "url": "string"
                }}
              ],
              "roadmap": {{
                "short_term": ["string"],
                "medium_term": ["string"],
                "long_term": ["string"]
              }}
            }}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert career counselor and learning path guide."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            raw_content = response.choices[0].message.content.strip()

            if raw_content.startswith("```"):
                raw_content = raw_content.replace("```json", "").replace("```", "").strip()

            parsed_json = extract_json(raw_content)
            if not parsed_json:
                return Response(
                    {"error": "Failed to parse JSON from OpenAI response."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Save in DB
            suggestion = CareerSuggestion.objects.create(
                user=request.user,
                career=career_name,
                suggestion=parsed_json
            )

            return Response({
                "id": suggestion.id,
                "career": parsed_json["career"],
                "required_skills": parsed_json["required_skills"],
                "free_courses": parsed_json["free_courses"],
                "roadmap": parsed_json["roadmap"],
                "created_at": suggestion.created_at
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
