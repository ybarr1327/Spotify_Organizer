from django.shortcuts import render, redirect
import os
import uuid
import spotipy

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path(item):
    if not item.session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        item.session['uuid'] = str(uuid.uuid4())
    return caches_folder + item.session.get('uuid')


# Create your views here.

def HomePage(request):
    return render(request, 'HomePage/home.html')


def AccountPage(request):
    if not request.session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        request.session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path(request))
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope='user-read-recently-played user-top-read user-library-read user-library-modify',
        cache_handler=cache_handler,
        show_dialog=True
    )
    if request.GET.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.GET.get("code"))
        return redirect('/account')

    if request.GET.get("error") == 'access_denied':
        # print(request.GET.get("error"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()

        return redirect(auth_url)

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    return render(request, 'AccountPage/account.html', {'ME': spotify.me()})


def sign_out(request):
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path(request))
        request.session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    return redirect('/')


def recently_played(request):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path(request))
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    results = spotify.current_user_recently_played(limit=50)

    return render(request, 'AccountPage/recently_played.html', {'recently_played': results['items']})


def top_artists(request):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path(request))
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    results = spotify.current_user_top_artists(limit=request.GET.get('num_top_artists', 25),
                                               time_range=request.GET.get('time_range_top_artists', 'medium_term'))

    return render(request, 'AccountPage/top_artists.html', {'top_artists': results['items']})


def top_tracks(request):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path(request))
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    results = spotify.current_user_top_tracks(limit=request.GET.get('num_top_tracks', 25),
                                              time_range=request.GET.get('time_range_top_tracks', 'medium_term'))

    return render(request, 'AccountPage/top_tracks.html', {'top_tracks': results['items']})


class SavedAlbum:
    def __init__(self, album_name, creator, date_added, album_id):
        self.album_name = album_name
        self.creator = creator
        self.date_added = date_added
        self.album_id = album_id


def view_all_saved_albums(request):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path(request))
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    if request.method == 'POST':
        if 'delete_selected_albums_btn' in request.POST:
            checkboxes = request.POST.getlist('album_cb')
            total_to_del = len(checkboxes)

            for i in range(0, total_to_del, 50):
                if i + 50 >= total_to_del:
                    chunk = checkboxes[i:total_to_del]
                    spotify.current_user_saved_albums_delete(chunk)
                    break
                chunk = checkboxes[i:i + 50]
                spotify.current_user_saved_albums_delete(chunk)
        elif 'add_selected_albums_songs_btn' in request.POST:
            checkboxes = request.POST.getlist('album_cb')

            tracks_to_add = []
            for album_id_to_add in checkboxes:
                albums_tracks = spotify.album_tracks(album_id=album_id_to_add, limit=50)
                track_ids = [i['id'] for i in albums_tracks['items']]
                tracks_to_add.extend(track_ids)

            total_songs_count = len(tracks_to_add)

            for i in range(0, total_songs_count, 50):
                if i + 50 >= total_songs_count:
                    chunk = tracks_to_add[i:total_songs_count]
                    spotify.current_user_saved_tracks_add(chunk)
                    break
                chunk = tracks_to_add[i:i + 50]
                spotify.current_user_saved_tracks_add(chunk)

            return redirect('/account')

    results = spotify.current_user_saved_albums(limit=50)

    total_album_count = results['total']

    all_albums = []

    if total_album_count > 0:

        for item in results['items']:
            all_albums.append(SavedAlbum(album_name=item['album']['name'], date_added=item['added_at'],
                                         creator=item['album']['artists'][0]['name'], album_id=item['album']['id']))
        while results['next']:  # repeat until reaching the end of the json
            results = spotify.next(results)

            for item in results['items']:
                all_albums.append(SavedAlbum(album_name=item['album']['name'], date_added=item['added_at'],
                                             creator=item['album']['artists'][0]['name'], album_id=item['album']['id']))

        sorted_by = request.GET.get('sorted_by', 'album_name')

        if sorted_by == 'album_name':
            all_albums.sort(key=lambda x: x.album_name)
        elif sorted_by == 'creator':
            all_albums.sort(key=lambda x: x.creator)
        elif sorted_by == 'recently_added':
            all_albums.sort(key=lambda x: x.date_added, reverse=True)

        return render(request, 'AccountPage/saved_albums.html', {'all_albums': all_albums})
    else:
        return redirect('/account')


class SavedTrack:
    def __init__(self, track_name, creator, date_added, album_name, track_id):
        self.track_name = track_name
        self.creator = creator
        self.date_added = date_added
        self.album_name = album_name
        self.track_id = track_id


def view_all_saved_tracks(request):
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path(request))
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    if request.method == 'POST':
        if 'delete_selected_tracks_btn' in request.POST:
            checkboxes = request.POST.getlist('track_cb')
            total_to_del = len(checkboxes)

            for i in range(0, total_to_del, 50):
                if i + 50 >= total_to_del:
                    chunk = checkboxes[i:total_to_del]
                    spotify.current_user_saved_tracks_delete(chunk)
                    break
                chunk = checkboxes[i:i + 50]
                spotify.current_user_saved_tracks_delete(chunk)

    results = spotify.current_user_saved_tracks(limit=50)

    total_tracks_count = results['total']

    all_tracks = []

    if total_tracks_count > 0:

        for item in results['items']:
            all_tracks.append(SavedTrack(track_name=item['track']['name'], creator=item['track']['artists'][0]['name'],
                                         date_added=item['added_at'], album_name=item['track']['album']['name'],
                                         track_id=item['track']['id']))
        while results['next']:  # repeat until reaching the end of the json
            results = spotify.next(results)

            for item in results['items']:
                all_tracks.append(
                    SavedTrack(track_name=item['track']['name'], creator=item['track']['artists'][0]['name'],
                               date_added=item['added_at'], album_name=item['track']['album']['name'],
                               track_id=item['track']['id']))

        sorted_by = request.GET.get('sorted_by', 'track_name')

        if sorted_by == 'track_name':
            all_tracks.sort(key=lambda x: x.track_name)
        elif sorted_by == 'creator':
            all_tracks.sort(key=lambda x: x.creator)
        elif sorted_by == 'recently_added':
            all_tracks.sort(key=lambda x: x.date_added, reverse=True)
        elif sorted_by == 'album_name':
            all_tracks.sort(key=lambda x: x.album_name)

        return render(request, 'AccountPage/saved_tracks.html', {'all_tracks': all_tracks})
    else:
        return redirect('/account')
