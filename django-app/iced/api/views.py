import json
import sys

import requests
import simplekml
import xmltodict
from api.serializers import CalculationsSerializer
from base.models import Calculation, CoreSample, Sample
from django.db import connection
from django.http import HttpResponse
from django.http.response import Http404
from django.utils.http import urlencode
from rest_framework import generics, permissions
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_xml.renderers import XMLRenderer

from .queries import leafletmap_query


class CalculationsList(generics.ListAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationsSerializer


class CalculationDetail(generics.ListAPIView):
    queryset = Calculation.objects.all()
    serializer_class = CalculationsSerializer


# This function accepts 2 methods, GET and POST
# GET - Gets calculations based on Calculation Name
# POST - Runs calculation with variables sent
@permission_classes((permissions.AllowAny,))
class GetCalculationByName(APIView):
    def get_object(self, name):
        try:
            return Calculation.objects.get(name=name)
        except Calculation.DoesNotExist:
            raise Http404

    def get(self, request, name, format=None):
        calculation = self.get_object(name)
        serializer = CalculationsSerializer(calculation)
        return Response(serializer.data)


# This function accepts POST and runs the calculations - This is probably the one we will chose to remove
@permission_classes((permissions.AllowAny,))
class RunCalculationByName(APIView):
    def get_object(self, name):
        try:
            return Calculation.objects.get(name=name)
        except Calculation.DoesNotExist:
            raise Http404

    def get(self, request, name, format=None):
        calculation = self.get_object(name)
        serializer = CalculationsSerializer(calculation)
        calculationServiceEndpoint = serializer.data["calculation_service_endpoint"]

        form_fields = json.loads(request.body)

        response = requests.post(calculationServiceEndpoint, form_fields)

        xml = xmltodict.parse(response.text)

        xml_items = list(xml.items())

        return Response(xml_items)


@permission_classes((permissions.AllowAny,))
class GetLeafletMapData(APIView):
    def get_object(self, application_name):
        try:
            sql_statement = leafletmap_query(application_name)
            with connection.cursor() as c:
                c.execute(sql_statement)
                return c.fetchall()
        except Exception as e:
            print(e)
            return {}

    def get(self, request, application_name, format=None):
        payload = self.get_object(application_name)
        return Response(payload[0][0], headers={
            'Access-Control-Allow-Origin': '*'
        })


@permission_classes((permissions.AllowAny,))
class GetSampleKMLs(APIView):
    renderer_classes = (XMLRenderer,)

    def get_object(self, sample_ids):
        try:
            ids = sample_ids.split(",")
            ids = [int(id) for id in ids if id != ""]
            kml = simplekml.Kml()
            samples = Sample.objects.filter(id__in=ids)
            for sample in samples:
                kml.newpoint(name=sample.name, coords=[(sample.lon_DD, sample.lat_DD)])

            return kml
        except Exception as e:
            print(e)
            return {}

    def get(self, request, sample_ids, format=None):
        payload = self.get_object(sample_ids)
        content = payload.kml()
        response = HttpResponse(
            content, content_type="application/vnd.google-earth.kml+xml"
        )
        response["Content-Disposition"] = 'attachment; filename="samples.kml"'
        return response


@permission_classes((permissions.AllowAny,))
class GetCoresampleKMLs(APIView):
    renderer_classes = (XMLRenderer,)

    class GetSampleKMLs(APIView):
        def get_object(self, sample_ids):
            try:
                ids = sample_ids.split(",")
                ids = [int(id) for id in ids if id != ""]
                kml = simplekml.Kml()
                samples = CoreSample.objects.filter(id__in=ids)
                for sample in samples:
                    kml.newpoint(
                        name=sample.name, coords=[sample.lon_DD, sample.lat_idd]
                    )

                return kml
            except Exception as e:
                print(e)
                return {}

        def get(self, request, sample_ids, format=None):
            payload = self.get_object(sample_ids)
            content = payload.kml()
            response = HttpResponse(
                content, content_type="application/vnd.google-earth.kml+xml"
            )
            response["Content-Disposition"] = 'attachment; filename="samples.kml"'
            return response
