import os
import sys
import requests
try:
    from handle.request_handler import RequestsHandler
except ModuleNotFoundError:
    path = os.path.abspath('.')
    sys.path.insert(1, path)
from handle.request_handler import RequestsHandler
    
class DaimlerCoaches():
    print("Ejecutando DaimlerCoaches!")
    

if __name__ == '__main__':
    DaimlerCoaches()