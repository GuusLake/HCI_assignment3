#!/usr/bin/python3
# File name: assignment3.py
# Authors: Lakeman, G (s3383180) and Algra, N (s3133125)
# Date: 05-04-20

import tweepy
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import messagebox
import time
import queue
import threading

class CustomStream(tweepy.StreamListener):
    
    def on_status(self, status):
        # Add stuff here to what to do when a tweet appears
        print(status.text)

    def on_error(self, status_code):
        print(status_code)
        if status_code == 401:
            # To prevent logging in in a loop and getting blocked
            quit()
    
class Credentials():

    def read_cred(self):
        f = open('credentials.txt', 'r')
        f_lines = f.readlines()
        self.consumer_key = f_lines[0].rstrip()
        self.consumer_secret = f_lines[1].rstrip()
        self.access_token = f_lines[2].rstrip()
        self.access_secret = f_lines[3].rstrip()
        
    def start_stream(self):
        # Get credentials and create api
        self.read_cred()
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_secret)
        self.api = tweepy.API(self.auth)
        
        # start stream
        self.stream_listener = CustomStream()
        self.stream = tweepy.Stream(auth = self.api.auth, listener = self.stream_listener)
        self.stream.filter(track = ['is'])

def main():
    api = Credentials()
    api.start_stream()

if __name__ == "__main__":
    main()
