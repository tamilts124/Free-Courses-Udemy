import ast, sys
from pynput import mouse, keyboard
from time import sleep
from threading import Thread

executeFile =sys.argv[1]
totalRun =sys.argv[2]
delayPerRun =sys.argv[3]

PressAndClickKeys =[]
MovedPositions =[]
Delays =[]
timeLoop =True
sleepTime =0.05
nowSecond =0
timerSecond =0
totalOperationRunningTimes =1
delayPerOperation =0
fileTypes =[(".rd","*.rd")]

defaultColor ='purple'
defaultLightColor ='lightgreen'
operation =None
cancel =False
executionStop =False

Keyboard =keyboard.Controller()
Mouse =mouse.Controller()
KeyboardListener =None
MouseListener =None
Key =keyboard.Key
Click =mouse.Button

def StringToHexString(data):
    return str(data).encode().hex()

def HexStringToString(data):
    return bytes.fromhex(data).decode()

def ByteStringToHex(data):
    return ''.join( [ "%02X " % ord( x ) for x in data ] ).strip()

def HexStringToByte(data):
    bytes = []
    data = ''.join( data.split(" ") )
    for i in range(0, len(data), 2):
        bytes.append( chr( int (data[i:i+2], 16 ) ) )
    return ''.join( bytes )

def StringtoList(data):
    return ast.literal_eval(data)

def openFile(file, mode):
    file = open(file, mode)
    data =file.read()
    file.close()
    return data

def KeyToKeyCode(key, pOr):
    try:
        key_code = key.vk
    except AttributeError:
        key_code = key.value.vk
    if pOr =='release':
        key_code+=300
    return key_code

def KeyCodetoKey(keycode, pOr):
    keycode =int(keycode)
    if pOr =='release':
        return keyboard.KeyCode(keycode-300)
    else:
        return keyboard.KeyCode(keycode)

def ClickToClickCode(click, pOr):
    if(Click.left==click and pOr=='press'):
        return 1000
    elif(Click.right==click and pOr=='press'):
        return 1001
    elif(Click.left==click and pOr=='release'):
        return 1002
    elif(Click.right==click and pOr=='release'):
        return 1003

def ClickCodeToClick(clickcode):
    clickcode =int(clickcode)
    if(clickcode==1000):
        return Click.left
    elif(clickcode==1001):
        return Click.right
    elif(clickcode==1002):
        return Click.left
    elif(clickcode==1003):
        return Click.right

def on_close():
    global timeLoop
    timeLoop =False
    Thread(target=KeyboardListener.stop).start()
    Thread(target=MouseListener.stop).start()

def pressKey(keycode):
    if int(keycode)<300:
        key =KeyCodetoKey(keycode, 'press')
        if not key==Key.cmd:
            Keyboard.press(key)
    else:
        key =KeyCodetoKey(keycode, 'release')
        if not key==Key.cmd:
            Keyboard.release(key)
    
def clickMouse(clickcode):
    if (int(clickcode) in [1000,1001]):
        click =ClickCodeToClick(clickcode)
        Mouse.press(click)
    else:
        click =ClickCodeToClick(clickcode)
        Mouse.release(click)

def moveMouse(positionX, positionY):
    Mouse.position =(positionX, positionY)

def TimeLoad():
    global nowSecond
    while timeLoop:
        sleep(sleepTime)
        nowSecond+=sleepTime

def stopExecution(key):
    global executionStop
    if key==Key.cmd:
        executionStop =True
        Thread(target=KeyboardListener.stop).start()

def KeyboardListen(on_pressed, on_released):
    global KeyboardListener
    with keyboard.Listener(on_press=on_pressed, on_release=on_released) as KeyboardListener:
        KeyboardListener.join()

def MouseListen(on_clicked, on_moved):
    global MouseListener
    with mouse.Listener(on_click=on_clicked, on_move=on_moved) as MouseListener:
        MouseListener.join()

def ExecuteOperation(totalOperationRunningTimes, delayPerOperation, PressAndClickKeys, MovedPositions, Delays):
    temp =0
    Thread(target=KeyboardListen, args=[stopExecution, stopExecution]).start()
    try:
        while(totalOperationRunningTimes>0):
            old_delay =0
            while(temp<len(PressAndClickKeys) and not executionStop):
                try:
                    delay =Delays[temp] - old_delay
                    if(delay<0):
                        delay =0
                    sleep(delay)
                    old_delay =Delays[temp]
                except Exception:pass
                x =MovedPositions[temp][0]
                y =MovedPositions[temp][1]
                moveMouse(x,y)
                if PressAndClickKeys[temp]:
                    if not (PressAndClickKeys[temp] in [1000, 1001, 1002, 1003]):
                        pressKey(PressAndClickKeys[temp])
                    else:
                        clickMouse(PressAndClickKeys[temp])
                temp +=1           
            temp =0
            totalOperationRunningTimes -=1
            sleep(delayPerOperation)
        if not executionStop:
            Thread(target=KeyboardListener.stop).start()
    except Exception:
        if not executionStop:
            Thread(target=KeyboardListener.stop).start()

def check_Executable(totalruns, perrunsdelay, executeFile):
    if totalruns and perrunsdelay:
        totalruns =int(totalruns)
        perrunsdelay =int(perrunsdelay)
        file =open(executeFile, 'r')
        values =HexStringToString(file.read())
        Datas =StringtoList(values)
        PressAndClickKeys =Datas[0]
        MovedPositions =Datas[1]
        Delays =Datas[2]
        ExecuteOperation(totalruns, perrunsdelay, PressAndClickKeys, MovedPositions, Delays)

if __name__=='__main__':
    check_Executable(totalRun, delayPerRun, executeFile)
