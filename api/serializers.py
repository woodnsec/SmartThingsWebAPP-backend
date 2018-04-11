from rest_framework import serializers
from api.models import *

class PingSerializer(serializers.Serializer):
    pingData = ChallengeSerializer()

class ChallengeSerializer(serializers.Serializer):
    challenge = serializer.CharField(max_length=1000, allow_blank=False)
