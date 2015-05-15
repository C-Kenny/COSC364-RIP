from threading import Timer, Thread
import time, struct, socket, random
import socketserver
import packet

class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        self.server.router.incoming_update(data)

class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

class Route(object):
  MIN_HOPS = 0
  MAX_HOPS = 16 
  
  def __init__(self, address=None, next_address=None, hops=0, afi=2):
    self.address = address            # Destination address
    self.next_address = next_address  # The next address (usually who we recieved info from)
    self.hops = hops                  # Distance to get to Destination address from Next address
    self.afi = afi                    # AFI
    self.next_cost = 1                # Cost to get to the next address
    self.marked = False
    self.marked_time = 0
    
  def mark(self):
    self.marked = True
    self.marked_time = time.time()
    
  def set_next_cost(self, cost):
    self.next_cost = cost
    
  def cost(self):
    c = self.hops + self.next_cost
    if (c > 16): c = 16
    return c
    
  def __repr__(self):
    marked_token = ""
    if (self.marked):
      marked_token = " [MARKED FOR DELETION at " + time.strftime("%X", time.localtime(self.marked_time)) + "]"
    return "Route(dest:" + str(self.address) + ", next: " + str(self.next_address) + " (cost: " + str(self.cost()) + "))" + marked_token

def if_failed(condition, message):
  if (not bool(condition)):
    print("[WARNING] Check Failed: " + str(message))
    return True
  return False

class Router(object):
  TIMER_TICK = 5.0
  NEIGHBOR_TIMEOUT = 30.0
  DELETION_TIMEOUT = 7.5
  # Initialization
  def __init__(self, config):
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
      
    for port in self.config["input-ports"]:
      server = ThreadedUDPServer(("localhost", port), ThreadedUDPRequestHandler)
      server.router = self
      server_thread = Thread(target=server.serve_forever)
      server_thread.daemon = True
      server_thread.start()
      print("Listening on port " + str(port) + " for datagrams...")
    
    # Load entry for self
    router_id = self.config["router-id"]
    self.router_id = self.config["router-id"]
    route = Route(router_id, router_id, 0)
    route.next_cost = 0
    self.id = router_id
    self.routes[router_id] = route
    
    # That's all, now we start!
    self.print_table()
    
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
    
    # Check if we have this route already
    if (route.address in self.routes.keys()):
      # We have that route in the table already
      old_route = self.routes[route.address]
      
      if old_route.next_address == route.next_address:
        # Sanity check, if it's marked we already know it's unreachable
        if (route.cost() != old_route.cost()):
          self.routes[route.address] = route
      elif route.cost() < old_route.cost():
        # Store new value
        self.routes[route.address] = route
      else:
        return
    elif route.cost() < 16:
      # The route is new, and under 16
      self.routes[route.address] = route
    else:
      # The route is new but is marked for deletion.
      # Seems odd, our neighbors should get this anyway and if not then they won't have this route
      # anyway, since we don't have it either
      return
    if route.cost() >= 16 and not route.marked and \
         route.next_address != self.id and route.address != self.id:
        route.mark()
        # Force an update of all routers
        self.update()
    
  def incoming_update(self, raw_data):
    # data is the data recieved
    data = packet.ByteArray(raw_data)
    if if_failed(data.size() >= 4, "Recieved invalid packet of length " + str(data.size())):
      return
      
    command = data.get_byte()
    if if_failed(command == 2, "Recieved RIPv2 request (expected only responses)"):
      return
    version = data.get_byte()
    if if_failed(version == 2, "Recieved RIPv1 or other message (expected RIPv2)"):
      return
    from_id = data.get_word()
    
    if if_failed(from_id in self.neighbors, "Recieved update from non-neighbor router"):
      return
    
    self.set_neighbor_updated(from_id)
    
    while (not data.is_empty()):
      afi = data.get_word()       # AF_INET (2)
      if if_failed(afi == 2, "Recieved unknown AF_INET (expected 2)"):
        return
      data.get_word()             # (BLANK) should we check for this being 0? Probably not important.
      address = data.get_dword()  # Router-ID
      data.get_dword()            # (BLANK)
      data.get_dword()            # (BLANK)
      hops = data.get_dword()     # 1-15 inclusive, or 16 (infinity)
      if if_failed(0 <= hops <= 16, "Recieved invalid hop count (setting to 16)"):
        hops = 16
      
      r = Route(address, from_id, hops, afi)
      self.incoming_route(r)
      
  
  def _start_timer(self):
    delay = Router.TIMER_TICK * random.uniform(0.8, 1.2)
    self.timer = Timer(delay, Router.tick, args=[self])
    self.timer.start()
    
  def print_table(self):
    now = time.strftime("%X")
    print("[{}] Routing Table for {}".format(str(now), self.router_id))
    for route_id in self.routes.keys():
      route = self.routes[route_id]
      print("\t\t", route)
    
  def send_updates(self):
    for neighbor in self.neighbors.keys():
        if (self.get_neighbor_metric(neighbor) < 16):
          self.send_update_to_router(neighbor)
    
          
  def send_update_to_router(self, router_id):
    # Sends a specialized update message to a neighbor using split-horizon poisoning
    # Skip sending updates to self
    if (router_id == self.id):
      return
    entries = []
    for route_id in self.routes.keys():
      route = self.routes[route_id]
      new_metric = route.cost()
      if (route.address == router_id or route.next_address == router_id):
        # Split-horizon poisoning
        new_metric = 16
        
        # Skip marked messages from contacting the router who sent us the deletion message
        if (route.marked): continue
        
      entries.append({"afi": 2, "address": route.address, "metric": new_metric})
      
    data = self.build_packet(self.id, entries).get_data()
    port = self.get_neighbor_port(router_id)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(data), ("localhost", port))
  
  def update(self):
    # Check for non-responsive neighbors
    now = time.time()
    for router_id in self.neighbors.keys():
      last = self.get_neighbor_updated(router_id)
      if last + Router.NEIGHBOR_TIMEOUT < now and self.get_neighbor_metric(router_id) < 16:
        print("Router #" + str(router_id) + " has not responded. Setting metric to 16...")
        self.neighbors[router_id][1] = 16
        
    # Check for marked routes ready for deletion
    # Update inaccessible routes with 16
    for route_id in self.routes.keys():
      route = self.routes[route_id]
      if (route.address in self.neighbors and self.get_neighbor_metric(route.address) >= 16 or \
          route.next_address in self.neighbors and self.get_neighbor_metric(route.next_address) >= 16):
        # If it's a neighbor, check to see if our internal metric is 16.
        # If it is, replace our "route" metrics with 16
        route.next_cost = 16
        # Mark for deletion in a little bit...
        if (not route.marked): 
          print("Marking route to " + str(route.address) + " for deletion (neighbor metric is 16)")
          route.mark()
        
      if (route.marked and route.marked_time + Router.DELETION_TIMEOUT < now):
        print("Deleting marked route " + str(route) + " as inaccessible")
        self.routes[route_id] = None
      
    self.routes = { k : v for k,v in self.routes.items() if v is not None }
        
    # If it's time, send an update ourselves (this handles a metric of 16 for the above!)
    self.send_updates()
    self.print_table()
  
  # Tick!
  def tick(self):
    self._start_timer()
    
    self.update()

  def build_packet(self, sender_id, entries, command=2, version=2):
    # (Byte) Command 
    # (Byte) Version
    # (Word) Padding 0x0 (or Sender-ID in COSC364's case)
    # (Void) Entries (20 bytes each, 1-25 entries)
    datagram = packet.ByteArray()
    datagram.insert_byte(command)
    datagram.insert_byte(version)
    
    # COSC364 special: Use the sending router-id here
    datagram.insert_word(sender_id)
    
    # Should we try and limit entries to 25?
    if if_failed(len(entries) <= 25, "Recieved invalid entries count (larger than 25)"):
      return datagram
    
    for i, item in enumerate(entries):
      datagram.insert_word(item["afi"]) # AF_INET (2)
      datagram.insert_word(0)
      datagram.insert_dword(item["address"]) # IPv4
      datagram.insert_dword(0)
      datagram.insert_dword(0)
      datagram.insert_dword(item["metric"]) # 1-15 inclusive, or 16 (infinity)
      
    return datagram
