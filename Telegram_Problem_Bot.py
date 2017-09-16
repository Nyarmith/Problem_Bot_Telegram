#!/usr/bin/python3

import smtplib
import time
import pickle
import telepot
import os
import yaml
import random
import datetime
import re

BASE_WD = ""  #to be populated by working directory of bot

#--good sorting--
def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)


def get_immediate_subdirectories(a_dir):
    os.chdir('/home/reader/Projects/Problem_Notifier');
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def removekey(d, key):
    r = dict(d)
    del r[key]
    return r

#--Problem Manager Definition
#   1 problemManager = 1 chat
class ProblemManager(object):
    def __init__(self):
        #dict of "source1" :  {"Chapter_1" : {"problems_done" : [], "problems_not_done" : []} , .. "Chapter_2" : {..}},  source2: ...
        self.problems   = {}  
        self.cur_source = None
        self.cur_chap = None
        self.cur_prob = None
        self.duedate = None
        self.selectionMode = 'Random'  #can also be 'Chapter'
        self.joined_usrs= {}  #user1 : 'ready', user2 : 'ready', user3 : 'not-ready', etc... (but with True and False)
        #populate problems

    #select pool to draw problems from
    def selectSource(self, src):
        if src in self.problems.keys():
            self.cur_source = src
            return True
        else:
            return False

    #def sendChapterProblem(source, chapter): # TODO: as part of mode

    def addUser(self, uname):
        print (uname)
        if uname['id'] not in self.joined_usrs.keys():
            self.joined_usrs[uname['id']] = False
            return True
        else:
            return False

    def rmUser(self, uname):
        if uname['id'] in self.joined_usrs.keys():
            removeKey(self.joined_usrs, uname['id'])
            return True
        else:
            return False

    def isUserInPool(self, uname):
        return uname['id'] in self.joined_usrs.keys()

    #set a user's state, True means the user has understood and is able to move on, False means they have not and are not ready
    def flagUser(self, uname, state):
        self.joined_usrs[uname['id']] = state

    def setSelectionMode(self, mode):
        if mode == 'Random':
            self.selectionMode = 'Random'
            return 0
        elif mode == 'Chapter':
            self.selectionMode = 'Chapter'
            return 0
        else:
            return -1

    #dispenses the next problem (TODO: based on the dispense-mode)
    def dispense(self):
        #first fresh problem from random chapter
        if self.cur_prob != None and not self.all_ready():
            return -1;
        if self.cur_source == None:
            return -2;
        if self.selectionMode == 'Random':
            return self.dispenseRandom()
        elif self.selectionMode == 'Chapter':
            return self.dispenseChapter()

    def dispenseChapter(self):
        #mark previous problem as done
        if self.cur_prob != None:
            self.problems[self.cur_source][self.cur_chap]['problems_done'].append(self.problems[self.cur_source][self.cur_chap]['problems_not_done'][0])
            del self.problems[self.cur_source][self.cur_chap]['problems_not_done'][0]
            sort_nicely( self.problems[self.cur_source][self.cur_chap]['problems_done'] )

        if len(self.problems[self.cur_source][self.cur_chap]['problems_not_done']) == 0:
            return -3
        else:
            self.cur_prob = self.cur_source + '/' + self.cur_chap + '/' + self.problems[self.cur_source][self.cur_chap]['problems_not_done'][0]

        #unready all users
        for usr in self.joined_usrs.keys():
            self.joined_usrs[usr] = False

        self.duedate = None

        return self.cur_prob

    def listChapters(self):
        if self.cur_source == None:
            return -1

        avail_chapters = []
        for chapter in self.problems[self.cur_source].keys():
            if len(self.problems[self.cur_source][chapter]['problems_not_done']) != 0:
                if len(self.problems[self.cur_source][chapter]['problems_done']) != 0:
                    avail_chapters.append(chapter + '~')
                else:
                    avail_chapters.append(chapter)
            else:
                avail_chapters.append(chapter + ' *completed* ')

        sort_nicely(avail_chapters)

        return (avail_chapters)

    def selectChapter(self, chapt):
        if (self.selectionMode != 'Chapter'):
            return -3

        avail_chapters = []
        chaps = self.problems[self.cur_source].keys()
        for chapter in chaps:
            if len(self.problems[self.cur_source][chapter]['problems_not_done']) != 0:
                avail_chapters.append(chapter)
        
        if avail_chapters == None:
            return None

        if chapt in chaps and chapt not in avail_chapters:
            return -1
        elif chapt not in chaps:
            return -2

        self.cur_chap = chapt
        self.cur_prob = None

        #unready all users
        for usr in self.joined_usrs.keys():
            self.joined_usrs[usr] = False

        return 0

    def dispenseRandom(self):
        avail_chapters = []
        for chapter in self.problems[self.cur_source].keys():
            if len(self.problems[self.cur_source][chapter]['problems_not_done']) != 0:
                avail_chapters.append(chapter)
        
        if avail_chapters == None:
            return None

        #mark previous problem as done
        if self.cur_prob != None:
            self.problems[self.cur_source][self.cur_chap]['problems_done'].append(self.problems[self.cur_source][self.cur_chap]['problems_not_done'][0])
            del self.problems[self.cur_source][self.cur_chap]['problems_not_done'][0]
            sort_nicely( self.problems[self.cur_source][self.cur_chap]['problems_done'] )

        #get list of random chapters that aren't completed
        #pick a random chapter and dispense, reset user's states to unready
        self.cur_chap = random.sample(avail_chapters,1)[0]
        # pick first problem in that chapter
        self.cur_prob = self.cur_source + '/' + self.cur_chap + '/' + self.problems[self.cur_source][self.cur_chap]['problems_not_done'][0]

        self.duedate = None

        #unready all users
        for usr in self.joined_usrs.keys():
            self.joined_usrs[usr] = False

        return self.cur_prob

    def readSources(self, wd):
        my_sources = {}
        for source in get_immediate_subdirectories(wd):
            if not source.startswith('.') and not source.startswith('__'):
                my_sources[source] = {}
                for chapter in get_immediate_subdirectories(source):
                    #init that chapter in yaml
                    my_sources[source][chapter] = {"problems_done" : [], "problems_not_done" : []}
                    #append problems
                    for problem in os.listdir(source + '/' + chapter):
                        my_sources[source][chapter]['problems_not_done'].append(problem)
                    sort_nicely( my_sources[source][chapter]['problems_not_done'] )

        return my_sources

    #What this does: returns a list of sources, and updates the sources's chapters(adds new chapters, adds new problems)
    def listSources(self):  #lists current sources, also looks for new ones
        #check if we haven't seen this source somewhere, so we can avoid overwriting in that scenario(but add the difference)
        mockobj = {}
        #make copy of new sources
        newsources = self.readSources(BASE_WD)

        for src in newsources.keys():
            if src not in self.problems.keys():
                #we can just add it
                self.problems[src] = newsources[src]
            else:
                #we must now compare them in detail
                for chapter in newsources[src].keys():
                    if chapter not in self.problems[src].keys():
                        self.problems[src][chapter] = newsources[src][chapter]
                    else:
                        #check individual problems in chapter
                        newprobs = set(newsources[src][chapter]['problems_not_done'])
                        newprobs = newprobs - set(self.problems[src][chapter]['problems_not_done'])
                        newprobs = newprobs - set(self.problems[src][chapter]['problems_done'])
                        if len(newprobs) != 0:
                            self.problems[src][chapter]['problems_not_done'] += list(newprobs)
                            sort_nicely(self.problems[src][chapter]['problems_not_done'])

        #now that reading of the sources is done, let's return the actual sources
        return list(self.problems.keys())


    def setDueDate(self, chat_id, timeArr):
        if timeArr[0] == "None":
            self.duedate = None

        incr = 0
        secs = { 'd' : 86400, 'h' : 3600, 'm' : 60 }
        try:
            for substr in timeArr:
                substr.strip()
                incr += float(substr[0:-1]) * secs[substr[-1]]
        except:
            return -1

        self.duedate = time.time() + incr

    def getDueDate(self):
        if self.duedate == None:
            return "No due date set!"
        return datetime.datetime.fromtimestamp(self.duedate).strftime('%Y-%m-%d %H:%M:%S')

    #def setDispenseMode(uname):


    def all_ready(self):
        for i in self.joined_usrs.keys():
            if self.joined_usrs[i] is False:
                return False

        return True




#Bot Definition
class ProblemBot(object):
    def __init__(self):
        self.save_file='__chats/ProblemBot'
        if os.path.isfile(self.save_file):
            self.load()
        else:
            self.chats = {}

    def save(self):
        with open(BASE_WD + "/" + self.save_file, "wb") as f:
            pickle.dump(self.chats, f, pickle.HIGHEST_PROTOCOL)

    #load file state to object
    def load(self):
        with open(BASE_WD + "/" + self.save_file, "rb") as f:
            self.chats = pickle.load(f)

#these map to new commands
    def join(self, chat_id, args):
        if self.chats[chat_id].addUser(args[0]):
            bot.sendMessage(chat_id, "User %s Added"   % args[0]['first_name'])
        else:
            bot.sendMessage(chat_id, "User %s already joined" % args[0]['first_name'])
        self.save()


    def leave(self, chat_id, args):
        if self.chats[chat_id].rmUser(args[0]):
            bot.sendMessage(chat_id, "User %s Removed"   % args[0]['first_name'])
        else:
            bot.sendMessage(chat_id, "User %s Not Participating!"   % args[0]['first_name'])
        self.save()

    def ready(self, chat_id, args):
        if not self.chats[chat_id].isUserInPool(args[0]):
            bot.sendMessage(chat_id, "Error : User %s Not /join-ed in Problem Solving"   % args[0]['first_name'])
            return

        state = self.chats[chat_id].flagUser(args[0], True)
        bot.sendMessage(chat_id, "User %s Readied"   % args[0]['first_name'])
        self.save()

    #the name for this command is really up for grabs
    def give_problem(self, chat_id, args):
        if not self.chats[chat_id].isUserInPool(args[0]):
            return
        newProb = self.chats[chat_id].dispense()  #returns filepath
        if newProb is None:
            bot.sendMessage(chat_id, "All problems in %s complete!" % self.chats[chat_id].cur_source)
            return 
        elif newProb == -1:
            bot.sendMessage(chat_id, "Users aren't readied!")
            return 
        elif newProb == -2:
            bot.sendMessage(chat_id, "No sources selected!")
            return 
        
        print(newProb)
        bot.sendPhoto(chat_id, open(BASE_WD + '/' +newProb, 'rb'))
        #unready all users

        self.save()

    def restate_problem(self, chat_id, args):
        if self.chats[chat_id].cur_prob != None:
            bot.sendPhoto(chat_id, open(BASE_WD + '/' +self.chats[chat_id].cur_prob, 'rb'))

    def unready(self, chat_id, args):
        if not self.chats[chat_id].isUserInPool(args[0]):
            bot.sendMessage(chat_id, "Error : User %s Not /join-ed in Problem Solving"   % args[0]['first_name'])
            return
        state = self.chats[chat_id].flagUser(args[0], False)
        bot.sendMessage(chat_id, "User %s Unreadied" % args[0]['first_name'])
        self.save()

    def set_selection_mode(self, chat_id, args):
        mode = args[1]
        res = self.chats[chat_id].setSelectionMode(mode)
        if res==-1:
            bot.sendMessage(chat_id, "Error : %s is not a valid mode" % mode)
        else:
            bot.sendMessage(chat_id, "Selection mode - %s - set" % mode)

    def set_chapter(self, chat_id, args):
        chapter = args[1]
        res = self.chats[chat_id].selectChapter(chapter)
        if res==-1:
            bot.sendMessage(chat_id, "Error : -  %s - already completed" % chapter)
        elif res == -2:
            bot.sendMessage(chat_id, "Error : - %s - is not a chapter!" % chapter)
        elif res == -3:
            bot.sendMessage(chat_id, "Wrong Selection Mode! - current mode : %s" % self.chats[chat_id].selectionMode)
        elif res == 0:
            bot.sendMessage(chat_id, "%s selected!" % chapter)

    def list_chapters(self, chat_id, args):
        res = self.chats[chat_id].listChapters()
        if res == -1:
            bot.sendMessage(chat_id, "No Source Selected!")
        else:
            bot.sendMessage(chat_id, '\n   * ' + '\n * '.join(res))
        

    def select_source(self, chat_id, args):
        if self.chats[chat_id].selectSource(args[1]):
            bot.sendMessage(chat_id, "Source Selected!")
        else:
            bot.sendMessage(chat_id, "No Such Source!")
        self.save()


    def list_sources(self, chat_id, args):
        src_list = self.chats[chat_id].listSources()
        bot.sendMessage(chat_id, 'Sources:\n - ' + '\n - '.join(src_list))
        self.save()


    def set_due_date(self, chat_id, args):
        res = self.chats[chat_id].setDueDate(chat_id, args[1:])
        if ( res == -1 ):
            bot.sendMessage(chat_id, "Due Date Format Incorrect! Use something like: 2d 12h 34m")
        else:
            date_fmtd = self.chats[chat_id].getDueDate()
            bot.sendMessage(chat_id, "Due date set at %s" % date_fmtd)

    def get_due_date(self, chat_id, args):
        duedate = self.chats[chat_id].getDueDate()
        bot.sendMessage(chat_id, duedate)

    #def stats(self, chat_id, args):
        #self.chats[chat_id] = problemmanager()
        #self.save()


    def start(self, chat_id, args):
        self.chats[chat_id] = ProblemManager()
        self.save()

        
    def help(self, chat_id, args):
        helpstr = "A bot for sharpening your problem skills!\nList of Commands:\n/join : joins pool of problem-solving participants. \n/list_sources : show available problem pools\n/select_source : choose a source to draw problems from. \n/give_problem : Dispense a problem from a source. By default this picks the easiest available problem in a random chapter.\n/ready : signals that you have completed the problem and are ready to move on.\n/unready : Unreadies yourself in case you do not want to move on yet.\n/restate_problem : restates current problem\n/leave : leave pool of problem-solving participants."
        bot.sendMessage(chat_id, helpstr)




f = open('config.yml')
cfgstr = f.read()
mykey = yaml.load(cfgstr)['key']
BASE_WD = yaml.load(cfgstr)['WD']
f.close()
PB = ProblemBot()

def handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']
    fromusr = msg['from']  #is a dict of 'first_name' : <users first name>, 'id' : <users id>

    print("got command: {}".format(command))

    split_msg = command.split()
    method    = split_msg[0].split('@')[0][1:]
    args      = split_msg[1:]
    args.insert(0,fromusr)

    try:
        getattr(PB, method)(chat_id, args)
    except:
        bot.sendMessage(chat_id, "Invalid Command")




#initialize the bot as a global that everything relies on
bot = telepot.Bot(mykey)

print("i'm listening yo")
bot.message_loop(handle, run_forever=True)

