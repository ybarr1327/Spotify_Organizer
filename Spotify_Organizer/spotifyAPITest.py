import spotipy
from spotipy.oauth2 import SpotifyOAuth

import credentials as cred


def authorize(scope):
    try:
        sp_oauth = SpotifyOAuth(cred.CLIENT_ID, cred.CLIENT_SECRET, cred.REDIRECT_URI, scope=scope)

        sp = spotipy.Spotify(auth_manager=sp_oauth)

        return sp, sp_oauth
    except:
        print("There was a problem with authentication")
        exit(1)


def get_recently_played(sp):
    num_songs = input("How many songs to retrieve? (Max = 50) ")

    if num_songs.isnumeric():
        num_songs = int(num_songs)
    else:
        print('Invalid input, returning to menu')
        return

    if 0 < num_songs <= 50:
        results = sp.current_user_recently_played(limit=num_songs)
        print_recently_played_tracks(results)
    elif num_songs <= 0:
        print('Invalid input, returning to menu')
        return
    else:
        results = sp.current_user_recently_played(limit=50)
        print_recently_played_tracks(results)


def print_recently_played_tracks(results):
    track_num = 1
    for item in results['items']:
        track = item['track']
        print('-------------------------------------------')
        print('Track', str(track_num))
        track_num += 1
        print('Artists:', end=' ')
        for artists in track['artists']:
            print(artists['name'], end=" ")

        print('\nAlbum Name:', track['album']['name'])

        print('Song Name:', track['name'])
    print('-------------------------------------------')


def get_saved_albums(sp: spotipy.Spotify):
    print("Processing...")

    results = sp.current_user_saved_albums(limit=50)

    total_songs_count = results['total']

    if total_songs_count > 0:

        all_albums = []
        for item in results['items']:
            all_albums.append(item['album']['name'])
        while results['next']:  # repeat until reaching the end of the json
            results = sp.next(results)
            for item in results['items']:
                all_albums.append(item['album']['name'])

        all_albums.sort()

        print('0: Save the albums to file \'saved_albums.txt\'')
        print('1: Print the saved albums')
        print('2: Return To Menu')
        x = input('Selection an option:')

        if x == '0':
            saved_albums = open("saved_albums.txt", 'w')
            for i in all_albums:
                if i == all_albums[-1]:
                    saved_albums.write(i)
                else:
                    saved_albums.write(i + '\n')
            saved_albums.close()
        elif x == '1':
            for i in all_albums:
                print(i)
        elif x == '2':
            return
        else:
            print('Invalid Input, returning to the Menu')
            return

    else:
        print("There are no albums to print")


# def print_saved_albums_from_file():
#     if not path.exists('saved_albums.txt') or not path.getsize('saved_albums.txt'):
#         print("Must First Run Get Saved Albums command")
#         return
#     else:
#         saved_albums = open('saved_albums.txt', 'r')
#         print(saved_albums.read())
#         saved_albums.close()


def get_saved_albums_songs(sp: spotipy.Spotify):
    results = sp.current_user_saved_albums(limit=50)  # start with a limit of 50
    total_albums_to_get = results['total']  # store the number of albums that will be searched aka all of them
    if total_albums_to_get == 0:
        print("There are no saved albums")
        return
    ans = input('About to look through ' + str(total_albums_to_get) + ' albums. Proceed? Y/N ')

    if ans == 'N' or ans == 'n':
        return
    elif ans == 'Y' or ans == 'y':

        print("Processing...")
        total_song_count = 0
        total_album_count = 0

        all_songs = []

        def parse_results(album_count, song_count):
            for item in results['items']:
                album_count += 1
                for tracks in item['album']['tracks']['items']:
                    all_songs.append(tracks['id'])
                    song_count += 1
            return album_count, song_count

        total_album_count, total_song_count = parse_results(total_album_count, total_song_count)
        while results['next']:  # repeat until reaching the end of the json
            results = sp.next(results)
            total_album_count, total_song_count = parse_results(total_album_count, total_song_count)

        print("Retrieved", total_song_count, 'songs from', total_album_count, 'albums')
        print('0: Save the tracks to liked songs')
        print('1: Return To Menu')
        x = input('Selection an option:')
        if x == '0':
            add_songs(sp, all_songs)
        elif x == '1':
            return
        else:
            print('Invalid Input, returning to the Menu')
            return


    else:
        print('Invalid Input, returning to main menu.')


def add_songs(sp: spotipy.Spotify, songs: list):
    print('Processing...')

    total_songs_count = len(songs)

    for i in range(0, total_songs_count, 50):
        if i + 50 >= total_songs_count:
            chunk = songs[i:total_songs_count]
            sp.current_user_saved_tracks_add(chunk)
            break
        chunk = songs[i:i + 50]
        sp.current_user_saved_tracks_add(chunk)

    # for i in songs:
    #     if not sp.current_user_saved_tracks_contains([i]):
    #         sp.current_user_saved_tracks_add([i])


def del_all_liked_songs(sp: spotipy.Spotify):
    def parse_results():
        for item in results['items']:
            all_songs.append(item['track']['id'])

    print('Processing...')
    results = sp.current_user_saved_tracks(limit=50)
    total_songs_count = results['total']

    if total_songs_count == 0:
        print('There are no songs saved in th library')
        return

    all_songs = []
    parse_results()
    i = len(results['items'])
    while i < total_songs_count:  # repeat until reaching the end of the json
        results = sp.next(results)
        parse_results()
        i += len(results['items'])

    ans = input('There are ' + str(total_songs_count) + ' songs in your library. Proceed with Deletion? Y/N')
    if ans == 'N' or ans == 'n':
        return
    elif ans == 'Y' or ans == 'y':
        print('Processing...')
        for i in range(0, total_songs_count, 50):
            if i + 50 >= total_songs_count:
                chunk = all_songs[i:total_songs_count]
                sp.current_user_saved_tracks_delete(chunk)
                break
            chunk = all_songs[i:i + 50]
            sp.current_user_saved_tracks_delete(chunk)
        print('Complete')
    else:
        print('Invalid Input, returning to main menu.')


def main():
    # scope holds the spotify permissions needed to modify the users account
    scope = "user-read-recently-played user-library-read user-library-modify"
    # spotify api authentication
    sp_oauth: SpotifyOAuth
    sp: spotipy.Spotify
    # checks if spotify api variables were set
    is_auth = False

    while True:
        # menu
        print('------------------------------------------------')
        print("Please enter a selection from the menu below:")
        print("0 - Authorize spotify")
        print("1 - Get Recently Played Songs")
        print("2 - Get Saved Albums")
        print('3 - Get All Tracks From All Saved Albums')
        print('4 - Delete all liked tracks')
        print("end - Exit Program")
        print('------------------------------------------------')
        selection = input('Selection: ')

        # input selection
        if selection == '0':
            if not is_auth:
                sp, sp_oauth = authorize(scope)
                is_auth = True
        else:
            if not is_auth:
                sp, sp_oauth = authorize(scope)
                is_auth = True

            if selection == '1':
                get_recently_played(sp)
            elif selection == '2':
                get_saved_albums(sp)
            elif selection == '3':
                get_saved_albums_songs(sp)
            elif selection == '4':
                del_all_liked_songs(sp)
            elif selection == 'end':
                exit(0)


if __name__ == '__main__':
    main()
