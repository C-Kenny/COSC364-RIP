from threading import Timer
import time, struct, socket
from random import randint
import packet

class Route(object):
  MIN_HOPS = 0
  MAX_HOPS = 16 
  
  def __init__(self, address=None, next_address=None, hops=0, afi=2):
    self.address = address            # Destination address
    self.next_address = next_address  # The next address (who we recieved info from)
    self.hops = hops                  # Distance to get to Destination address from Next address
    self.afi = afi                    # AFI
    self.next_cost = 1                     # Cost to get to the next address
    
  def set_next_cost(self, cost):
    self.next_cost = cost
    
  def cost(self):
    return self.hops + self.next_cost
    
  def __repr__(self):
    return "Route(dest:" + str(self.address) + ", next: " + str(self.next_address) + " (" + str(self.cost()) + "))"

  
# A quick test class, could be made into our actual object?
class Router(object):
  # Initialization
  def __init__(self, config):
    #self.timer = None
    self.routes = dict()
    self.config = config
    
    # load configuration
    print(self.config)
    
    self.neighbors = dict()
    outputs = self.config["outputs"]
    for output in outputs:
      port = output[0]
      metric = output[1]
      router_id = output[2]
      last_updated = time.time() # Current time (in seconds)
      self.neighbors[router_id] = [port, metric, last_updated]
    
    self._start_timer()
    
  def get_neighbor_port(self, router_id):
    return self.neighbors[router_id][0] # port
    
  def get_neighbor_metric(self, router_id):
    return self.neighbors[router_id][1] # metric
    
  def get_neighbor_updated(self, router_id):
    return self.neighbors[router_id][2] # last_updated
    
  def set_neighbor_updated(self, router_id):
    self.neighbors[router_id][2] = time.time()
    # Reset metric to known value if updated and metric >= 16
    if (self.get_neighbor_metric(router_id) >= 16):
      outputs = self.config["outputs"]
      for output in outputs:
        if (output[2] == router_id):
          self.neighbors[router_id][1] = output[1]
          break
    
  def incoming_route(self, route):
    cost = self.get_neighbor_metric(route.next_address)
    route.set_next_cost(cost)
    
    print("New route: " + str(route) + "(me -> them costs " + str(cost) + ")")
    
    # Check if we have this route already
    if (route.address in self.routes.keys()):
      # We have that route in the table already
      old_route = self.routes[route.address]
      if route.cost() < old_route.cost() or \
          old_route.next_address == route.next_address:
        # Store new value
        self.routes[route.address] = route
        print("\tRoute is better or more recent than the one stored, updating...")
      else:
        # New value is worse than previous, ignore
        pass
    else:
      # The route is new
      self.routes[route.address] = route
    
  def incoming_update(self, from_id, raw_data):
    # from_id is who sent the update
    self.set_neighbor_updated(from_id)
    # data is the data recieved
    data = packet.ByteArray(raw_data)
    command = data.get_byte()
    version = data.get_byte()
    data.get_word()
    while (not data.is_empty()):
      afi = data.get_word() # AF_INET (2)
      data.get_word()
      address = data.get_dword() # IPv4
      data.get_dword()
      data.get_dword()
      hops = data.get_dword() # 1-15 inclusive, or 16 (infinity)
      
      r = Route(address, from_id, hops, afi)
      self.incoming_route(r)
      
  def request_update(self, to_id):
    data = packet.build_packet(packet.Command.request, [])
    #TODO: Send on clients port with the data
    pass
    
  def request_full_table(self, to_id):
    #TODO: Work out how this works (AF = 0, Metric = 16)
    pass
  
  def _start_timer(self):
    self.timer = Timer(5.0, Router.tick, args=[self])
    self.timer.start()
  
  # Tick!
  def tick(self):
    self._start_timer()
    
    NEIGHBOR_TIMEOUT = 30.0
        
    # Handle updates
    #TODO: Handle updates from sockets
    
    # Check for non-responsive neighbors
    now = time.time()
    for router_id in self.neighbors.keys():
      last = self.get_neighbor_updated(router_id)
      if last + NEIGHBOR_TIMEOUT < now and self.get_neighbor_metric(router_id) < 16:
        print("Router #" + str(router_id) + " has not responded. Setting metric to 16...")
        self.neighbors[router_id][1] = 16
        
    # Request update
    for router_id in self.neighbors.keys():
      if (self.get_neighbor_metric(router_id) >= 16):
        continue
      self.request_update(router_id)
    
#    self._incoming_update_test()


#    def _incoming_update_test(self):
#    from_address = 1
#    to_address = 2
#    entries = []
#    entries.append({"afi": 2, "address": to_address, "metric": randint(1, 16)})
#    data = packet.build_packet(packet.Command.response, entries)
#    self.incoming_update(from_address, data.get_data())