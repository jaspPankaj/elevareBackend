from django.db import models
from django.contrib.auth.models import User

class CareerPrediction(models.Model):
    user_input = models.JSONField()  # Store submitted inputs
    prediction = models.JSONField()  # Store career paths with roadmap
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="career_predictions")

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
    
class CareerSuggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="career_suggestions")
    career = models.CharField(max_length=255)
    suggestion = models.JSONField()   # Store parsed JSON from OpenAI
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.career} suggestion for {self.user.username}"
