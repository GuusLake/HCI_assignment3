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
from geopy import Nominatim


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
        self.geolocator = Nominatim(user_agent = 'Guus en Nick')
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
        
    def set_var(self, languages, keywords, location_string, radius):
        if languagues:
            self.lang = languages.split(', ')
        else:
            self.lang = False
        self.keywords = keywords.split(', ')
        self.radius = radius
        if location_string:
            try:
                self.location = self.geolocator.geocode(location_string)
                self.loc = [self.location.longitude, self.location.latitude]
            except:
                messagebox.showerror('Error: Location not found', 'The given location has not been found, no location will be used instead')
                self.loc = False
        else:
            self.loc = False
        
        
    def start_stream(self):
        print("Starting stream...")
        threading.Thread(target=lambda: self.stream.filter(languages = self.lang, track = self.keywords), daemon=True).start()
        print("Started stream?!")

class IncomingTweets(tk.Frame):
    ''' Main interface class for the Twitter stream '''
    def __init__(self, parent, api, queue):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.api = api
        self.queue = queue
        self.dict = {'leaves': dict(), 'tweets': dict()}
        self.last_branch_id = 0
        #self.after(100, check_queue)
        threading.Thread(target=self.check_queue, daemon=True).start()

        # Make menubar
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load conversation", command=exit)
        self.filemenu.add_command(label="Save conversation", command=exit)
        self.filemenu.add_command(label="Exit", command=exit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.accountmenu = tk.Menu(self.menubar, tearoff=0)
        self.accountmenu.add_command(label="Load credentials", command=lambda:self.api.set_new_cred())
        self.menubar.add_cascade(label="Account", menu=self.accountmenu)
        self.parent.config(menu=self.menubar)
        
        # Input fields and buttons
        self.langloc_string = tk.StringVar()
        self.langloc_entry = tk.Entry(self, textvariable=self.langloc_string)
        self.langloc_string.set("en, nl")
        self.langloc_label = tk.Label(self, text='Languages')
        self.langloc_label.grid(column=0, row=1, sticky= 'nsw')
        self.langloc_entry.grid(column=0, row=2, columnspan = 2, sticky= 'nswe')
        
        self.keyrad_string = tk.StringVar()
        self.keyrad_entry = tk.Entry(self, textvariable=self.keyrad_string)
        self.keyrad_string.set("Example, #List, @Input")
        self.keyrad_label = tk.Label(self, text='Keywords')
        self.keyrad_label.grid(column=0, row=3, sticky= 'nsw')
        self.keyrad_entry.grid(column=0, row=4, columnspan = 2, sticky= 'nswe')
        self.old_loc = "Oude Kijk in Het Jatstraat 26 Groningen"
        self.old_rad = '50'
        
        self.option_value = tk.IntVar()
        self.option1 = tk.Radiobutton(self, text='Languages and Keywords', variable = self.option_value, value=1, command = lambda: self.set_lan_key())
        self.option1.select()
        self.option1.grid(column=0, row=5, sticky= 'nsw')
        self.option2 = tk.Radiobutton(self, text='Location and Radius', variable = self.option_value, value=2, command = lambda: self.set_loc_rad())
        self.option2.grid(column=0, row=6, sticky= 'nsw')
        
        self.var_button = tk.Button(self, text = "Start stream", command = lambda: self.set_variables())
        self.var_button.grid(column=1, row=5, rowspan =2, sticky = 'nse', padx=15, pady=15)
        
        # Treeview with conversations
        self.tree = ttk.Treeview(self)
        self.yscrollbarTree = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.yscrollbarTree.set)
        self.yscrollbarTree.grid(row=0, column=0, sticky='nse')
        self.tree.grid(column=0, row=0, columnspan=3, sticky= 'nsew')

    def set_lan_key(self):
        self.old_loc = self.langloc_string.get()
        self.langloc_string.set(self.old_lang)
        self.langloc_label['text'] = 'Languages'
        self.old_rad = self.keyrad_string.get()
        self.keyrad_string.set(self.old_key)
        self.keyrad_label['text'] = 'Keywords'
        
    def set_loc_rad(self):
        self.old_lang = self.langloc_string.get()
        self.langloc_string.set(self.old_loc)
        self.langloc_label['text'] = 'Location'
        self.old_key = self.keyrad_string.get()
        self.keyrad_string.set(self.old_rad)
        self.keyrad_label['text'] = 'Radius'
        
    def check_queue(self):
        while True:
            try:
                status = self.queue.getNextItem()
                response = self.get_convo_stats(status, set(), 0)
                if response['old_leaf']:
                    if response['old_leaf'] in self.dict['leaves']:
                        branch_id = self.dict['leaves'][response['old_leaf']]
                        self.dict['leaves'].pop(response['old_leaf'])
                else:
                    self.last_branch_id += 1
                    branch_id = self.last_branch_id
                self.dict['leaves'][status.id] = branch_id
                #TODO
                #if (len(response[0]) > 1 and len(response[0]) <= 10 and response[1] > 1 and response[1] <= 10):
                #    self.add_convo(status)
                print(self.dict)
            except: pass
            time.sleep(0.1)
    
    def get_convo_stats(self, status, total_author_set, total_turns):
        print("doing something with id:")
        print(status.id)
        parent_id = status.in_reply_to_status_id  
        if (parent_id):
            if parent_id in self.dict['tweets']:
                total_author_set = total_author_set.union(self.dict['tweets'][parent_id][author_set])
                total_author_set.add(status.author.name)
                authors = len(total_author_set)
                total_turns = total_turns + self.dict['tweets'][parent_id][turns] + 1
                if (authors > 1 and authors <= 10 and total_turns > 1 and total_turns <= 10):
                    author_set = self.dict['tweets'][parent_id][author_set]
                    author_set.add(status.author.name)
                    turns = self.dict['tweets'][parent_id][turns] + 1
                    self.dict['tweets'][status.id] = {
                        'author': status.author.name, 
                        'text': status.text, 
                        'parent': parent_id, 
                        'author_set': author_set, 
                        'turns': turns
                    }
                    print("found one in dict")
                    return {'author_set': author_set, 'turns': turns, 'old_leaf': parent_id}
                else:
                    print("doesn't meet requirements")
                    print(total_author_set)
                    print(total_turns)
                    return False
            else:
                parent = self.api.api.get_status(parent_id)
                total_author_set.add(status.author.name)
                total_turns = total_turns + 1
                result = self.get_convo_stats(parent, total_author_set, total_turns)
                if result:
                    author_set = result['author_set']
                    author_set.add(status.author.name)
                    turns = result['turns'] + 1
                    self.dict['tweets'][status.id] = {
                        'author': status.author.name, 
                        'text': status.text, 
                        'parent': parent_id, 
                        'author_set': author_set, 
                        'turns': turns
                    }
                    return {'author_set': author_set, 'turns': turns, 'old_leaf': result['old_leaf']}
                else:
                    return False
        else:
            total_author_set.add(status.author.name)
            authors = len(total_author_set)
            total_turns = total_turns + 1
            if (authors > 1 and authors <= 10 and total_turns > 1 and total_turns <= 10):
                print("found one")
                self.dict['tweets'][status.id] = {
                    'author': status.author.name, 
                    'text': status.text, 
                    'parent': parent_id, 
                    'author_set': {status.author.name}, 
                    'turns': 1
                }
                return {'author_set': {status.author.name}, 'turns': 1, 'old_leaf': None}
            else:
                print("doesn't meet requirements")
                print(total_author_set)
                print(total_turns)
                return False

    def add_convo(self, status):
        parent_id = status.in_reply_to_status_id
        if (parent_id):
            try:
                self.dict[parent_id][children].append(status.id)
            except:
                parent = self.api.api.get_status(parent_id)
                self.add_convo(parent)
                self.dict[parent_id][children].append(status.id)
            #self.tree.insert(parent_id, 'end', status.id, text=status.text)
        else:
            return (status.id in self.dict.keys())
            #self.tree.insert('', 'end', status.id, text=status.text)
        self.dict[status.id] = {'author': status.author.name, 'text': status.text, 'parent': parent_id, 'children': list()}

def set_variables(self):
        print(' test')


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
