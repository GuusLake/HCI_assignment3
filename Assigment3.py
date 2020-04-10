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
            print('New credentials will be used the next time the variables are set'
        
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
        
    def set_var(self, lang_loc, key_rad, stream_type):
        self.stream_type = stream_type
        if stream_type == 1 and key_rad:
            if (lang_loc and key_rad):
                try:
                    self.lang = lang_loc.split(', ')
                    self.keywords = key_rad.split(', ')
                    print("Starting stream...")
                    self.stream.filter(languages = self.lang, track = self.keywords, is_async = True)
                    print("Started stream?!")
                except:
                    messagebox.showerror('Error: Input error', 'The given input does not meet the right format, please enter according to the given example. The program will continue to use the old variables')
            else:
                try:
                    self.lang = False
                    self.keywords = key_rad.split(', ')
                    print("Starting stream...")
                    self.stream.filter(track = self.keywords, is_async = True)
                    print("Started stream?!")
                except:
                    messagebox.showerror('Error: Input error', 'The given input does not meet the right format, please enter according to the given example. The program will continue to use the old variables')
                    
        elif (streamtype == 2 and lang_loc and key_rad):
            try:
                self.location = self.geolocator.geocode(location_string)
                rad = convert_to_degrees(int(keyrad))
                self.loc = [self.location.longitude-rad, self.location.latitude-rad, self.location.longitude+rad, self.location.latitude+rad]
                print("Starting stream...")
                self.stream.filter(locations = self.loc, is_async = True)
                print("Starting stream...")
            except:
                messagebox.showerror('Error: Location not found', 'The given location has not been found. The program will continue to use the old variables')
        else:
            if streamtype == 1:
                messagebox.showerror('Error: No input', 'Twitter requires us to give a search term, please enter one. The program will continue to use the old variables')
            else:
                if not(key_Rad):
                    messagebox.showerror('Error: No input', 'Twitter requires us to give a location, please enter one. The program will continue to use the old variables')
                else:
                    messagebox.showerror('Error: No input', 'Twitter requires us to give a radius, please enter one. The program will continue to use the old variables')
        

class IncomingTweets(tk.Frame):
    ''' Main interface class for the Twitter stream '''
    def __init__(self, parent, api, queue):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.api = api
        self.queue = queue
        self.dict = dict()
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
        print(self.option_value.get())
        
    def set_loc_rad(self):
        self.old_lang = self.langloc_string.get()
        self.langloc_string.set(self.old_loc)
        self.langloc_label['text'] = 'Location'
        self.old_key = self.keyrad_string.get()
        self.keyrad_string.set(self.old_rad)
        self.keyrad_label['text'] = 'Radius'
        print(self.option_value.get())
        
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
            return (status.id in self.dict.keys())
            self.tree.insert('', 'end', status.id, text=status.text)
        self.dict[status.id] = {'author': status.author.name, 'text': status.text, 'parent': parent_id, 'children': list()}
        
    def set_variables(self):
        self.api.set_var(self.langloc_string.get(), self.keyrad_string.get(), self.option_value.get())
        self.var_button['text'] = 'Set variables'

def convert_to_degrees(dist):
    return (dist*(1/111))


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
