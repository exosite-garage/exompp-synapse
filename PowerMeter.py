"""
  Power Meter Demo for EK2100 Kit (for use on Proto-Board)
  Requires: Hall effect sensor measuring power
"""
# Use Synapse Evaluation Board definitions
from synapse.evalBase import *

portalAddr = '\x00\x00\x01' # hard-coded address for Portal
NV_DEVICE_NAME_ID = 8       # The decvice name is stored at this location

def startupEvent():
    """This is hooked into the HOOK_STARTUP event"""  
    global secondCounter, buttonPin
    
    secondCounter = 0 # Used by the system for one second count
    
    initProtoHw() # Intialize the proto board
    monitorPin(5,True) # Monitor for button press
    

def doEverySecond():
    """Things to be done every second"""
    blinkLed(200)
    updatePowerSensor()
    

def rpcSentEvent():
    """This is hooked into the HOOK_RPC_SENT event that is called after every RPC"""  
    return
    

def timer100msEvent(currentMs):
    """Hooked into the HOOK_100MS event. Called every 100ms"""
    global secondCounter, lqSum  
    secondCounter += 1
    lqSum += getPercentLq() # get the link Quality every 100ms
    if secondCounter >= 10:
        doEverySecond()
        secondCounter = 0
        lqSum = 0 # reset the link quality sum after updating

def buttonEvent(pinNum, isSet):
    """Action taken when the on-board buttton is pressed (i.e. change meter)"""  
    if isSet:
        doButtonAction()
    

def updatePowerSensor():
    """Send the current power back to Portal for logging"""
    rawPower0 = adcRead(0) # Read Adc on GPIO 18
    rawPower1 = adcRead(1) # Read Adc on GPIO 17
    rawPower2 = adcRead(2) # Read Adc on GPIO 16
    
    # Send the data to the Portal node for logging to One
    rpc(portalAddr,"LogToOne",rawPower0,rawPower1,rawPower2,"Raw Power Reading",loadNvParam(NV_DEVICE_NAME_ID))
    

def adcRead(adc_pin):
    """Read the current power draw from the sensor"""
    # For this simple example we will not calculate the actual power in watts
    return readAdc(adc_pin) # Read Adc
    

def getPercentLq():
    """Calculate the Link Quality as a percentage"""
    maxDbm = 18
    minDbm = 95
    percent = 100 - ((getLq() - maxDbm) * 100) / (minDbm - maxDbm)
    return percent
    

def doButtonAction():
    """Put code here to do something on button press"""
    

# hook up event handlers
snappyGen.setHook(SnapConstants.HOOK_STARTUP, startupEvent)
snappyGen.setHook(SnapConstants.HOOK_100MS, timer100msEvent)
snappyGen.setHook(SnapConstants.HOOK_GPIN, buttonEvent)
snappyGen.setHook(SnapConstants.HOOK_RPC_SENT, rpcSentEvent)

