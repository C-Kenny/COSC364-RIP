from threading import Timer
import time

# A quick test class, could be made into our actual object?
class Router(object):
  # Initialization
  def __init__(self):
    self.timer = None
    self._start_timer()
    
  # Starts a timer that ticks once (after 1.0 seconds) and calls the tick method below
  def _start_timer(self):
    self.timer = Timer(1.0, Router.tick, args=[self])
    self.timer.start()
  
  # Tick!
  def tick(self):
    print("Tick!")
    self._start_timer()
  
# This is just to test, the "tick" message will be
# displayed even though the main thread is blocked
x = Router()
while (True):
  pass