from celery import task

from stripeboard.board.models import Profile


@task(serializer='json')
def rebuild_caches():
    profiles = Profile.objects.exclude(access_token=None).all()

    for profile in profiles:
        profile.rebuild()


@task(serializer='json')
def rebuild_cache(user_id):
    profile = Profile.objects.get(user_id=user_id)

    profile.rebuild_customers()
    profile.rebuild_churns()
