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
import pprint

# setup command line arguments
if len(sys.argv) != 2:
    sys.stderr.write('Usage: %s <port>\n' % sys.argv[0])
    sys.exit()

# parse port and set some global variables
port = int(sys.argv[1])
tstamp = None
options_message = None
vote_length = None

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

# --------------------
# perform Spotify setup
# --------------------
PLAYLIST_NAME = 'networks-playlist'

def parse_song(s):
    d = {
        'artist':  s['album']['artists'][0]['name'],
        'name':    s['name'],
        'length':  s['duration_ms'] / 1000.0,
        'uri':     s['uri'],
    }
    return d

def gen_songs():
    """
    Endlessly generate Spotify songs
    """
    # buffer a multiple of 3 since we serve three choices per vote
    BUFFER = 100
    SEED_GENRES = ['work-out', 'summer', 'club']
    while True:
        recs = sp.recommendations(seed_genres=SEED_GENRES, limit=BUFFER)['tracks']
        # sort by song length for demo
        recs = sorted(recs, key=lambda s: s['duration_ms'])
        for song in recs:
            data = song['name'] + song['album']['artists'][0]['name']
            if not is_ascii(data):
                sys.stderr.write("skipping song with non-ascii\n")
                continue
            yield song

# prompt for username and attempt Spotify authentication
username = raw_input('What is your Spotify username?\n> ')
scope = 'user-modify-playback-state playlist-modify-public user-modify-playback-state user-modify-playback-state'
redirect = 'http://localhost/'
token = spotipy.util.prompt_for_user_token(username, scope, redirect_uri=redirect)

# exit if authentication failed
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

# start/resume the playlist
sp.start_playback(context_uri=pl['uri'])


# --------------------
# socket setup 
# --------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# the empty string here indicates INADDR_ANY for the server address
server_address = ('', port)
sock.bind(server_address)

# define constants for application messages
# NOTE: would be a good place for an enum if Python had strong support for them 
MAX_DATA = 4096
REGISTER_MSG = "1"
ACK_MSG = "2"
SONGS_MSG = "3"
VOTE_MSG = "4"
UNREGISTER_MSG = "5"

# --------------------
# setup shared data
# --------------------
songs = gen_songs()
clients = {}
tally = collections.Counter()
client_lock = threading.Lock()
tally_lock = threading.Lock()
sock_write_lock = threading.Lock()


# threaded function that sends out song candidates to clients
def disc_jockey(sock, songs, sock_write_lock, clients, client_lock, tally, tally_lock, spot):
    global tstamp
    global options_message
    global vote_length
    winner = None

    # use 45 seconds for the first vote to let clients attach
    vote_length = 45

    while True:
        s1 = parse_song(next(songs))
        s2 = parse_song(next(songs))
        s3 = parse_song(next(songs))

        options_message = json.dumps({'songs': [s1, s2, s3],
                                      'deadline': time.time() + vote_length})

        with tally_lock:
            # clear Counter and set up new entries
            tally.clear()
            tally[s1['uri']] = 0
            tally[s2['uri']] = 0
            tally[s3['uri']] = 0

        with client_lock, sock_write_lock:
            tstamp = time.time()
            for client in clients:
                sock.sendto(SONGS_MSG + options_message, client)
                sys.stderr.write("Just sent options to a client\n")

        # sleep during the voting session
        sys.stderr.write("Sleeping during the vote\n")
        time.sleep(vote_length)

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
            # pprint.pprint(tally)
            for identifier, score in tally.iteritems():
                sys.stderr.write("%s: %f\n" % (identifier, score))
            sys.stderr.write('Song "%s" has won with %f votes\n' % (winner['name'], votes))

        # change back to 30 seconds after the first vote
        vote_length = 30
        spot.user_playlist_add_tracks(user, pl['id'], [winner['uri']])
        sys.stderr.write("Sleeping until next vote\n")
        time.sleep(winner['length'] - vote_length)


t = threading.Thread(target=disc_jockey, args=(sock, songs, sock_write_lock, clients, client_lock, tally, tally_lock, sp))
t.start()

while True:
    data, address = sock.recvfrom(MAX_DATA)

    if len(data) < 1:
        sys.stderr.write("Read empty data\n")
        continue

    # examine the first byte to figure out what message type was received
    msg = data[0]
    if msg == REGISTER_MSG:
        delay = 0.0
        try:
            delay = float(data[1:])
            sys.stderr.write("Registering new client with a %f sec delay\n" % delay)
        except:
            pass

        with client_lock, sock_write_lock:
            clients[address] = delay
            sock.sendto(ACK_MSG, address)
        with client_lock, sock_write_lock:
            sock.sendto(SONGS_MSG + options_message, address)
    elif msg == VOTE_MSG:
        uri = data[1:]
        with tally_lock:
            votetime = time.time() - tstamp
            if uri in tally:
                score = (vote_length - votetime + clients[address]) / float(vote_length)
                tally[uri] += max(score, 0)
                sys.stderr.write("Recorded %f votes for %s\n" % (score, uri))
            else:
                sys.stderr.write("A URI not found in tally\n")
    elif msg == UNREGISTER_MSG:
        with client_lock:
            try:
                clients.pop(address)
                sys.stderr.write("Removed client from list\n")
            except ValueError:
                sys.stderr.write("Could not remove client\n")
    else:
        sys.stderr.write("Unrecognized message type: %d\n", msg)
        continue
