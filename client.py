#!/usr/bin/env python

import sys
import os
import socket
import string
import time
from struct import *
import json
import signal
import select
from time import sleep
import threading
from threading import Thread


# Request types
REGISTER   = '1'
ACK        = '2'
OPTIONS    = '3'
VOTE       = '4'
UNREGISTER = '5'

MAX_TIMEOUTS  = 3
TIMEOUT_SECS  = 3


def interrupted(signum, frame):
	# print ''
    print("Didn't respond in time.")

signal.signal(signal.SIGALRM, interrupted)

def input():
    try:
        foo = raw_input()
        return foo
    except:
        # timeout
        return


def displayOptions(options):
	longLength, longName, longArtist = 0, 0, 0
	extraSpace = 3
	for song in options:
		mins = str(int(song['length']) / 60)
		secs = string.rjust(str(int(song['length']) % 60), 2, '0')
		song['length'] = mins + ':' + secs

	for song in options:
		longLen = max(longLength, len(song['length']))
		longName = max(longName, len(song['name']))
		longArtist = max(longArtist, len(song['artist']))

	print "   {} {} {}".format(string.ljust('Name', longName + extraSpace), string.ljust('Artist', longArtist + extraSpace), string.ljust('Length', longLength + extraSpace))

	i = 0
	indices = ['a', 'b', 'c']
	for song in options:
		print "{}) {} {} {}".format(indices[i], string.ljust(song['name'], longName + extraSpace), string.ljust(song['artist'], longArtist + extraSpace), string.ljust(song['length'], longLength + extraSpace))
		i += 1


voted = False
count = 10

def timeoutVote():
  global voted
  # print "You have ten seconds to answer!"

  i, o, e = select.select( [sys.stdin], [], [], 10 )

  if (i):
    print "You voted for option", sys.stdin.readline().strip()
    voted = True
  else:
    print "You didn't vote in time!"


def countDown():
	global count
	global voted
	while not voted:
  		os.system('clear')
  		displayOptions('')
  		print "Type 'a', 'b' or 'c' to vote for an option. You have {} seconds to choose!".format(count)
    # print count
    	count -= 1
    	sleep(1)


def vote(sock, sockData, optionsJSON):
	print optionsJSON
	# optionsJSON = '[{"name":"Perfect","artist":"Ed Sheeran","uri":"someUriA","length":"213"},{"name":"Hello","artist":"Adele","uri":"someUriB","length":"182"},{"name":"Up&Up","artist":"Coldplay","uri":"someUriC","length":"405"}]'
	options  = json.loads(optionsJSON)
	timeLeft = 30

	vote = ''

	
	signal.alarm(30)
	os.system('clear')
	displayOptions(options) # pass options
	print "Type 'a', 'b' or 'c' to vote for an option. You have {} seconds to choose!".format(timeLeft)
	try:
		signal.alarm(30)
		vote = input()
		print "Voted for option {}. Great choice! Stay tuned for the next options :)".format(vote)
		if vote == 'a':
			return options[0]['uri']
		elif vote == 'b':
			return options[1]['uri']
		elif vote == 'c':
			return options[2]['uri']
		else:
			print "Vote is not valid"
		return vote

	except:
		print "Didn't vote."
	return ''



def play(sock, sockData):
	print "App is now running (play())"
	sock.settimeout(3600)

	while True:
		sock.settimeout(3600)
		try:
			data, _ = sock.recvfrom(512)
			print "Data:"
			print data
			if len(data) > 1:
				msgType = data[0]
				optionsJSON = data[1:]

				if msgType == OPTIONS:
					result = vote(sock, sockData, optionsJSON)
					print result
					msg = VOTE + result
					sock.sendto(msg, sockData)
		except:
			continue




def register(sock, sockData):
	registerMsg = pack('c', REGISTER)
	nTimeouts = 0
	# print registerMsg
	sock.sendto(registerMsg, sockData)
	# time.sleep(2)


	while nTimeouts < MAX_TIMEOUTS:
		try:
			print "Calling recvfrom()"
			data, _ = sock.recvfrom(1)
			msgType = unpack('c', data)[0]
			print "Message type:", msgType
			if msgType == ACK:
				print "Registered successfully!"
				return True

		except:
			nTimeouts += 1
			print("Timeout #{}".format(nTimeouts))
			if nTimeouts != MAX_TIMEOUTS:
				sock.sendto(registerMsg, sockData)
				# time.sleep(2)

	return False



def run(sock, sockData):
	sock.settimeout(5.0)

	if not register(sock, sockData):
		print("Exceeded number of timeouts registering. Exiting program.")
		exit()

	play(sock, sockData)
		


def main():
	if len(sys.argv) < 3:
		print "Usage: python client.py [Destination IP] [Destination PORT]"
		sys.exit(0)

	UDP_IP_ADDRESS = sys.argv[1]
	UDP_PORT_NO = int(sys.argv[2])

	# print("IP: {}\nPORT: {}".format(UDP_IP_ADDRESS, UDP_PORT_NO))

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	run(sock, (UDP_IP_ADDRESS, UDP_PORT_NO))


if __name__ == '__main__':
	main()