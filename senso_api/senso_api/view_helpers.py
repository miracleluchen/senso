import json
import logging
import traceback
from django import forms
import exceptions

logger = logging.getLogger('main')

class ApiRequest(object):
    def __init__(self, request):
        self.request = request

class ApiReply(object):pass

class ApiJsonRequest(ApiRequest):
    def __init__(self, request):
        super(ApiJsonRequest, self).__init__(request)

        try:
            content = json.loads(request.body)
        except ValueError:
            logger.error('Request is not valid Json format')
            raise exceptions.ApiInputFormatError('Request is not valid Json format')

        self.clean(content)

    def clean(self, content):
        self.cleaned_data = {}
        for name, field in self.fields:
            value = content.get(name, '')
            try:
                self.cleaned_data[name] = field.clean(value)
            except forms.ValidationError as e:
                msg = '%s: %s' % (name, e)
                logger.error(msg)
                raise exceptions.ApiInputFormatError('%s: %s' % (name, str(e)))

            clean_field = getattr(self, 'clean_%s' % (name,), None)
            if clean_field is not None:
                self.cleaned_data[name] = clean_field()

        return self.cleaned_data

class ApiJsonReply(ApiReply):
    def __init__(self):
        self.content = {
            'resp_code':0,
            'resp_msg':'OK',
        }

    def __unicode__(self):
        return json.dumps(self.content)

    def set_resp(self, e):
        self.content['resp_code'] = e.value
        self.content['resp_msg'] = unicode(e.msg)

    def set_resp_msg(self, message):
        self.content['resp_msg'] = message

    def set_field(self, field, value):
        self.content[field] = value


class EmptyRequest(ApiJsonRequest):
    fields = []

class EmptyReply(ApiJsonReply):pass

class FetchFeedRequest(ApiJsonRequest):
    fields = [
        ('channel', forms.IntegerField()),
        ('result', forms.IntegerField(required=False)),
        ('start', forms.DateTimeField(required=False)),
        ('end', forms.DateTimeField(required=False)),
        ('days', forms.DateTimeField(required=False)),
    ]

class FetchFeedReply(ApiJsonReply):
    pass

class ChannelRequest(ApiJsonRequest):
    fields = [
        ('name', forms.CharField(max_length=50)),
        ('max_temp', forms.DecimalField(max_digits=10, decimal_places=2)),
        ('min_temp', forms.DecimalField(max_digits=10, decimal_places=2)),
        ('valid_from', forms.TimeField()),
        ('valid_to', forms.TimeField()),
        ('category', forms.IntegerField()),
    ]

