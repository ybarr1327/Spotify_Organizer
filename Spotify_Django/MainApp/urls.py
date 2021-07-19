"""
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from MainApp import views
from django.urls import path

urlpatterns = [
    path('', views.HomePage, name='home'),
    path('account', views.AccountPage, name='account'),
    path('sign_out', views.sign_out, name='sign_out'),
    path('recently_played', views.recently_played, name='recently_played'),
    path('top_artists', views.top_artists, name='top_artists'),
    path('top_tracks', views.top_tracks, name='top_tracks'),
    path('saved_albums', views.view_all_saved_albums, name='saved_albums'),
    path('saved_tracks', views.view_all_saved_tracks, name='saved_tracks'),
]
