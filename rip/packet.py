from enum import Enum

class Command(Enum):
  request = 1
  response = 2

class ByteArray(object):
  def __init__(self, data=None):
    if (data is None):
      self.data = []
    else:
      self.data = data
    self.pointer = 0
    
  def is_empty(self):
    return (len(self.data) - self.pointer) <= 0
    
  def __str__(self):
    return "".join(format(x, '02x') for x in self.data)
    
  def set_pointer(self, pointer):
    self.pointer = pointer
    
  def get_pointer(self):
    return self.pointer
    
  def set_data(self, data):
    self.data = data
  
  def get_data(self):
    return self.data
    
  def insert_byte(self, byte):
    assert byte >= 0 and byte < 256
    bytes = byte.to_bytes(1, byteorder='big')
    self.data.extend(bytes)
  
  def insert_word(self, word):
    assert word >= 0 and word < 65536
    bytes = word.to_bytes(2, byteorder='big')
    self.data.extend(bytes)
  
  def insert_dword(self, dword):
    assert dword >= 0 and dword < 4294967296
    bytes = dword.to_bytes(4, byteorder='big')
    self.data.extend(bytes)
  
  def peek_byte(self, offset=0):
    byte = self.data[self.pointer + offset]
    bytes = [byte]
    return int.from_bytes(bytes, byteorder='big')
  
  def peek_word(self, offset=0):
    index = self.pointer + offset
    bytes = self.data[index:index + 2]
    return int.from_bytes(bytes, byteorder='big')
  
  def peek_dword(self, offset=0):
    index = self.pointer + offset
    bytes = self.data[index:index + 4]
    return int.from_bytes(bytes, byteorder='big')
  
  def get_byte(self):
    byte = self.peek_byte()
    self.pointer += 1
    return byte
  
  def get_word(self):
    word = self.peek_word()
    self.pointer += 2
    return word
  
  def get_dword(self):
    dword = self.peek_dword()
    self.pointer += 4
    return dword

def build_packet(command, entries, version=2):
  # (Byte) Command 
  # (Byte) Version
  # (Word) Padding 0x0
  # (Void) Entries (20 bytes, 1-25 entries)
  packet = ByteArray()
  packet.insert_byte(command.value)
  packet.insert_byte(version)
  packet.insert_word(0)
  
  for i, item in enumerate(entries):
    packet.insert_word(item["afi"]) # AF_INET (2)
    packet.insert_word(0)
    packet.insert_dword(item["address"]) # IPv4
    packet.insert_dword(0)
    packet.insert_dword(0)
    packet.insert_dword(item["metric"]) # 1-15 inclusive, or 16 (infinity)
    
  return packet
