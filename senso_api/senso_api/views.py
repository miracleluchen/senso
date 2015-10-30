import exceptions
import json
import logging
import traceback
import datetime

from django.db import transaction
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.utils.timezone import localtime
import collections
from collections import OrderedDict
import api_helpers
import view_helpers
from senso_api import models, settings, logic
from decimal import getcontext, Decimal
logger = logging.getLogger("main")

class ApiView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(ApiView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        reply = view_helpers.ApiJsonReply()
        reply.set_resp(exceptions.ApiHttpMethodNotAllowed())
        return HttpResponse(
            unicode(reply),
            content_type='application/json')

    def post(self, request, *args, **kwargs):
        name = self.__class__.__name__
        logger.info('post begin: %s', name)

        self.api_reply = self.reply_class()

        try:
            api_request = self.request_class(request)
            self.api_reply = self.post_valid(api_request)
        except exceptions.ApiError as e:
            self.api_reply.set_resp(e)
            logger.error(traceback.format_exc())
        except:
            debug = traceback.format_exc()
            logger.error(debug)
            self.api_reply.set_resp(exceptions.ApiUnexpectedError(debug='internal error'))

        logger.info('post end: %s', name)
        return HttpResponse(
            unicode(self.api_reply),
            content_type='application/json')

    def check_client_ip(request):
        return True

class FetchChannelFeedsView(ApiView):
    request_class = view_helpers.FetchFeedRequest
    reply_class = view_helpers.FetchFeedReply

    def post_valid(self, api_request):
        api_reply = self.reply_class()
        channel = api_request.cleaned_data['channel']
        result = api_request.cleaned_data['result']
        start = api_request.cleaned_data['start']
        end = api_request.cleaned_data['end']
        days = api_request.cleaned_data['days']

        ret_data = {'channel':{}, 'feeds':{}}
        try:
            channel = models.Channel.objects.using("slave").get(channel_id=channel)
            # read_key = channel.api_read_key
            # ret_data = api_helpers.get_data_feeds(channel.channel_id, read_key, results=result, start=start, end=end, days=days)

            # process channel data
            sensor_setting = {}
            sensor_setting['name'] = channel.name
            sensor_setting['category'] = channel.category
            for sensor_data in models.AlertSetting.objects.using("slave").filter(channel=channel):
                sensor_setting[sensor_data.sensor.name] = int(sensor_data.value)
                sensor_setting['alert'] = sensor_data.abnormal >= settings.ALERT_LIMIT
                if sensor_data.sensor.id == 1:
                    sensor_setting['valid_from'] = sensor_data.valid_from.strftime("%H:%M:%S")
                    sensor_setting['valid_to'] = sensor_data.valid_to.strftime("%H:%M:%S")
                    sensor_setting['min_value'] = int(sensor_data.min_value)
                    sensor_setting['max_value'] = int(sensor_data.max_value)
                sensor_setting['updated_at'] = logic.format_date(sensor_data.update_time)
            ret_data['channel'].update(sensor_setting)

            # process feeds
            getcontext().prec = 3
            data_feeds = collections.defaultdict(lambda:0)
            for data in models.HistoryFeeds.objects.using("slave").filter(channel=channel, sensor_id=1):
                key = localtime(data.create_time).strftime("%Y%m%d%H")
                if data_feeds[key] == 0:
                    data_feeds[key] = data.value
                else:
                    data_feeds[key] = (data_feeds[key] + data.value) / 2

            ordered = OrderedDict(sorted(data_feeds.items(), key=lambda x:int(x[0]), reverse=True))

            horizen = []
            dataset = []
            for key, value in ordered.iteritems():
                horizen.insert(0, key[-2:]+":00")
                dataset.insert(0, str(value))
                if len(horizen) == 10:
                    break
            ret_data['feeds']['labels'] = horizen
            ret_data['feeds']['data'] = [dataset]

            api_reply.set_field("data", ret_data)
            return api_reply

        except models.Channel.DoesNotExist:
            raise exceptions.ApiChannelNotFound()

class ChannelListView(ApiView):
    request_class = view_helpers.EmptyRequest
    reply_class = view_helpers.EmptyReply

    def post_valid(self, api_request):
        api_reply = self.reply_class()

        # channels = api_helpers.get_channel_list()
        channels = []

        channel_setting_dict = collections.defaultdict(list)
        for alert in models.AlertSetting.objects.using("slave").all():
            setting_dict = collections.defaultdict(dict)
            setting_dict[alert.sensor.name]["max"] = str(alert.max_value)
            setting_dict[alert.sensor.name]["min"] = str(alert.min_value)
            setting_dict[alert.sensor.name]["from"] = alert.valid_from.strftime("%H:%M:%S")
            setting_dict[alert.sensor.name]["to"] = alert.valid_to.strftime("%H:%M:%S")
            setting_dict[alert.sensor.name]["value"] = str(alert.value)
            setting_dict[alert.sensor.name]["update_time"] = logic.format_date(alert.update_time)
            setting_dict[alert.sensor.name]["alert"] = alert.abnormal >= settings.ALERT_LIMIT
            channel_setting_dict[alert.channel.id].append(setting_dict)

        for channel in models.Channel.objects.using("slave").all():
            channel_dict = {}
            channel_dict['name'] = channel.name
            channel_dict['api_key'] = channel.api_write_key
            channel_dict['category'] = channel.get_category_display()
            channel_dict['id'] = channel.channel_id
            channel_dict['status'] = channel_setting_dict[channel.id]

            channels.append(channel_dict)

        api_reply.set_field("data", channels)
        return api_reply

class ChannelCreateView(ApiView):
    request_class = view_helpers.ChannelRequest
    reply_class = view_helpers.EmptyReply

    def post_valid(self, api_request):
        api_reply = self.reply_class()
        cleaned_data = api_request.cleaned_data

        name = cleaned_data['name']
        max_temp = cleaned_data['max_temp']
        min_temp = cleaned_data['min_temp']
        valid_from = cleaned_data['valid_from']
        valid_to = cleaned_data['valid_to']
        category = cleaned_data['category']
        channel = cleaned_data['channel']

        try:
            cha = models.Channel.objects.get(channel_id=channel)
            ret_data = api_helpers.update_channel_info(channel, name)
            if ret_data['id']:
                models.Channel.objects.filter(channel_id=channel).update(
                    name = name,
                    category = category
                )
                models.AlertSetting.objects.filter(channel=cha, sensor_id=1).update(
                    min_value = min_temp,
                    max_value = max_temp,
                    valid_from = valid_from,
                    valid_to = valid_to
                )
            else:
                logger.error("update channel failed, api fail")
                raise exceptions.ApiUpdateChannelError("API Error")

        except models.Channel.DoesNotExist:
            ret_data = api_helpers.create_channel(name)

            if ret_data['id']:
                channel_id = ret_data['id']
                api_read_key, api_write_key = '', ''
                for api_key in ret_data['api_keys']:
                    if api_key['write_flag']:
                        api_write_key = api_key['api_key']
                    else:
                        api_read_key = api_key['api_key']
                try:
                    with transaction.atomic():
                        cha = models.Channel.objects.create(
                            name = name,
                            description = '',
                            category = category,
                            channel_id = channel_id,
                            api_write_key = api_write_key,
                            api_read_key = api_read_key
                        )

                        models.AlertSetting.objects.create(
                            channel = cha,
                            sensor_id = 1, # hard code here, id 1 is sensor temperature
                            min_value = min_temp,
                            max_value = max_temp,
                            valid_from = valid_from,
                            valid_to = valid_to
                        )
                        models.AlertSetting.objects.create(
                            channel = cha,
                            sensor_id = 2, # hard code here, id 1 is sensor temperature
                            min_value = 30,
                            max_value = 80,
                            valid_from = valid_from,
                            valid_to = valid_to
                        )
                        models.AlertSetting.objects.create(
                            channel = cha,
                            sensor_id = 3, # hard code here, id 1 is sensor temperature
                            min_value = 0,
                            max_value = 100,
                            valid_from = valid_from,
                            valid_to = valid_to
                        )

                        ret_data.update({'api_key': api_write_key})
                except Exception as e:
                    logger.error("create channel failed, exception: %s", e)
                    api_helpers.delete_channel(channel_id)
                    raise exceptions.ApiCreateChannelError("Database Error")
            else:
                logger.error("create channel failed, api fail")
                raise exceptions.ApiCreateChannelError("API Error")

        ret_data.pop('api_keys')
        api_reply.set_field("data", ret_data)
        return api_reply


class ChannelDeleteView(ApiView):
    request_class = view_helpers.ChannelDeleteRequest
    reply_class = view_helpers.EmptyReply

    def post_valid(self, api_request):
        channel = api_request.cleaned_data['channel']

        api_reply = self.reply_class()
        res = api_helpers.delete_channel(channel)
        if not 'id' in res:
            raise exceptions.ApiDeleteChannelError("API Error")

        try:
            with transaction.atomic():
                models.AlertSetting.objects.filter(channel_id=channel).delete()
                models.HistoryFeeds.objects.filter(channel_id=channel).delete()
                models.Channel.objects.filter(channel_id=channel).delete()

        except Exception as e:
            logger.error("delete channel failed, exception: %s", e)
            raise exceptions.ApiDeleteChannelError("Database Error")

        return api_reply
