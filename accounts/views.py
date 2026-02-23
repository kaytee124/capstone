from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer, UserLoginSerializer, ChangePasswordSerializer, UserCreationSerializer, UserUpdateSerializer
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
        user.last_login = timezone.now()
        user.save()
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
    
    def put(self, request):
        """Handle change password API request"""
        # request.user is automatically set from the JWT token
        # This ensures the user can only change their own password
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


class clientregistrationview(APIView):
    serializer_class = UserCreationSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.last_login = None
        user.date_joined = timezone.now()
        user.updated_at = timezone.now()
        user.updated_by = None
        user.role = 'client'
        user.save()
        return Response({'message': 'Client created successfully'}, status=status.HTTP_201_CREATED)


class clientupdateview(APIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    def put(self, request):
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.username = serializer.validated_data['username']
        user.email = serializer.validated_data['email']
        user.first_name = serializer.validated_data['first_name']
        user.last_name = serializer.validated_data['last_name']
        user.updated_at = timezone.now()
        user.updated_by = request.user
        user.save()
        return Response({'message': 'Client updated successfully'}, status=status.HTTP_200_OK)

class clientupdateactivationview(APIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        user.is_active = serializer.validated_data['is_active']
        user.is_staff =  False
        user.is_superuser = False
        user.updated_at = timezone.now()
        user.updated_by = request.user
        user.save()
        return Response({'message': 'is_active' if user.is_active else 'is_inactive' 'Client  successfully'}, status=status.HTTP_200_OK)

class createadminview(APIView):
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = False
        user.last_login = None
        user.date_joined = timezone.now()
        user.updated_at = timezone.now()
        user.updated_by = request.user
        user.role = 'admin'
        user.save()
        return Response({'message': 'Admin created successfully'}, status=status.HTTP_201_CREATED)

class createemployeeview(APIView):
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = False
        user.role = 'employee'
        user.last_login = None
        user.date_joined = timezone.now()
        user.updated_at = timezone.now()
        user.updated_by = request.user
        user.save()
        return Response({'message': 'Employee created successfully'}, status=status.HTTP_201_CREATED)


class superadminupdateactivationview(APIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        user.is_active = serializer.validated_data['is_active']
        user.is_staff = serializer.validated_data['is_staff']
        user.is_superuser = serializer.validated_data['is_superuser']
        user.updated_at = timezone.now()
        user.updated_by = request.user
        user.save()
        return Response({'message': 'Superadmin updated successfully'}, status=status.HTTP_200_OK)