from django.conf import settings


def fire(signal_name, obj=None, **kwargs):
    from django.utils.module_loading import import_string
    message = kwargs
    if getattr(settings, 'ARISTOTLE_ASYNC_SIGNALS', False):
        # pragma: no cover -- We've dropped channels, and are awaiting (pun) on celery stuff
        message.update({
            '__object___': {
                'pk': obj.pk,
                'app_label': obj._meta.app_label,
                'model_name': obj._meta.model_name,
            }
        })
        # Channel("aristotle_mdr.contrib.channels.%s" % signal_name).send(message)
    else:
        message.update({'__object__': {'object': obj}})
        import_string("aristotle_mdr.contrib.async_signals.%s" % signal_name)(message)


def safe_object(message):
    __object__ = message['__object__']
    if __object__.get('object', None):
        instance = __object__['object']
    else:
        model = apps.get_model(__object__['app_label'], __object__['model_name'])
        instance = model.objects.filter(pk=__object__['pk']).first()
    return instance
