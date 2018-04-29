# Partify
A Networks project that aims to cooridinate voting on a Spotify playlist. It
creates a playlist with the name 'networks-playlist' if one does not already
exist and begins voting sessions where clients can vote on which song to add
next.

## Server Dependency Installation
The client has no external dependencies and the server only has a single
dependency: [spotipy](https://github.com/plamere/spotipy). This project relies
on a version of the spotipy library that is unavailable on the Python Package
Index ([PyPI](https://pypi.org/)), the de facto standard for distributing Python
packages. To install the most recent version of spotipy from source (within a
virtual environment if desired):

```
$ git clone https://github.com/plamere/spotipy.git
$ cd spotipy && python spotipy/setup.py install
```

## Server API Credentials
We use the [Spotify Web API](https://beta.developer.spotify.com/documentation/web-api/)
to generate songs and update the central playlist. For this, you need to [register an
application](https://beta.developer.spotify.com/dashboard/) with Spotify. Once set up,
you can store your credentials in the server context as shell environment
variables. With Bash:
```
$ export SPOTIPY_CLIENT_ID='your-spotify-client-id'
$ export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
```
