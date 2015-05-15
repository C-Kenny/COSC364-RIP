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
    
  def set_next_cost(self, cost):
    self.next_cost = cost
    
  def cost(self):
    return self.hops + self.next_cost
    
  def __repr__(self):
    return "Route(dest:" + str(self.address) + ", next: " + str(self.next_address) + " (" + str(self.cost()) + "))"


class Router(object):
  TIMER_TICK = 5.0
  NEIGHBOR_TIMEOUT = 30.0
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
      if route.cost() < old_route.cost() or \
          old_route.next_address == route.next_address:
        # Store new value
        self.routes[route.address] = route
      else:
        # New value is worse than previous, ignore
        pass
    else:
      # The route is new
      self.routes[route.address] = route
    
  def incoming_update(self, raw_data):
    # data is the data recieved
    data = packet.ByteArray(raw_data)
    command = data.get_byte()
    version = data.get_byte()
    from_id = data.get_word()
    
    self.set_neighbor_updated(from_id)
    
    while (not data.is_empty()):
      afi = data.get_word() # AF_INET (2)
      data.get_word()
      address = data.get_dword() # IPv4
      data.get_dword()
      data.get_dword()
      hops = data.get_dword() # 1-15 inclusive, or 16 (infinity)
      
      r = Route(address, from_id, hops, afi)
      self.incoming_route(r)
      
  
  def _start_timer(self):
    delay = Router.TIMER_TICK * random.uniform(0.8, 1.2)
    self.timer = Timer(delay, Router.tick, args=[self])
    self.timer.start()
    
  def print_table(self):
    print("Routing Table:")
    for route_id in self.routes.keys():
      route = self.routes[route_id]
      print("\t", route)
    
  def send_updates(self):
    for neighbor in self.neighbors.keys():
        if (self.get_neighbor_metric(neighbor) < 16):
          self.send_update_to_router(neighbor)
    self.print_table()
    
          
  def send_update_to_router(self, router_id):
    # Sends a specialized update message to a neighbor using split-horizon poisoning
    entries = []
    for route_id in self.routes.keys():
      route = self.routes[route_id]
      new_metric = route.cost()
      if (route.address == router_id):
        # we don't need to send an update for the router itself...
        continue
      elif (route.next_address == router_id):
        # Split-horizon poisoning
        new_metric = 16
        
      entries.append({"afi": 2, "address": route.address, "metric": new_metric})
      
    data = self.build_packet(self.id, entries).get_data()
    port = self.get_neighbor_port(router_id)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(data), ("localhost", port))
  
  # Tick!
  def tick(self):
    self._start_timer()
    
    # Check for non-responsive neighbors
    now = time.time()
    for router_id in self.neighbors.keys():
      last = self.get_neighbor_updated(router_id)
      if last + Router.NEIGHBOR_TIMEOUT < now and self.get_neighbor_metric(router_id) < 16:
        print("Router #" + str(router_id) + " has not responded. Setting metric to 16...")
        self.neighbors[router_id][1] = 16
    
    # Update inaccessible routes with 16
    for route_id in self.routes.keys():
      route = self.routes[route_id]
      if (route.address in self.neighbors and self.get_neighbor_metric(route.address) >= 16 or \
          route.next_address in self.neighbors and self.get_neighbor_metric(route.next_address) >= 16):
        # If it's a neighbor, check to see if our internal metric is 16.
        # If it is, replace our "route" metrics with 16
        route.next_cost = 16
        
    # If it's time, send an update ourselves (this handles a metric of 16 for the above!)
    self.send_updates()

  def build_packet(self, sender_id, entries, command=2, version=2):
    # (Byte) Command 
    # (Byte) Version
    # (Word) Padding 0x0
    # (Void) Entries (20 bytes, 1-25 entries)
    datagram = packet.ByteArray()
    datagram.insert_byte(command)
    datagram.insert_byte(version)
    
    # COSC364 special: Use the sending router-id here
    datagram.insert_word(sender_id)
    
    for i, item in enumerate(entries):
      datagram.insert_word(item["afi"]) # AF_INET (2)
      datagram.insert_word(0)
      datagram.insert_dword(item["address"]) # IPv4
      datagram.insert_dword(0)
      datagram.insert_dword(0)
      datagram.insert_dword(item["metric"]) # 1-15 inclusive, or 16 (infinity)
      
    return datagram