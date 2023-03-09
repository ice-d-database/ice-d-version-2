from base.models import Calculation
from rest_framework import serializers


class CalculationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calculation
        fields = ["id", "name", "calculation_service_endpoint", "variable_json"]
