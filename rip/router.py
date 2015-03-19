from threading import Timer
import time, ipaddress, struct, socket

import packet

class Route(object):
  MIN_HOPS = 0
  MAX_HOPS = 16
  
  @staticmethod
  def int2ip(addr):                                                               
    return socket.inet_ntoa(struct.pack("!I", addr))
  
  @staticmethod
  def ip2int(addr):                                                               
    return struct.unpack("!I", socket.inet_aton(addr))[0]   
  
  @staticmethod
  def from_packet(address, mask, p):
    data = packet.ByteArray(p)
    command = data.get_byte()
    version = data.get_byte()
    data.get_word()
    afi = data.get_word()
    data.get_word()
    next_address = ipaddress.IPv4Address(data.get_dword())
    data.get_dword()
    data.get_dword()
    hops = data.get_dword()
    r = Route(address=address, mask=mask, next_address=next_address, hops=hops, afi=afi)
    return r
  
  def __init__(self, address=None, mask=None, next_address=None, hops=0, afi=2):
    self.address = address
    self.mask = mask
    self.next_address = next_address
    self.hops = hops
    self.afi = afi
    #self.final_address = ipaddress.ip_address(address + "/" + str(mask))
    
  def __repr__(self):
    return "Route(" + str(self.address) + "/" + str(self.mask) + " -> " + str(self.next_address) + " (" + str(self.hops) + "))"
  
  def build_request(self):
    entries = []
    entries.append({"afi": self.afi, "address": Route.ip2int(self.next_address), "metric": self.hops})
    return packet.build_packet(packet.Command.request, entries)

  
# A quick test class, could be made into our actual object?
class Router(object):
  # Initialization
  def __init__(self):
    #self.timer = None
    self.tick()
    
  # Starts a timer that ticks once (after 1.0 seconds) and calls the tick method below
#  def _start_timer(self):
#    self.timer = Timer(1.0, Router.tick, args=[self])
#    self.timer.start()
  
  # Tick!
  def tick(self):
    r = Route("0.0.0.0", 0, "0.0.0.0", Route.MAX_HOPS)
    self.send_update(r)
    #self._start_timer()
    
  def send_update(self, r):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((r.address, 520)) # a random port for now
    p = r.build_request()
    print(p)


def main():
    # This is just to test, the "tick" message will be
    # displayed even though the main thread is blocked
    print("Starting!")
    x = Router()
    

if __name__ == "__main__":
    main()