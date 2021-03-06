from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    url(r'^feeds/$', views.FetchChannelFeedsView.as_view(), name='fetch_channel_feeds'),
    url(r'^channels/$', views.ChannelListView.as_view(), name='channel_list'),
    url(r'^channels/new/$', views.ChannelCreateView.as_view(), name='channel_new'),
    url(r'^channels/delete/$', views.ChannelDeleteView.as_view(), name='channel_delete'),
    url(r'^update/$', views.update_feed, name='feed_update'),
)
