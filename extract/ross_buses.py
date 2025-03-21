import os
import re
import sys
import boto3
import traceback
import platform
import datetime
import requests
from bs4 import BeautifulSoup
from types import TracebackType
from typing import Optional, Type
from pyvirtualdisplay import Display
from botocore.client import Config
from playwright.sync_api import TimeoutError
from playwright.sync_api import sync_playwright
try:
    from handle.request_handler import RequestsHandler
except ModuleNotFoundError:
    path = os.path.abspath('.')
    sys.path.insert(1, path)
from handle.request_handler import RequestsHandler
from handle.sql_handler import PyMySQLHandler
from handle.boto_handler import BotoHandler
    
class RossBuses():
    """
    Web: bus.com/school-buses
    Metodo: Playwright & Soup
    Duración: Aprox. 15 minutos
    """
    def __init__(self):
        # playwright
        self.playwright = sync_playwright().start()
        self.sesion = requests.session()
        self.browser = self.playwright.firefox.launch(args=['--start-maximized'], headless=True)
        self.context = self.browser.new_context(ignore_https_errors=True)
        self.page = self.context.new_page()
        # Database
        self._db = PyMySQLHandler("172.100.0.2", 
                                   os.environ.get("MYSQL_USER"),
                                   os.environ.get("MYSQL_PASSWORD"),
                                   os.environ.get("MYSQL_DATABASE"))
        self.scraped_buses = self._db.get_buses_titles()
        
    def __enter__(self):
        # Display
        os.environ['PYVIRTUALDISPLAY_DISPLAYFD'] = '0'
        if platform.system() == 'Linux':
            self.display = Display(visible=0, size=(1366, 768))
            self.display.start()
        return self

    def __exit__(self, exception_type: Optional[Type[BaseException]], 
                        exception_value: Optional[BaseException], 
                    exception_traceback: Optional[TracebackType]) -> None:
        if exception_traceback:
            print("Excepción durante la ejecución del scraping...")
            self.upload_log(exception_type, exception_value, exception_traceback)
        # Stop Playwright
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        if self.sesion:
            self.sesion.close()
        if self.display:
            self.display.stop()
        
    
    def upload_log(self, exception_type: Optional[Type[BaseException]], 
                        exception_value: Optional[BaseException], 
                        exception_traceback: Optional[TracebackType]) -> None:
        """
        Realiza el upload del log al S3 (Minio) si ocurre una excepión en el
        Scraping.
        """
        print("Almacenando log en S3 (Minio)...")
        boto_handler = BotoHandler('http://172.100.0.3:9000', 
                                   os.environ.get('MINIO_ROOT_USER'), 
                                   os.environ.get('MINIO_ROOT_PASSWORD'))
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        key = f'exceptions/rossbuses/rossbuses_exception_{timestamp}.log'
        exception_info = ''.join(traceback.format_exception(exception_type, 
                                                            exception_value, 
                                                            exception_traceback))
        boto_handler.put_log(bucket='scraping-data', key=key, body=exception_info)
        boto_handler.close()
        
    def scraping(self) -> None:
        """
        Metodo principal que se encarga de interactuar con la pagina de
        RossBuses, haciendo Hover sobre el nav de buses, realiza la paginación
        de seccion a seccion y de bus a bus, ayudandose de un count para saber
        la cantidad de subitems que tiene cada <li>
        Llama al metodo get_fields() para realizar la obtencion de la metadata
        de cada bus.
        """
        print("Ejecutando Scraping RossBuses...")
        self.page.goto('https://www.rossbus.com/')
        self.page.wait_for_timeout(5000)
        school_buses = self.page.locator('nav ul#navigation li:has-text("Buses")').nth(0)
        self.page.wait_for_timeout(2000)
        submenu_items = school_buses.locator('ul.Submenu li')
        for submenu_index in range(submenu_items.count()):
            school_buses.hover()
            submenu_items.nth(submenu_index).click()
            self.page.wait_for_timeout(2000)
            info_divs = self.page.locator('div.Information')
            for bus_index in range(info_divs.count()):
                info_divs.nth(bus_index).locator('div.FillYellowBtn').click()
                self.page.wait_for_timeout(2000)
                try:
                    bus_faqs = self.page.locator('div.FaqTitle')
                except TimeoutError:
                    print("Bus no tiene solapa de detalles")
                    self.page.go_back()
                    continue
                for faq_index in range(bus_faqs.count()):
                    bus_faqs.nth(faq_index).click()
                    self.page.wait_for_timeout(2000)
                    self.get_fields()
                    self.page.wait_for_timeout(1000)
                self.page.wait_for_timeout(2000)
                self.page.go_back()
                self.page.wait_for_timeout(1000)
        print("Exit.")
        self._db.close()
    
    def get_fields(self) -> None:
        """
        Metodo que obtiene datos de cada Bus parseando el source page de PW
        a BeautifulSoup, con la data de la seccion "Specifications" y demas campos
        generales arma un diccionario.
        Los diferentes campos de este diccionario luego se insertan en las distintas
        tablas via similitud de nombres (entre keys y columnas de cada tabla).
        """
        source_html = self.page.content()
        soup = BeautifulSoup(source_html, 'html.parser')
        bus_title = soup.find("h5", class_='BlueTitle').text.strip()
        print(f"Scraping bus {bus_title}...")
        if bus_title in self.scraped_buses: return
        bus_description = soup.find('div', class_='Describe FParagraph1 EditorText').text.strip()
        bus_image = soup.find('div', class_='ImgWrap')
        extra_info = soup.find('div', class_='Extra_Info_Wrap')
        if extra_info:
            ac = extra_info.find('li', re.compile('A/C'))
        model_name = soup.find('div', class_='FaqTitle').text.strip()
        bus_details = soup.find_all('li', class_='addColon')
        bus_info = {}
        bus_info['title'] = f'{bus_title} {model_name}' if model_name.lower() != 'specifications' else bus_title
        bus_info['model'] = model_name if model_name.lower() != 'specifications' else bus_title
        bus_info['description'] = bus_description.strip().replace(r'\n', '')
        bus_info['airconditioning'] = ac.text if ac else None
        bus_info['image'] = bus_image.find('img')['src'].strip() if bus_image else None
        for item in bus_details:
            key_div = item.find('div', class_='First')
            value_div = item.find('div', class_='Last')
            if key_div and value_div:
                key = key_div.get_text(strip=True)
                value = value_div.get_text(strip=True)
                bus_info[key] = value
        print(bus_info)
        self.insert_data(bus_info)
        
    def insert_data(self, data):
        """
        Realiza las distintas inserciones de la data de cada bus
        en las 3 tablas de MySQL.
        """
        ### Inserción de la data en tabla buses (por similitud de campos) ###
        print("INSERTING BUS DATA INTO MySQL...")
        buses_query = """
                        INSERT INTO buses (title, model, 
                            description, airconditioning, 
                            passengers, engine, 
                            transmission, gvwr, 
                            brake
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
        bus_id = self._db.insert(buses_query, (
                                        data.get("title"), 
                                        data.get("model"),
                                        data.get("description"),
                                        data.get("airconditioning").upper() if data.get("airconditioning") else "NONE",  # airconditioning
                                        data.get("Capacity"), 
                                        data.get("Engine (4N/5N/6N/6R)"),
                                        data.get("Transmission (4N/5N/6N/6R)"), 
                                        data.get("GVWR (4N)"),
                                        data.get("Brakes (4N/5N/6N/6R)") 
                                    ))
        print("BUS DATA INSERTED IN TABLE buses")
        ### Inserción de la data en tabla buses_overview (por similitud de campos) ###
        overview_query = """
                            INSERT INTO buses_overview (bus_id, mdesc, intdesc, extdesc, features, specs)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
        intdesc = f"""
                    Interior Floor Length: {data.get('Interior Floor length', '')}
                    Interior Height at Hip: {data.get('Interior height at hip', '')}
                    Interior Height at Center Line: {data.get('Interior height at center line', '')}
                    """

        extdesc = f"""
                    Exterior Length Overall: {data.get('Exterior length overall', '')}
                    Exterior Width Overall: {data.get('Exterior width overall', '')}
                    Exterior Height Overall: {data.get('Exterior height overall', '')}
                    """
        features = f"""
                    Capacity: {data.get('Capacity', '')}
                    Number of Rows: {data.get('Number of Rows', '')}
                    Entrance Door: {data.get('Entrance door', '')}
                    Rear Bumper: {data.get('Rear Bumper', '')}
                    """

        specs = f"""
                    Engine: {data.get('Engine (4N/5N/6N/6R)', '')}
                    Wheelbase (4N): {data.get('Wheelbase (4N)', '')}
                    Wheelbase (5N/6N/6R): {data.get('Wheelbase (5N/6N/6R)', '')}
                    Transmission: {data.get('Transmission (4N/5N/6N/6R)', '')}
                    GVWR (4N): {data.get('GVWR (4N)', '')}
                    GVWR (5N/6N/6R): {data.get('GVWR (5N/6N/6R)', '')}
                    Fuel Tank: {data.get('Fuel Tank (4N/5N/6N/6R)', '')}
                    Brakes: {data.get('Brakes (4N/5N/6N/6R)', '')}
                    Tires: {data.get('Tires (4N/5N/6N/6R)', '')}
                    Alternator: {data.get('Alternator (4N/5N/6N/6R)', '')}
                    Battery: {data.get('Battery (4N/5N/6N/6R)', '')}
                """
        self._db.insert(overview_query, (
                                            bus_id,
                                            data.get("description"),
                                            intdesc.strip(),
                                            extdesc.strip(),
                                            features.strip(),
                                            specs.strip()
                                        ))
        print("BUS DATA INSERTED IN TABLE buses_overview")
        ### Inserción de la data en tabla buses_images (solo tenemos link) ###
        images_query = """
                        INSERT INTO buses_images (name, url, description, image_index, bus_id)
                        VALUES (%s, %s, %s, %s, %s)
                        """
        self._db.insert(images_query, ('Main Image', data['img_url'], 'Main bus image', 0, bus_id))
        print("BUS DATA INSERTED IN TABLE buses_images")
        
if __name__ == '__main__':
    with RossBuses() as scraper:
        scraper.scraping()