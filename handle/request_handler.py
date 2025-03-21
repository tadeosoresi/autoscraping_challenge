import traceback
import requests
import time
import ssl
from requests import Response
from datetime import datetime
from json.decoder import JSONDecodeError
from bs4 import BeautifulSoup
from requests.exceptions import ChunkedEncodingError
from typing import Optional, Generator, Iterable, Union, Tuple, Iterator, Any, List, Dict

class RequestsHandler():
    """
    Clase para realizar requests, sirve para scrapings via API publica o Soup.
    SIN USO.
    """
    def close(self):
        try:
            self.__session.close()
        except:
            pass
        
    def create_new_session(self, disable_warnings=False, ssl_error=False):
        if disable_warnings:
            requests.packages.urllib3.disable_warnings()
        try:
            self.__session.close()
        except:
            pass
        
        self.__session = requests.Session()
        
    def get_response(
        self, url: str, 
        params: Optional[dict]=None, data: Union[None, str, dict]=None, 
        json_: Optional[dict]=None, sleep: int=5,
        headers: Optional[dict]=None, timeout: int=15, 
        attempts: int=5, verify: bool=True, 
        method: str='GET', **kwargs
    ) -> Optional[Response]:
        """
        Metodo para realizar requests
        """
        response = None
        retries = 0
        # Realizamos una cantidad de intentos acorde
        while retries < 5:
            try:
                response = self.__session.request(
                    method, url, params, data, headers,
                    timeout=timeout, verify=verify, 
                    json=json_, **kwargs
                )
                time.sleep(sleep)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.HTTPError,
                    ssl.SSLError, ChunkedEncodingError, requests.exceptions.URLRequired) as e:
                print(f"Request Exception in request, type:\n {e}, retrying...")
                time.sleep(5)
                retries += 1
                continue
            except Exception as e:
                raise
            
            print(f'[ {datetime.now()} ]\x1b[1;34;40m[ {method} {response.status_code} ]\x1b[0m {url}')
            # Si el status es 200, ejectuamos las verificaciones necesarias p/return
            if response.ok:
                if response.content:
                    return response
            time.sleep(sleep * 10)
        return response

    def get_soup(
        self, url: str, params: Optional[dict]=None,
        data: Union[None, str, dict]=None, json: Optional[dict]=None, sleep: int=0,
        headers: Optional[dict]=None, timeout: int=15,
        attempts: int=5, verify: bool=True, method: str='GET', **kwargs
    ) -> Optional[BeautifulSoup]:
        """
        Método para obtener el soup de una página mediante request.
        """
        response = self.get_response(url, params, data, json, sleep, headers, timeout,
                                    attempts, verify, method=method, **kwargs)
        if response is None:
            return None
        
        soup = BeautifulSoup(response.content, 'lxml')
        return soup

    def get_json(
        self, url: str, params: Optional[dict]=None,
        data: Union[None, str, dict]=None, json: Optional[dict]=None, sleep: int=0,
        headers: Optional[dict]=None, timeout: int=15, attempts: int=5,
        verify: bool=True, method: str='GET', **kwargs
    ) -> Optional[dict]:
        """
        Obtiene el JSON de la URL dada
        """
        bad_api = kwargs.pop('bad_api', False)
        bad_key = kwargs.pop('bad_key', '')

        flagged = kwargs.get('flagged_status_codes', [])

        attempt = 0
        while attempt < attempts:
            attempt += 1
            response = self.get_response(url, params, data, json, sleep, headers, timeout,
                                    attempts, verify, method=method, **kwargs)

            if response is None:
                return None

            if response.status_code in flagged:
                return response

            try:
                _json = response.json()
                if not bad_key or bad_key not in _json:
                    return _json
            except JSONDecodeError:
                print(f'\x1b[1;31;40m[ JSONDecodeError ]\x1b[0m {url}')
                if not bad_api:
                    return None
        print(f'\x1b[1;31;40mMax attempts limit reached!\x1b[0m {url}')
    