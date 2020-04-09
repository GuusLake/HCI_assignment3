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

    def __init__(self, q):
        tweepy.StreamListener.__init__(self)
        self.myQueue = q
    
    def on_status(self, status):
        # Add stuff here to what to do when a tweet appears
        if status.in_reply_to_status_id:
            #print(status.text)
            self.myQueue.sendItem(status)

    def on_error(self, status_code):
        print(status_code)
        if status_code == 401:
            # To prevent logging in in a loop and getting blocked
            quit()


class MyQueue():
    ''' Queue class to transfer new submission data between threads '''
    def __init__(self, maxsize, sendBlock, getBlock):
        self.myqueue=queue.Queue(maxsize)
        self.sendBlock = sendBlock
        self.getBlock = getBlock

    def sendItem(self,item):
        ''' Add item to queue '''
        self.myqueue.put(item, block=self.sendBlock)

    def getNextItem(self):
        ''' Get item from queue '''
        message=self.myqueue.get(block=self.getBlock)
        return message


class Credentials():
    def __init__(self, queue):
        self.queue = queue
        #temp
        self.lang = ['en']
        self.keywords = ['corona']

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
        print("Setting up stream...")
        # Get credentials and create api
        self.read_cred()
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_secret)
        self.api = tweepy.API(self.auth)
        
        # create stream
        self.stream_listener = CustomStream(self.queue)
        self.stream = tweepy.Stream(auth = self.api.auth, listener = self.stream_listener)
        
    def set_var(self, languages, keywords, loc_long, loc_lang):
        self.lang = languages
        self.keywords = keywords
        
    def start_stream(self):
        print("Starting stream...")
        threading.Thread(target=lambda: self.stream.filter(languages = self.lang, track = self.keywords), daemon=True).start()
        print("Started stream?!")

class IncomingTweets(tk.Frame):
    ''' Main interface class for the reddit submission stream '''
    def __init__(self, parent, api, queue):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.api = api
        self.queue = queue
        self.dict = dict()
        threading.Thread(target=self.check_queue, daemon=True).start()

        # Make menubar
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load conversation", command=exit)
        self.filemenu.add_command(label="Close current tab", command=exit)
        self.filemenu.add_command(label="exit", command=exit)
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
        
        # Treeview with conversations
        self.tree = ttk.Treeview(self)
        self.yscrollbarTree = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.yscrollbarTree.set)
        self.yscrollbarTree.grid(row=0, column=0, sticky='nse')
        self.tree.grid(column=0, row=0, columnspan=3, sticky= 'nsew')

    def check_queue(self):
        while True:
            try:
                status = self.queue.getNextItem()
                response = self.get_convo_stats(status)
                if len(response[0]) > 1 and len(response[0]) <= 10 and response[1] > 1 and response[1] <= 10:
                    self.add_convo(status)
                print(self.dict)
            except: pass
            time.sleep(0.1)
    
    def get_convo_stats(self, status):
        parent_id = status.in_reply_to_status_id  
        if (parent_id):
            parent = self.api.api.get_status(parent_id)
            author_set, turns = self.get_convo_stats(parent)
            author_set.add(status.author.name)
            turns += 1
            return [author_set, turns]
        else:
            return [{status.author.name},1]

    def add_convo(self, status):
        parent_id = status.in_reply_to_status_id
        if (parent_id):
            try:
                self.dict[parent_id][children].append(status.id)
            except:
                parent = self.api.api.get_status(parent_id)
                self.add_convo(parent)
                self.dict[parent_id][children].append(status.id)
            self.tree.insert(parent_id, 'end', status.id, text=status.text)
        else:
            self.tree.insert('', 'end', status.id, text=status.text)
        self.dict[status.id] = {'author': status.author.name, 'text': status.text, 'parent': parent_id, 'children': list()}


def main():
    queue = MyQueue(100, False, False)
    api = Credentials(queue)
    api.setup_stream()
    root = tk.Tk()
    root.geometry('1280x720')
    inc_tweets = IncomingTweets(root, api, queue)
    inc_tweets.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    root.mainloop()

if __name__ == "__main__":
    main()
