#!/usr/bin/env python

import sys
import os
import socket
import string
import time
# import struct
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
OPTION     = '3'
VOTE       = '4'
UNREGISTER = '5'

MAX_TIMEOUTS  = 3
TIMEOUT_SECS  = 3


def interrupted(signum, frame):
	# print ''
    print("Didn't respond within 1 seconds")

signal.signal(signal.SIGALRM, interrupted)

def input():
    try:
        foo = raw_input()
        return foo
    except:
        # timeout
        return

# set alarm
# signal.alarm(1) # seconds of timeout
# s = input()
# disable the alarm after success
# signal.alarm(0)
# print 'You typed', s





def displayOptions(options):
	print 'Options are:\nA) Ed Sheeran - Shape Of You\nB) Kanye West - Runaway\nC) Nicky Jam - X\n'


# def vote(sock, sockData, optionsJSON):
# 	# options  = json.loads(optionsJSON)
# 	timeLeft = 29

# 	vote = ''

# 	while (timeLeft > 0):
# 		signal.alarm(1)
# 		# os.system('clear')
# 		displayOptions('') # pass options
# 		print "Type 'A', 'B' or 'C' to vote for an option. You have {} seconds to choose!".format(timeLeft)
# 		vote = input()

# 		if not vote:
# 			print "Hasn't voted"
# 			timeLeft -= 1
# 			continue
# 		else:
# 			print "Voted for option {}. Great choice! Stay tuned for the next options :)".format(vote)
# 			return vote
# 	return ''

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
  		print "Type 'A', 'B' or 'C' to vote for an option. You have {} seconds to choose!".format(count)
    # print count
    	count -= 1
    	sleep(1)

# Thread(target = timeoutVote).start()
# Thread(target = countDown).start()


def vote(sock, sockData, optionsJSON):
	# Thread(target = timeoutVote).start()
	# Thread(target = countDown).start()


	# options  = json.loads(optionsJSON)
	timeLeft = 29

	vote = ''

	while (timeLeft > 0):
		signal.alarm(1)
		# os.system('clear')
		displayOptions('') # pass options
		print "Type 'A', 'B' or 'C' to vote for an option. You have {} seconds to choose!".format(timeLeft)
		try:
			signal.alarm(1)
			vote = input()
			print "Voted for option {}. Great choice! Stay tuned for the next options :)".format(vote)
			return vote

		except:
			print "Hasn't voted"
			timeLeft -= 1
			continue			
	return ''



def play(sock, sockData):
	sock.settimeout(None)
	data, _ = recvfrom(512)
	msgType, optionsJSON = unpack('cs', data)

	if msgType == OPTIONS:
		vote(sock, sockData, optionsJSON)




def register(sock, sockData):
	registerMsg = pack('c', REGISTER)
	nTimeouts = 0
	# print registerMsg
	sock.sendto(registerMsg, sockData)
	# time.sleep(2)


	while nTimeouts < MAX_TIMEOUTS:
		try:
			data, _ = recvfrom(1)
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
	# vote(sock, sockData, 'hey')
	sock.settimeout(3.0)

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