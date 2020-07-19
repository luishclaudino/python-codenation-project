from django.utils import timezone
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.core.validators import URLValidator
from django.db.utils import IntegrityError, DataError
from django.contrib.auth.hashers import check_password

from api.models import User, Group, Event
from api.serializers import UserModelSerializer, GroupModelSerializer, EventModelSerializer

@api_view(['POST'])
def signup_user(request):
    """
    Função utilizada para realizar o cadastro dos usuários

    Parameters:
    request (HttpRequest): Post Request contendo email e password do usuário

    Returns:
    HttpResponse

   """
    email = request.data['email']
    password = request.data['password']
    if User.objects.filter(email=email):
        return Response({'status': f'User already exists.'}, status=status.HTTP_403_FORBIDDEN)
    user = User.objects.create_user(email,password)

    return Response({'status': f'User {user.email} created.'}, status=status.HTTP_201_CREATED)

class CustomAuthToken(ObtainAuthToken):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    def post(self, request, *args, **kwargs):
        """
        Função utilizada para realizar o login do usuário

        Parameters:
        request (HttpRequest): Post Request contendo email e password do usuário

        Returns:
        HttpResponse: Retorna o token de autenticação como dado da resposta.

        """
        email = request.data['email']
        password = request.data['password']
        try:
            user = self.queryset.get(email=email)
            if not check_password(password, user.password):
                raise DataError("Senha errada.")
        except:
            return Response(data={
                'error': 'Wrong email or password.'
            }, status=status.HTTP_403_FORBIDDEN)
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': f'{token}'}, status=status.HTTP_202_ACCEPTED)

# Create your views here.

class GroupApiViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Group.objects.all()
    serializer_class = GroupModelSerializer

    def list(self, request):
        """
        Função utilizada para listar todos os grupos

        Parameters:
        request (HttpRequest): GET Request

        Returns:
        HttpResponse[]: Retorna uma lista com todos os grupos.

        """
        response = [GroupModelSerializer(group).data for group in self.queryset]
        return Response(data=response, status=status.HTTP_200_OK)

    def create(self, request):
        """
        Função que cria um novo grupo

        Parameters:
        request (HttpRequest): : POST Request contendo o nome do grupo

        Returns:
        HttpResponse: Retorna o nome e id do grupo criado na resposta.

        """
        group_name = request.data['name']
        try:
            group = Group(name=group_name)
        except IntegrityError:
            return Response({'error': 'Group name alredy exists.'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        group.save()
        response = GroupModelSerializer(group)
        return Response(data=response.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_group_events(request, group_id):
    """
    Função utilizada para listar todos os eventos de um grupo específico.

    Parameters:
    request (HttpRequest): GET Request que pode conter parâmetros para filtrar por
    level, origin e title ou ordenar por frequency ou level.
    group_id (int): ID do grupo

    Returns:
    HttpResponse[]: Retorna uma lista de eventos filtrado e/ou ordenados.

    """
    events = Event.objects.all().filter(group_id=group_id)

    if request.GET.getlist('level'):
        level = request.GET.getlist('level')[0]
        events = events.filter(level=level)

    elif request.GET.getlist('origin'):
        origin = request.GET.getlist('origin')[0]
        events = events.filter(origin=origin)

    elif request.GET.getlist('title'):
        title = request.GET.getlist('title')[0]
        events = events.filter(title__contains=title)
    # Caso não haja uma busca, apenas arquivos não arquivados são mostrados.
    else:
        events = events.filter(shelved=False)

    if request.GET.getlist('order-by'):
        ordination = request.GET.getlist('order-by')[0]
        if ordination == 'frequency':
            events = events.order_by(ordination).reverse()
        elif ordination == 'level':
            events = events.order_by(ordination)
        response = [EventModelSerializer(event).data for event in events]
        return Response(data=response, status=status.HTTP_200_OK)
    
    response = [EventModelSerializer(event).data for event in events.order_by('date').reverse()]
    return Response(data=response, status=status.HTTP_200_OK)


class EventApiViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Event.objects.all()
    serializer_class = EventModelSerializer

    def create(self, request):
        """
        Função utilizada para criar um evento

        Parameters:
        request (HttpRequest): POST Request contendo os seguintes dados do evento:
        level, title, details, origin, date, user_id e group_id

        Returns:
        HttpResponse: Retorna uma mensagem de erro ou os dados do evento criado.

        """
        events = Event.objects.all().filter(
            level=request.data['level'],
            title=request.data['title'],
            origin=request.data['origin'],
            group_id = Group.objects.get(id=request.data['group_id']),
        )
        if events:
            event = events[0]
            event.frequency += 1
            event.date=timezone.now()
            event.user_id = User.objects.get(id=request.data['user_id'])
            response_status = status.HTTP_202_ACCEPTED
            event.save()
        else:
            validate = URLValidator()
            origin = request.data['origin']
            try:
                if '://' not in origin:
                    # Validate as if it were http://
                    validate('http://' + origin)
                else:
                    validate(origin)
                event = Event.objects.create(
                    level = request.data['level'],
                    title = request.data['title'],
                    details = request.data['details'],
                    origin = origin,
                    date=timezone.now(),
                    user_id = User.objects.get(id=request.data['user_id']),
                    group_id = Group.objects.get(id=request.data['group_id'])
                )
            except:
                return Response({'error': 'Invalid request data.'}, status=status.HTTP_400_BAD_REQUEST)
            response_status = status.HTTP_201_CREATED
        response = EventModelSerializer(event)
        return Response(data=response.data, status=response_status)

    def retrieve(self, request, pk=None):
        """
        Função utilizada para buscar um evento específico pelo id.

        Parameters:
        request (HttpRequest): GET Request
        pk (int): ID do evento

        Returns:
        HttpResponse: Retorna os dados do evento e o token do usuário que o criou.

        """
        event = self.queryset.get(id=pk)
        response = dict(EventModelSerializer(event).data)
        response['user_token'] = str(Token.objects.get(user=event.user_id))
        return Response(data=response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_events(request):
    """
    Função utilizada para deletar eventos

    Parameters:
    request (HttpRequest): POST Request contendo uma lista de id de eventos.

    Returns:
    HttpResponse: Retorna uma mensagem de erro ou sucesso.

    """
    try:
        events_to_delete =[Event.objects.get(id=event) for event in request.data['events']]
    except:
        return Response({'error': f'Event given does not exists.'}, status=status.HTTP_404_NOT_FOUND)
    for event in events_to_delete:
        event.delete()

    return Response({'status': f'Events deleted.'}, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def shelve_events(request) -> Response:
    """
    Função utilizada para arquivar eventos

    Parameters:
    request (HttpRequest): POST Request contendo uma lista de id de eventos.

    Returns:
    HttpResponse: Retorna uma mensagem de erro ou sucesso.

    """
    try:
        events_to_shelve =[Event.objects.get(id=event) for event in request.data['events']]
    except:
        return Response({'error': f'Event given does not exists.'}, status=status.HTTP_404_NOT_FOUND)
    for event in events_to_shelve:
        event.shelved = True
        event.save()

    return Response({'status': f'Events shelved.'}, status=status.HTTP_201_CREATED)