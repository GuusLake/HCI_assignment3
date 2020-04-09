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
import geopy

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
        
    def test_credentials(self):
        self.read_cred()
        try:
            self.test_auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            self.test_auth.set_access_token(self.access_token, self.access_secret)
            self.test_api = tweepy.API(self.test_auth)
            self.test_search = self.test_api.get_user('twitter')
            return True
        except:
            return False
    
    def set_new_cred(self):
        if self.test_credentials():
            self.setup_stream()
            self.start_stream()
        else:
            messagebox.showerror('Error: Wrong Credentials', 'The credentials found in credentials.txt were not accepted by twitter. The previous credentials are being used instead.')
            
        
    def setup_stream(self):
        # Get credentials and create api
        self.read_cred()
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_secret)
        self.api = tweepy.API(self.auth)
        
        # create stream
        self.stream_listener = CustomStream()
        self.stream = tweepy.Stream(auth = self.api.auth, listener = self.stream_listener)
        
    def set_var(self, languages, keywords, loc_long, loc_lang):
        self.lang = languages
        self.keywords = keywords
        
    def start_stream(self):
        self.stream.filter(languages = self.lang, track = self.keywords)

class IncomingTweets(tk.Frame):
    ''' Main interface class for the reddit submission stream '''
    def __init__(self, parent, api):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.api = api

        # Make menubar
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load conversation", command=lambda:self.parent.destroy)
        self.filemenu.add_command(label="Close current tab", command=lambda:self.parent.destroy)
        self.filemenu.add_command(label="exit", command=lambda:self.parent.destroy)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.accountmenu = tk.Menu(self.menubar, tearoff=0)
        self.accountmenu.add_command(label="Load credentials", command=lambda:self.api.set_new_cred())
        self.menubar.add_cascade(label="Account", menu=self.accountmenu)
        self.parent.config(menu=self.menubar)
        
        # Input fields and buttons
        self.lang_string = tk.StringVar()
        self.lang_entry = tk.Entry(self, textvariable=self.lang_string)
        self.lang_string.set("en, nl")
        self.lang_label = tk.Label(self, text='Languages')
        self.lang_label.grid(column=0, row=1, sticky= 'nswe')
        self.lang_entry.grid(column=0, row=2, sticky= 'nswe')
        
        self.key_string = tk.StringVar()
        self.key_entry = tk.Entry(self, textvariable=self.key_string)
        self.key_string.set("Example, #List, @Input")
        self.key_label = tk.Label(self, text='Keywords')
        self.key_label.grid(column=0, row=3, sticky= 'nswe')
        self.key_entry.grid(column=0, row=4, sticky= 'nswe')
        
        self.loc_string = tk.StringVar()
        self.loc_entry = tk.Entry(self, textvariable=self.loc_string)
        self.loc_string.set("Oude Kijk in het Jatstraat 26 Groningen")
        self.loc_label = tk.Label(self, text='Location')
        self.loc_label.grid(column=0, row=5, sticky= 'nswe')
        self.loc_entry.grid(column=0, row=6, sticky= 'nswe')
        

def main():
    api = Credentials()
    api.setup_stream()
    root = tk.Tk()
    root.geometry('1280x720')
    inc_tweets = IncomingTweets(root, api)
    inc_tweets.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    root.mainloop()

if __name__ == "__main__":
    main()
