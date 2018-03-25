#!/usr/bin/env python

import spotipy
import spotipy.util

scope = 'user-library-read'
redirect = 'http://localhost/'
username = raw_input('What is your Spotify username?\n> ') 

token = spotipy.util.prompt_for_user_token(username, scope, redirect_uri=redirect)

if token:
    print "successfully retrieved token"
else:
    print "failed to retrieve token"
