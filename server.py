#!/usr/bin/env python

import sys
import json
import struct
import socket
import spotipy
import spotipy.util

if len(sys.argv) != 2:
    sys.stderr.write('Usage: %s <port>\n' % sys.argv[0])
    sys.exit()

port = int(sys.argv[1])

# --------------------
# perform Spotify setup
# --------------------
PLAYLIST_NAME = 'networks-playlist'

def gen_songs(n):
    """
    Endlessly generate n-tuples of Spotify songs
    """
    SEED_GENRES = ['work-out', 'summer', 'club']
    while True:
        recs = sp.recommendations(seed_genres=SEED_GENRES, limit=20)['tracks']
        for i in xrange(0, len(recs), n):
            group = tuple(recs[i:i+n])
            if len(group) == n:
                yield group

# prompt for username and attempt authentication
username = raw_input('What is your Spotify username?\n> ') 
scope = 'user-modify-playback-state playlist-modify-public user-modify-playback-state user-modify-playback-state'
redirect = 'http://localhost/'
token = spotipy.util.prompt_for_user_token(username, scope, redirect_uri=redirect)

# if authentication failed
if not token:
    sys.stderr.write('Could not authenticate user')
    sys.exit()

# initiate Spotify client
sp = spotipy.Spotify(auth=token)
user = sp.me()['id']

# get all playlists that match the name PLAYLIST_NAME
playlists = filter(lambda pl: pl['name'] == PLAYLIST_NAME, sp.current_user_playlists()['items'])

# grab first result if there is one, otherwise create it
if playlists:
    pl = playlists[0]
else:
    pl = sp.user_playlist_create(user, PLAYLIST_NAME)

# start or resume the playlist
sp.start_playback(context_uri=pl['uri'])


# --------------------
# enter loop
# --------------------
MAX_DATA = 4096

REQUEST_MSG = 1
VOTE_MSG = 2
UNAVAIL_MSG = 3
OPTIONS_MSG = 4

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# the empty string here indicates INADDR_ANY for the server address
server_address = ('', port)
sock.bind(server_address)

# sp.user_playlist_add_tracks(user, pl['id'], tracks)

while True:
    songs = gen_songs(2)
    data, address = sock.recvfrom(MAX_DATA)

    if len(data) < 1:
        sys.stderr.write("Read some empty data\n")
        continue

    # examine the first byte to figure out what message type was received
    msg = data[0]
    if msg == REQUEST_MSG:
        print "got a request message"
    elif msg == VOTE_MSG:
        # TODO: tally votes
        print "got a vote message"

    response = struct.pack('!b', UNAVAIL_MSG)
    sent = sock.sendto(response, address)
