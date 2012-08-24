import requests
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, QueryDict
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

from stripeboard.board.forms import UserCreateForm
from stripeboard.board.tasks import rebuild_cache


# it's late...
def do_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Logged in.')
                return redirect('dashboard')
    messages.error(request, 'Could not log you in (check email or password).')
    return redirect('home')

def do_logout(request):
    logout(request)
    messages.success(request, 'Logged out.')
    return redirect('home')


@login_required
def dashboard(request):
    return render(request, 'board/dashboard.html', locals())

@login_required
def rebuild(request):
    profile = request.user.get_profile()
    rebuilt = profile.rebuild()
    if not rebuilt:
        messages.error(request, 'Only refreshes once an hour.')
    else:
        messages.success(request, 'Data refreshing... refresh in about a minute.')
    return redirect('dashboard')

@login_required
def json_data(request):
    profile = request.user.get_profile()
    return HttpResponse(json.dumps(profile.data), content_type='application/json')


##################
### OAUTH FLOW ###
##################

def oauth_start(request):
    qs = QueryDict('', mutable=True)
    qs.update({
        'response_type': 'code',
        'client_id': settings.STRIPE_CLIENT_ID,
        'scope': 'read_only'})
    return redirect('https://connect.stripe.com/oauth/authorize?' + qs.urlencode())

def oauth_return(request):
    '''
    An interstatial that confirms the user does have an account and is logged in.

    Redirects to the final step with code intact in the querystring.
    '''
    code = request.GET.get('code')
    if not code:
        raise Http404

    if not request.user.is_authenticated():
        # create account form
        if request.method == 'POST':
            form = UserCreateForm(request.POST)

            if form.is_valid():
                user = form.create_user()
                user.backend = 'django.contrib.auth.backends.ModelBackend' 
                login(request, user)
                # do no return, allow redirect
            else:
                return render(request, 'signup.html', locals())
        else:
            form = UserCreateForm()
            return render(request, 'signup.html', locals())

    response = redirect('retrieve_oauth')
    response['Location'] += '?code={0}'.format(code)
    return response

@login_required
def retrieve_oauth(request):
    '''
    After ensured signup, 
    '''
    code = request.GET.get('code')
    if not code:
        raise Http404

    r = requests.post(
        url='https://connect.stripe.com/oauth/token',
        headers={'Accept': 'application/json',
                 'Authorization': 'Bearer {0}'.format(settings.STRIPE_CLIENT_SECRET)},
        data={'grant_type': 'authorization_code',
              'client_id': settings.STRIPE_CLIENT_ID,
              'scope': 'read_only',
              'code': code})

    try:
        r.raise_for_status()
    except requests.HTTPError:
        return render(request, 'oauth/failed.html', locals())

    profile = request.user.get_profile()
    profile.set(r.json)
    profile.save()

    # build the cache in the background...
    profile.rebuild()
    messages.success(request, 'Data refreshing... refresh in about a minute.')

    return redirect('dashboard')
