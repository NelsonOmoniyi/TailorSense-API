"""Authenticated endpoint for personalized style recommendations."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.styles.api_views import ProjectSessionPermission

from .serializers import RecommendationRequestSerializer, RecommendationResultSerializer
from .services import get_recommendations


class RecommendationView(APIView):
    permission_classes = [ProjectSessionPermission]

    def post(self, request):
        serializer = RecommendationRequestSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        results, missing_measurements, excluded_styles = get_recommendations(
            profile=values['measurement_profile_id'],
            fabric=values['fabric_id'],
            category=values['category'],
            occasion=values.get('occasion'),
            limit=values['limit'],
        )
        serialized_results = RecommendationResultSerializer(
            results,
            many=True,
            context={'request': request},
        ).data
        excluded_for_measurements = [
            {
                'style_id': item['style'].pk,
                'name': item['style'].name,
                'measurement_check': item['measurement_check'],
                'missing_measurements': item['missing_measurements'],
            }
            for item in excluded_styles
        ]
        return Response({
            'category': values['category'].slug,
            'results': serialized_results,
            'missing_measurements': missing_measurements,
            'excluded_for_measurements': excluded_for_measurements,
            'count': len(serialized_results),
        }, status=status.HTTP_200_OK)
