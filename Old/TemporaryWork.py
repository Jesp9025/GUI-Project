import PySimpleGUI as sg # To make a GUI
import subprocess # To run shell commands
import MusicPlayer # To play music
import threading # To run threads
import whois # The name explains it
from queue import Queue # To make a queue system for threads for port scanner
import socket # Library used to check if port is open
import time # To start a timer for port scanner
from decimal import Decimal #To round numbers
import itertools #For loading animation


#####################################################################
#                           Functions
#####################################################################
#Clears the window
def clearWindow():
    window["_INFO_"].update("")
    


############# Run CMD ##############
#Uses subprocess, which includes stdout, stderr. Using communicate() allows you to get output and error from the subprocess.Popen
def runcmd(cmd, ipreq): # cmd argument is used to determine which command to run. ipreq is used to determine if input from _IP_ is needed or can be ignored. ipreq has to be 1 or 0
    global done
    clearWindow()
    if ipreq == 1:
        temp = cmd + " " + values["_IP_"]
    elif ipreq == 0:
        temp = cmd
    chars = "-"
    #Checks if the input contains '-'
    #https://stackoverflow.com/questions/5188792/how-to-check-a-string-for-specific-characters
    if any((c in chars) for c in temp):
        print("Not gonna happen..")
    else:
        #Runs the command, and outputs it in readable format
        done = False
        result = subprocess.Popen(temp, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        done = True
        if out:
            clearWindow()
            print(out.decode("utf-8"))
            
        if err:
            clearWindow()
            print("Unknown command")
            

#Function to show ipconfig for Windows and Linux
def ipconfigFunc():
    if values["_WINDOWS_"]:
        threading.Thread(target=runcmd, args=("ipconfig", 0), daemon=True).start()
    elif values["_LINUX_"]:
        threading.Thread(target=runcmd, args=("ifconfig", 0), daemon=True).start()

#Function to start a ping. Takes input _IP_ to determine address
def pingFunc():
    threading.Thread(target=runcmd, args=("ping", 1), daemon=True).start()

#Function to start a trace route. Takes input _IP_ to determine address
def traceFunc():
    if values["_WINDOWS_"]:
        threading.Thread(target=runcmd, args=("tracert", 1), daemon=True).start()
    elif values["_LINUX_"]:
        threading.Thread(target=runcmd, args=("traceroute", 1), daemon=True).start()

#To run a custom command
def customcmd():
    #Checks if input is empty, to avoid error
    if values["_IP_"] != "":
        threading.Thread(target=runcmd, args=(values["_IP_"], 0), daemon=True).start()
    else:
        clearWindow()
        print("Please enter a command first")

#Function to flush DNS
def flushDNS():
    if values["_WINDOWS_"]:
        threading.Thread(target=runcmd, args=("ipconfig /flushdns", 0), daemon=True).start()
    elif values["_LINUX_"]:
        threading.Thread(target=runcmd, args=("service nscd restart", 0), daemon=True).start()

#Function to shut down PC
def shutdownPC():
    if values["_WINDOWS_"]:
        subprocess.Popen('shutdown -p -f')
    elif values["_LINUX_"]:
        subprocess.Popen('shutdown -h now')

#Help with a timer that doesn't freeze the program
#https://stackoverflow.com/a/44666336
#This will create a new thread that runs a timer, and then runs the function, without freezing the program
def fun():
    MusicPlayer.setCountdown()
    threading.Timer(17, shutdownPC).start()

############# Whois ##############
#https://github.com/richardpenman/pywhois
#https://www.pythonforbeginners.com/dns/using-pywhois
#Uses module 'python-whois'
def runWhois():
    global done
    
    # If input is not empty, do stuff
    if values["_whoisInput_"] != "":
        clearWindow()
        done = False
        w = whois.whois(values["_whoisInput_"])
        done = True
        clearWindow()
        print(w)
    else:
        clearWindow()
        print("Please enter a target")
#It may or may not say there is an error and whois is not callable.. Ignore it.

############# Port Scanner ##############
#https://pythonprogramming.net/python-threaded-port-scanner/?completed=/python-port-scanner-sockets/
#Added s.settimeout() to make it faster, instead of using default timeout

#The function that does the actual port scan
def portscan(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        con = s.connect((values["_PORTINPUT_"], port))
        with print_lock:
            print('port', port)
        con.close()
    except:
        pass

_FINISH = False
# The threader thread pulls a worker from the queue and processes it
def threader():
    global _FINISH
    while True:
        if _FINISH and q.empty():
            break
        # gets a worker from the queue
        worker = q.get()

        # Run the example job with the available worker in queue (thread)
        portscan(worker)

        # completed with the job
        q.task_done()


def startPortScan():
    clearWindow()
    global q
    global print_lock
    global _FINISH

    # print_lock makes sure that once a thread has started "working" on a task/variable, other threads can not use it
    print_lock = threading.Lock()

    # Create the queue
    q = Queue()

    # how many threads are we going to allow for
    # Checks if target input is empty
    if values["_PORTINPUT_"] != "":
        try:
            # Checks if inputs are lower than or equal to 0
            if int(values["_STARTPORT_"]) <= 0 or int(values["_ENDPORT_"]) <= 0:
                print("Start and end port must be higher than 0")
            else:
                # Checks if endport is higher than startport
                if int(values["_ENDPORT_"]) >= int(values["_STARTPORT_"]) and int(values["_ENDPORT_"]) <= 65535:

                    # Used to determine how many threads to create
                    temp = int(values["_ENDPORT_"]) - int(values["_STARTPORT_"]) + 1

                    # If temp is lower than 800, it should only create the needed amount of threads
                    if temp < 800:
                        for x in range(temp):
                            z = threading.Thread(target=threader, daemon=True)
                            z.start()
                    else:
                        # 800 is almost the max amount of threads possible to run at same time
                        for x in range(800):
                            z = threading.Thread(target=threader, daemon=True)
                            z.start()

                    #Start time
                    start = time.time()

                    # Number of ports to scan
                    for worker in range(int(values["_STARTPORT_"]), int(values["_ENDPORT_"]) +1):
                        q.put(worker)

                    _FINISH = True
                    # wait until the thread terminates.
                    q.join()

                    #End time
                    end = time.time()

                    print("Scan completed in", round(end - start, 2), "seconds\nNumber of ports scanned:", temp)

                    # Remember to set _FINISH to False
                    _FINISH = False
                else:
                    print("Can't go higher than 65535,\nand end port must be higher than start port")
        # Returns a printed error if non-int has been input
        except ValueError:
            print("Incorrect input. You either didn't type port numbers, or you wrote a non-Int")
    else:
            print("Please enter a target")

############# Loading Animation ##############
#Very basic. We might find something better
#https://stackoverflow.com/a/22029635
def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        window["_INFO_"].update('\rloading ' + c)
        time.sleep(0.1)

#To start and stop loading animation. True = Not loading, False = Loading
done = True


#####################################################################
#                           GUI Code
#####################################################################

#Sets the theme
sg.change_look_and_feel('Reddit')

#Creates the layouts for each tab
#MusicPlayer tab. Uses PyGame to play sounds, control volume etc.
tab1_layout =  [[sg.Text("")],
                [sg.Text("Some music to enjoy while troubleshooting")], 
                [sg.Button(button_text="Play Music"),
                    sg.Button(button_text="Stop Music")],
                [sg.Button(button_text="+", size=(1,1)), 
                    sg.Button(button_text="-", size=(1,1))],
                [sg.Text("Choose a song:"), sg.Combo(["Push It To The Limit",
                "John Denver - Take Me Home, Country Roads",
                "John Denver - Leaving On A Jetplane",
                "Eye Of The Tiger"],
                default_value="Push It To The Limit", key="_SONG_")]]

#Basic tools tab
tab2_layout = [[sg.Frame(layout=[
    [sg.Radio('Windows', "RADIO1", default=True, key="_WINDOWS_"), #key will make it possible to do events and use value of the button, depending on if its pressed or not(True, False)
        sg.Radio('Linux', "RADIO1", key="_LINUX_")]],
            title='Operating System',
            title_color='black',
            relief=sg.RELIEF_SUNKEN)],
    [sg.Button(button_text="IP Config")],
    [sg.Text('Enter IP Address or custom command')],
    [sg.InputText(key="_IP_", size=(20,1))],
    [sg.Button(button_text="Ping")],
    [sg.Button(button_text="Trace Route")],
    [sg.Button(button_text="Flush DNS")],
    [sg.Text("")],
    [sg.Button("Custom Command")]]

#Whois tab
tab3_layout = [[sg.Text("Here you can run a whois on a URL")],
                [sg.T('Target:'), sg.InputText(key="_whoisInput_")],
                [sg.Button("Run Whois")]]

#Port scanner tab
tab4_layout = [[sg.Text("Here you can scan a range of ports")],
    [sg.Text("Target:"), sg.Input(key="_PORTINPUT_")],
    [sg.Button("Run PortScan"), sg.Text("Hackthissite.org is legal to scan")],
    [sg.Frame(layout=[
    [sg.Text("Start Port:"), sg.Input(key="_STARTPORT_", size=(10,1))],
    [sg.Text("End Port: "), sg.Input(key="_ENDPORT_", size=(10,1))]],
            title='Scan Size',
            title_color='black',
            relief=sg.RELIEF_SUNKEN)],
    [sg.Text("Scanning 65535 ports takes 40-60 seconds.")]]

#Wifi-Analyzer tab
tab5_layout = [[sg.T('This is inside tab 5 / Wi-Fi Analyzer')]]

#IP Calculator tab
tab6_layout = [[sg.T('This is inside tab 6 / IP (VLSM) Calculator')]]

#Cisco IOS tab
tab7_layout = [[sg.T('This is inside tab 7 / Cisco IOS')]]

tab8_layout = [[sg.T('This is inside tab 8')]]

#This is where all layots/tabs are put together, to be used in window
layout = [[sg.TabGroup([[sg.Tab('Music Player', tab1_layout), sg.Tab('Basics', tab2_layout),
            sg.Tab('Whois', tab3_layout), sg.Tab('Port Scanner', tab4_layout), sg.Tab('Wi-Fi Analyzer', tab5_layout),
            sg.Tab('IP (VLSM) Calculator', tab6_layout),sg.Tab('Cisco IOS', tab7_layout), sg.Tab('Tab 8', tab8_layout)]]),
            sg.Output(size=(46, 18), key="_INFO_")]]

#Creates the window
window = sg.Window('Network Tool', layout, default_element_size=(12,1))    


#Runs the window in a loop
while True:    
    event, values = window.read()   
    if event is None:           # always,  always give a way out!    
        break
    if event == "Play Music":
        if values["_SONG_"] == "Push It To The Limit":
            MusicPlayer.setSong()
        elif values["_SONG_"] == "John Denver - Take Me Home, Country Roads":
            MusicPlayer.setSong1()
        elif values["_SONG_"] == "John Denver - Leaving On A Jetplane":
            MusicPlayer.setSong2()
        elif values["_SONG_"] == "Eye Of The Tiger":
            MusicPlayer.setSong3()
    elif event == "Stop Music":
        MusicPlayer.stopMusic()
    elif event == "+":
        MusicPlayer.volumeUP()
    elif event == "-":
        MusicPlayer.volumeDOWN()
    elif event == "IP Config": #This will do stuff if button named "IP Config" button is pressed
        ipconfigFunc()
        threading.Timer(0.5, animate).start() #Using a timed thread in order to allow some time for other functions to set 'done' to False
    elif event == "Ping":
        pingFunc()
        threading.Timer(0.5, animate).start()
    elif event == "Trace Route":
        traceFunc()
        threading.Timer(0.5, animate).start()
    elif event == "Custom Command":
        customcmd()
        threading.Timer(0.5, animate).start()
    elif event == "Flush DNS":
        flushDNS()
        threading.Timer(0.5, animate).start()
    elif event =="Run Whois":
        threading.Thread(target=runWhois, daemon=True).start()
        threading.Timer(0.5, animate).start()
    elif event =="Run PortScan":
        threading.Thread(target=startPortScan, daemon=True).start()