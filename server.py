#!/usr/bin/env python

import sys
import json
import time
import struct
import socket
import threading
import collections
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

def gen_songs():
    """
    Endlessly generate Spotify songs
    """
    # buffer a multiple of 3 since we serve three choices per vote
    BUFFER = 40
    SEED_GENRES = ['work-out', 'summer', 'club']
    while True:
        recs = sp.recommendations(seed_genres=SEED_GENRES, limit=30)['tracks']
        # sort by song length for demo
        recs = sorted(recs, key=lambda s: s['duration_ms'])
        for song in recs:
            yield song

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
# setup socket
# --------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# the empty string here indicates INADDR_ANY for the server address
server_address = ('', port)
sock.bind(server_address)

MAX_DATA = 4096
REGISTER_MSG = "1"
ACK_MSG = "2"
SONGS_MSG = "3"
VOTE_MSG = "4"
UNREGISTER_MSG = "5"

# --------------------
# setup data stuctures
# --------------------
songs = gen_songs()
clients = []
tally = collections.Counter()
client_lock = threading.Lock()
tally_lock = threading.Lock()
sock_write_lock = threading.Lock()

def parse_song(s):
    d = {
        'artist': s['album']['artists'][0]['name'],
        'name':   s['name'],
        'length': s['duration_ms'] / 1000,
        'uri':    s['uri'],
            
    }
    return d

def disc_jockey(sock, songs, sock_write_lock, clients, client_lock, tally, tally_lock, spot):
    winner = None

    wait = 30
    while True:
        s1 = parse_song(next(songs))
        s2 = parse_song(next(songs))
        s3 = parse_song(next(songs))

        options_message = json.dumps([s1, s2, s3]) 
        with tally_lock:
            tally.clear()
            tally.update([s1['uri'], s2['uri'], s3['uri']])
        with client_lock, sock_write_lock:
            for client in clients:
                sock.sendto(SONGS_MSG + options_message, client)
                sys.stderr.write("Just sent songs to client\n")

        # otherwise, sleep for time of winner
        sys.stderr.write("Sleeping for %d seconds\n" % (wait))
        time.sleep(wait)

        with tally_lock:
            sys.stderr.write("Deciding the winner\n")
            winner_uri, votes = tally.most_common(1)[0]
            # decide which song this uri corresponds to
            if s1['uri'] == winner_uri:
                winner = s1
            elif s2['uri'] == winner_uri:
                winner = s2
            else:
                winner = s3
            sys.stderr.write("Song %s has won with %d votes\n" % (winner, votes))

        wait = winner['length']

        sys.stderr.write("trying to add track %s\n" % (winner['uri'],))
        sys.stderr.write("playlist id: %s\n" % (pl['id'],))
        spot.user_playlist_add_tracks(user, pl['id'], [winner['uri']])


t = threading.Thread(target=disc_jockey, args=(sock, songs, sock_write_lock, clients, client_lock, tally, tally_lock, sp))
t.start()

while True:
    data, address = sock.recvfrom(MAX_DATA)
    sys.stderr.write("just received data\n")

    if len(data) < 1:
        sys.stderr.write("Read empty data\n")
        continue

    # examine the first byte to figure out what message type was received
    msg = data[0]
    if msg == REGISTER_MSG:
        sys.stderr.write("Got a register message\n")
        delay = 0.0
        try:
            delay = float(data[1:])
            print "Read in a delay of %f" % delay
        except:
            pass

        with client_lock, sock_write_lock:
            clients.append(address)
            sock.sendto(ACK_MSG, address)
            sys.stderr.write("Sent ACK message\n")
    elif msg == VOTE_MSG:
        sys.stderr.write("Got a vote message\n")
        uri = data[1:]
        with tally_lock:
            if uri in tally:
                tally[uri] += 1
                sys.stderr.write("Recorded vote\n")
            else:
                sys.stderr.write("uri not found in tally\n")
    elif msg == UNREGISTER_MSG:
        sys.stderr.write("Got an unregister message\n")
        with client_lock:
            try:
                clients.remove(address)
                sys.stderr.write("Removed client from list\n")
            except ValueError:
                sys.stderr.write("Could not remove client\n")
    else:
        sys.stderr.write("Unrecognized message type: %d\n", msg)
        continue
