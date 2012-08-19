from celery import task

from stripeboard.board.models import Profile


@task(serializer='json')
def rebuild_caches():
    user_ids = Profile.objects.exclude(access_token=None)\
                              .values_list('user_id', flat=True)

    for user_id in user_ids:
        rebuild_cache.apply_async((user_id,))


@task(serializer='json')
def rebuild_cache(user_id):
    profile = Profile.objects.get(user_id=user_id)

    profile.rebuild_customers()
    profile.rebuild_churns()
