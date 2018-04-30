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
import thread


# Request types
REGISTER   = '1'
ACK        = '2'
OPTIONS    = '3'
VOTE       = '4'
UNREGISTER = '5'

MAX_TIMEOUTS  = 3
TIMEOUT_SECS  = 3


partify = "\n\n                                ___              .-.                \n                               (   )      .-.   /    \              \n   .-..     .---.   ___ .-.     | |_     ( __)  | .`. ;   ___  ___  \n  /    \   / .-, \ (   )   \   (   __)   (''')  | |(___) (   )(   ) \n ' .-,  ; (__) ; |  | ' .-. ;   | |       | |   | |_      | |  | |  \n | |  . |   .'`  |  |  / (___)  | | ___   | |  (   __)    | |  | |  \n | |  | |  / .'| |  | |         | |(   )  | |   | |       | '  | |  \n | |  | | | /  | |  | |         | | | |   | |   | |       '  `-' |  \n | |  ' | ; |  ; |  | |         | ' | |   | |   | |        `.__. |  \n | `-'  ' ' `-'  |  | |         ' `-' ;   | |   | |        ___ | |  \n | \__.'  `.__.'_. (___)         `.__.   (___) (___)      (   )' |  \n | |                                                       ; `-' '  \n(___)                                                       .__.'   \n\n"


def beep():
	print "\a",


def input_with_timeout(prompt, timeout):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    ready, _, _ = select.select([sys.stdin], [],[], timeout)
    if ready:
        return sys.stdin.readline().rstrip('\n') # expect stdin to be line-buffered
    raise TimeoutExpired



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

	print "\n   {} {} {}".format(string.ljust('Name', longName + extraSpace), string.ljust('Artist', longArtist + extraSpace), string.ljust('Length', longLength + extraSpace))

	i = 0
	indices = ['a', 'b', 'c']
	for song in options:
		print "{}) {} {} {}".format(indices[i], string.ljust(song['name'], longName + extraSpace), string.ljust(song['artist'], longArtist + extraSpace), string.ljust(song['length'], longLength + extraSpace))
		i += 1


def vote(sock, sockData, options):
	timeLeft = int(options['deadline'] - time.time())
	minsLeft = timeLeft / 60
	secsLeft = timeLeft % 60

	vote = ''
	letters = {'a', 'b', 'c'}
	
	os.system('clear')
	displayOptions(options['songs'])
	print "\nType 'a', 'b' or 'c' to vote for an option."

	if minsLeft > 0:
		print "You have {}m and {}s to choose!".format(minsLeft, secsLeft)
	else:
		print "You have {} seconds to choose!".format(secsLeft + 1)

	while True:
		try:
			vote = input_with_timeout("\n", float(options['deadline'] - time.time()))
		except:
			print "Wake up! You didn't vote in time. But no worries, there will be more."
			return ''
		else:
			if vote not in letters:
				print "'{}' isn't a valid vote. Please choose a valid option!".format(vote)
				continue
			else:
				print "Voted for option '{}'. Great choice! Stay tuned for the next options :)".format(vote)
				if vote == 'a':
					return options['songs'][0]['uri']
				elif vote == 'b':
					return options['songs'][1]['uri']
				elif vote == 'c':
					return options['songs'][2]['uri']



def play(sock, sockData):
	while True:
		try:
			data, _ = sock.recvfrom(512)
			if len(data) > 1:
				msgType = data[0]

				if msgType == OPTIONS:
					options = json.loads(data[1:])

					if (options['deadline'] - time.time()) < 0:
						print "There's no voting sessions at the moment. \nI'll let you know when the next session comes up!"
						continue

					result = vote(sock, sockData, options)
					if result == '':
						continue
					else:
						msg = VOTE + result
						time.sleep(RTT)
						sock.sendto(msg, sockData)
		except:
			continue




def register(sock, sockData):
	registerMsg = REGISTER + str(RTT)
	nTimeouts = 0
	
	time.sleep(RTT)
	sock.sendto(registerMsg, sockData)

	while nTimeouts < MAX_TIMEOUTS:
		try:
			print "Waiting for registration acknowledgement. Attempt {}/{}".format(nTimeouts + 1, MAX_TIMEOUTS)
			data, _ = sock.recvfrom(1)
			msgType = unpack('c', data)[0]
			if msgType == ACK:
				print "Registered successfully!"
				return True
		except:
			nTimeouts += 1
			beep()
			time.sleep(RTT)
			print("Timeout #{}".format(nTimeouts))
			if nTimeouts != MAX_TIMEOUTS:
				time.sleep(RTT)
				sock.sendto(registerMsg, sockData)

	return False



def run(sock, sockData):
	sock.settimeout(5.0)

	if not register(sock, sockData):
		print("Exceeded number of timeouts registering.\nPlease check your Internet connection and try again later :)")
		exit()

	play(sock, sockData)
		


def main():
	if len(sys.argv) < 3:
		print "Usage: python client.py [Destination IP] [Destination PORT]"
		sys.exit(0)
	else:
		UDP_IP_ADDRESS = sys.argv[1]
		UDP_PORT_NO = int(sys.argv[2])

	os.system('clear')
	print partify

	global RTT
	RTT = 0

	print "Hey there Partifier, and welcome to the best and most entertaining \nway to make a collaborative playlist with your friends.\n"
	print "Our application uses clients' latency to make up for user \ndelays when computing the 'weight' of their vote.\n"

	RTT = float(raw_input("For the purpose of this demo, what RTT (in seconds, between 0 and 10) \nwould you like us to simulate for you? "))

	if (RTT <= 10 and RTT >=0):
		print "\nSounds good! Simulating connection with RTT of {} seconds.\n".format(RTT)
	elif (RTT > 10):
		RTT = 10
		print "\nWhoops! The number you entered is way too big, so we capped it to 10s!\n"
	elif (RTT < 0):
		RTT *= -1
		print "Hmmmmm, you typed a negative number. We'll just assume you \nmeant positive {} :) \nSimulating connection with RTT of {} seconds!\n".format(RTT, RTT)

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	run(sock, (UDP_IP_ADDRESS, UDP_PORT_NO))


if __name__ == '__main__':
	main()