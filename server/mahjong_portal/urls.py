from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.views.decorators.cache import cache_page

from mahjong_portal.sitemap import (
    ClubSitemap,
    EMATournamentListSitemap,
    PlayerSitemap,
    RatingSitemap,
    StaticSitemap,
    TournamentAnnouncementSitemap,
    TournamentListSitemap,
    TournamentSitemap,
)
from website.views import players_api

sitemaps = {
    "static": StaticSitemap,
    "tournament_list": TournamentListSitemap,
    "ema_tournaments_list": EMATournamentListSitemap,
    "tournament_details": TournamentSitemap,
    "tournament_announcement_details": TournamentAnnouncementSitemap,
    "club_details": ClubSitemap,
    "player_details": PlayerSitemap,
    "rating_details": RatingSitemap,
}

urlpatterns = [
    url(r"^admin/", include(admin.site.urls[:2])),
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(
        r"^sitemap\.xml$",
        cache_page(86400)(sitemap),
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    url("^api/v0/players/$", players_api),
    url(r"^online/", include("online.urls")),
]

urlpatterns += i18n_patterns(
    url(r"", include("website.urls")),
    url(r"^rating/", include("rating.urls")),
    url(r"^tournaments/", include("tournament.urls")),
    url(r"^clubs/", include("club.urls")),
    url(r"^players/", include("player.urls")),
    url(r"^tenhou/", include("player.tenhou.urls")),
    url(r"^ms/", include("player.mahjong_soul.urls")),
    url(r"^system/", include("system.urls")),
    url(r"^ema/", include("ema.urls")),
    url(r"^login/$", auth_views.LoginView.as_view(template_name="account/login.html"), name="login"),
    url(r"^logout/$", auth_views.LogoutView.as_view(), name="logout"),
)
