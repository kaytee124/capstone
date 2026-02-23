from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer, UserLoginSerializer, ChangePasswordSerializer
# Create your views here.

class userloginview(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def get(self, request):
        """Render login template"""
        return render(request, 'accounts/login.html')
    
    def post(self, request):
        """Handle login API request"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class userlogoutview(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    """
    Change password endpoint.
    Requires JWT token authentication - user can only change their own password.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def get(self, request):
        """Render change password template"""
        return render(request, 'accounts/change_password.html')
    
    def post(self, request):
        """Handle change password API request"""
        # request.user is automatically set from the JWT token
        # This ensures the user can only change their own password
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        
        # Update password
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
        