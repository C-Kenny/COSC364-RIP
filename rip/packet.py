from enum import Enum

class Command(Enum):
  request = 1
  response = 2

class ByteArray(object):
  def __init__(self):
    self.data = []
    self.pointer = 0
    
  def set_pointer(self, pointer):
    self.pointer = pointer
    
  def pointer(self):
    return self.pointer
    
  def set_data(self, data):
    self.data = data
  
  def data(self):
    return self.data
    
  def insert_byte(self, byte):
    bytes = byte.to_byte(1, byteorder='big')
    self.data.append(bytes)
  
  def insert_word(self, word):
    bytes = word.to_byte(2, byteorder='big')
    self.data.append(bytes)
  
  def insert_dword(self, dword):
    bytes = dword.to_byte(4, byteorder='big')
    self.data.append(bytes)
  
  def peek_byte():
    bytes = self.data[self.pointer]
    return int.from_bytes(bytes, byteorder='big')
  
  def peek_word():
    bytes = self.data[self.pointer:self.pointer+1]
    return int.from_bytes(bytes, byteorder='big')
  
  def peek_dword():
    bytes = self.data[self.pointer:self.pointer+3]
    return int.from_bytes(bytes, byteorder='big')
  
  def get_byte():
    byte = self.peek_byte()
    self.pointer += 1
    return byte
  
  def get_word():
    word = self.peek_word()
    self.pointer += 2
    return word
  
  def get_dword():
    dword = self.peek_dword()
    self.pointer += 4
    return dword

def build_packet(command, entries, version=2):
  // (Byte) Command 
  // (Byte) Version
  // (Word) Padding 0x0
  // (Void) Entries (20 bytes, 1-25 entries)
  packet = ByteArray()
  packet.insert_byte(command)
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