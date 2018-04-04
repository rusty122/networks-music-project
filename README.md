# networks-music-project
A project to cooridinate voting on a Spotify playlist.

## Server Dependency Installation
This project requires a version of the spotipy library that is unavailable on
PyPI. To install it (from a virtual environment if applicable):
```
$ git clone https://github.com/plamere/spotipy.git
$ cd spotipy && python spotipy/setup.py install
```

## Server API Credentials
We use the [Spotify Web API](https://beta.developer.spotify.com/documentation/web-api/)
to generate songs and update the central playlist. For this, you need to [register an
application](https://beta.developer.spotify.com/dashboard/) with Spotify. Once set up,
you can store your credentials in the server environment as shell environment
variables. With Bash:
```
$ export SPOTIPY_CLIENT_ID='your-spotify-client-id'
$ export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
```

# Architecture
The project follows a client-server architecture.
