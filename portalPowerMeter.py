"""This script logs power meter information to Exosite One
"""
import time
import xmpp

global connection
global messenger
global writer0
global writer1
global writer2
global readingIndex
global readingBuffer0
global readingBuffer1
global readingBuffer2
#-------------------------------------------------------------------------------
def LogToOne(newReading0, newReading1, newReading2, meterType, nodeName):
#-------------------------------------------------------------------------------
    global connection
    global messenger
    global writer0
    global writer1
    global writer2
    global readingIndex
    global readingBuffer0
    global readingBuffer1
    global readingBuffer2
    
    try: 
      connection
    except:
      readingIndex = 0
      readingBuffer0 = []
      readingBuffer1 = []
      readingBuffer2 = []
      setup_xmpp()
    else:
      readingBuffer0.insert(0,newReading0)
      readingBuffer1.insert(0,newReading1)
      readingBuffer2.insert(0,newReading2)
      del readingBuffer0[15:] #keep the buffer fresh, use 2x the log samples
      del readingBuffer1[15:] #keep the buffer fresh, use 2x the log samples
      del readingBuffer2[15:] #keep the buffer fresh, use 2x the log samples
      
      if readingIndex > 10:
        meanValue0 = round(sum(readingBuffer0) / len(readingBuffer0), 2)
        maxValue0 = round(max(readingBuffer0),2)
        minValue0 = round(min(readingBuffer0),2)
        meanValue1 = round(sum(readingBuffer1) / len(readingBuffer1), 2)
        maxValue1 = round(max(readingBuffer1),2)
        minValue1 = round(min(readingBuffer1),2)
        meanValue2 = round(sum(readingBuffer2) / len(readingBuffer2), 2)
        maxValue2 = round(max(readingBuffer2),2)
        minValue2 = round(min(readingBuffer2),2)
        readingIndex = 0
        
        norm_value0 = maxValue0 - meanValue0
        if meanValue0 - minValue0 > norm_value0:
          norm_value0 = meanValue0 - minValue0
        norm_value1 = maxValue1 - meanValue1
        if meanValue1 - minValue1 > norm_value1:
          norm_value1 = meanValue1 - minValue1
        norm_value2 = maxValue2 - meanValue2
        if meanValue2 - minValue2 > norm_value2:
          norm_value2 = meanValue2 - minValue2
        #using Honeywell CSLS sensor, 17mV/AT
        #using 10bit ADC - 1024 is full scale of 3.3V
        #one ADC position equates to 3.2mV (188mA)
        #assuming measuring wall power @ 120VAC
        #W = VA = norm_value*0.188*120
        powerValue0 = round(norm_value0 * 0.188 * 120, 2)
        powerValue1 = round(norm_value1 * 0.188 * 120, 2)
        powerValue2 = round(norm_value2 * 0.188 * 120, 2)
        messenger.send(writer0.make_msg(powerValue0, connection['exosite_bot']))
        messenger.wait()
        print "Power 0: %d" % (powerValue0)
        messenger.send(writer1.make_msg(powerValue1, connection['exosite_bot']))
        messenger.wait()
        print "Power 1: %d" % (powerValue1)
        messenger.send(writer2.make_msg(powerValue2, connection['exosite_bot']))
        messenger.wait()
        print "Power 2: %d" % (powerValue2)
      else:
        readingIndex += 1
        

#-------------------------------------------------------------------------------
def setup_xmpp():
#-------------------------------------------------------------------------------
    global connection
    global messenger
    global writer0
    global writer1
    global writer2
    
    print "Setting up XMPP connection for Exosite One logging"
    
    connection = {'exosite_bot':'commander@m2.exosite.com','user_id':'exositedemo@xmpp.jp','password':'exositedemo','cik':'c3a2b3f60292de9910e2786a922f0978ae03934d'}
    datasources = { 'power_meter0':'19', 'power_meter1':'20' , 'power_meter2':'21'  }
    
    messenger = connect( connection )
    
    if messenger == -1:
      print "Could not connect!"
    else:
      print "Setting up Data Sources"
      cds = CreateDataSource('power_meter0',datasources['power_meter0'], connection)
      messenger.send(cds.make_msg(), cds.message_handler)
      messenger.wait()
      writer0 = DataWriter(cds.get_resource_id())
      cds = CreateDataSource('power_meter1',datasources['power_meter1'], connection)
      messenger.send(cds.make_msg(), cds.message_handler)
      messenger.wait()
      writer1 = DataWriter(cds.get_resource_id())
      cds = CreateDataSource('power_meter2',datasources['power_meter2'], connection)
      messenger.send(cds.make_msg(), cds.message_handler)
      messenger.wait()
      writer2 = DataWriter(cds.get_resource_id())
      print "Data Source Setup Complete"
    
#-------------------------------------------------------------------------------
def connect ( connection ):
#-------------------------------------------------------------------------------
    print "Trying to connect to Exosite XMPP bot."
    try:
      jid = xmpp.protocol.JID(connection['user_id'])
    except:
      print "Unable to establish XMPP connection!"
      return -1
    
    cl = xmpp.Client(jid.getDomain(), debug="")
    messenger = Messenger(cl)
    con = cl.connect()
    try:
      auth = cl.auth(jid.getNode(), connection['password'])
    except:
      print "Authentication failed!"
      return -1
      
    if not auth:
      print "Authentication failed!"
      return -1
    
    cl.RegisterHandler('message', messenger.message_handler)
    msg = xmpp.protocol.Message(to=connection['exosite_bot'],
                                body='setcik %s\n' % connection['cik'],
                                typ='chat')
    messenger.send(msg)
    if messenger.wait() == -1:
      print "Timed out waiting for response!"
      return -1
    
    return messenger
    
    
#-------------------------------------------------------------------------------
class Messenger(object):
#-------------------------------------------------------------------------------
    def __init__(self, client):
        self.wait_for_response = False
        self.callback = None
        self.client = client

    def wait(self):
        start = time.clock()
        while self.wait_for_response:
            if time.clock() - start > 10: return -1
            if not self.client.Process(1):
                print 'disconnected'
                break

    def message_handler(self, con, event):
        response = event.getBody()
        if self.callback:
            self.callback(response)
        else:
            if response.find("ok") == -1:
              logtext("ERROR: XMPP response: %s" % response)
        self.wait_for_response = False

    def send(self, message, callback=None):
        self.wait_for_response = True
        self.callback = callback
        self.client.send(message)
        
#-------------------------------------------------------------------------------
class CreateDataSource(object):
#-------------------------------------------------------------------------------
    def __init__(self, desc1, desc2, connection):
        self.resource_id = desc2
        body = 'dscreate %s %s na 0' % (desc1, self.resource_id)
        self.msg = xmpp.protocol.Message(connection['exosite_bot'], body, typ='chat')

    def make_msg(self):
        return self.msg

    def message_handler(self, response):
        self.remote_id = response
        if response.find("error") != -1:
          if response.find("duplicate") != -1:
            print "Duplicate DataSource, continuing."
          else:
            print "CreateDataSource Error: response: %s" % response
        else:
          print "CreateDataSource: response: %s" % response

    def get_resource_id(self):
        return self.resource_id

    def get_remote_id(self):
        return self.remote_id

#-------------------------------------------------------------------------------
class DataWriter(object):
#-------------------------------------------------------------------------------
    def __init__(self, resource_id):
        self.resource_id = resource_id

    def make_msg(self, data_value, client):
        body = 'write %s %s' % (self.resource_id, data_value)
        return xmpp.protocol.Message(client, body, typ='chat')

