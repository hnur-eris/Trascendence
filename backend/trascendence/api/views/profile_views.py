
import json
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, HttpResponseNotFound, JsonResponse, HttpResponse
from django.db.models import Q
from trascendence.middleware.validators import request_body, str_field
from trascendence.middleware.auth import authorize
from trascendence.api.models.tournament_models import Tournaments
from trascendence.api.models.User import UserModel
from trascendence.api.models.match_models import Matches
from trascendence.api.models.tournament_models import TournamentMatches
from django.contrib.auth.hashers import BCryptPasswordHasher
from trascendence.api.dto import user_dto, profile_dto

def get_most_played(user_id_list):
    from collections import Counter
    most_played_with = Counter(user_id_list)
    return most_played_with.most_common(2)[1][0]


@require_http_methods(['GET'])
def get_user_profile(request: HttpRequest, username: str):
    try:
        user = UserModel.objects.get(Q(username__exact=username))
        matches = Matches.objects.filter(Q(home=user) | Q(away=user))
        tournament_matches = TournamentMatches.objects.filter(Q(match__home__exact=user.id) | Q(match__away__exact=user.id))
        tournaments = Tournaments.objects.filter(tournamentplayers_tournament_id__user=user.id)
        played_users = [match.home.id for match in matches] + [match.away.id for match in matches]
        rival = None
        if len(played_users) > 0:
            rival_id = get_most_played(played_users)
            rival = UserModel.objects.get(id=rival_id)
        profile = profile_dto(user, matches, tournament_matches, tournaments, rival)
        return JsonResponse(profile, status=200)
    except Exception as e:
        return HttpResponseNotFound(json.dumps({"message":f"user '{username}' not found", "exception": str(e)}), content_type="application/json")
    
@require_http_methods(['PATCH'])
@authorize()
@request_body(
    content_type="application/json",
    fields={
        "username": str_field(required=False),
        "name": str_field(required=False),
        "surname": str_field(required=False),
        "email": str_field(required=False),
        "avatarURI": str_field(required=False),
        "playcode": str_field(required=False),
        "password": str_field(required=False)
    }
)
def update_profile(request: HttpRequest, content: dict):
    user = request.auth_info.user
    password_hasher = BCryptPasswordHasher()
    if "username" in content.keys():
        user.username = content["username"]

    if "name" in content.keys():
        user.name = content["name"]

    if "surname" in content.keys():
        user.surname = content["surname"]

    if "email" in content.keys():
        user.email = content["email"]

    if "avatarURI" in content.keys():
        user.avatarURI = content["avatarURI"]

    if "playcode" in content.keys():
        user.play_code = password_hasher.encode(content["playcode"], password_hasher.salt())
        user.has_play_code = True

    if "password" in content.keys():
        user.password = password_hasher.encode(content["password"], password_hasher.salt())

    user.save()
    return JsonResponse({"new_user": user_dto(user)})


from trascendence.core import generate_token
from datetime import timedelta
import requests
@require_http_methods(['GET'])
def send_notification(request, username):
    message = "Dummy Text"
    resource_group = "dummy"
    resource_code = "dummy"
    temp_token = generate_token({"sub": "42_rush"}, timedelta(seconds=30))
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer ${temp_token}"
    }
    url = f"http://websocket/ws/api/push/{username}"
    try:
        response = requests.post(url, headers=headers, data=json.dumps({
            "message": message,
            "resource_group": resource_group,
            "resource_code": resource_code
        }))
        return JsonResponse({"response_code": response.status_code}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)},status=200)