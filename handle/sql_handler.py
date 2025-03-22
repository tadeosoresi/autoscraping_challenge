import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

class PyMySQLHandler():
    """
    Clase que se encarga de la conexión a MySQL y las 
    distintas operaciones.
    """
    def __init__(self, host:str, user:str, password:str, db:str, charset="utf8mb4"):
        self._connection = pymysql.connect(host=host,
                                            user=user,
                                            password=password,
                                            database=db,
                                            charset=charset,
                                            cursorclass=pymysql.cursors.DictCursor)
        print("Conectado a MySQL via PyMySQL")
        
    def close(self):
        if self._connection and self._connection.open:
            self._connection.close()
            
    def insert(self, query:str, data:tuple) -> int:
        """
        Inserta data en cierta tabla.
        Args:
            query: str
            data: tuple
        Returns:
            last_id: int
            Esto sirve para la posterior insercion de datos con FK
        """
        with self._connection:
            with self._connection.cursor() as cursor:
                try:
                    cursor.execute(query, data)
                    last_id = cursor.lastrowid
                    # Save changes
                    self._connection.commit()
                except pymysql.MySQLError as e:
                    print(f"Error al insertar en MySQL: {e}")
                    self._connection.rollback()
                    raise
        return last_id
    
    def get_buses_titles(self) -> set:
        """
        Metodo para evitar insertar duplicados (via title).
        Realiza una query a la tabla buses y extrae los titles.
        Returns:
            titles: set
        """
        with self._connection:
            with self._connection.cursor() as cursor:
                query = f"SELECT title FROM buses;"
                cursor.execute(query)
                 # Obtenemos titles de todos los buses
                titles = {row[0] for row in cursor.fetchall()}
        return titles

class SQLAlchemyHandler:
    """
    Clase que se encarga de la conexión a MySQL y las distintas 
    operaciones usando SQLAlchemy.
    """
    def __init__(self, host: str, user: str, password: str, db: str, charset="utf8mb4"):
        self._engine = create_engine(
            f"mysql+pymysql://{user}:{password}@{host}/{db}?charset={charset}",
            echo=False,
            future=True
        )
        self._Session = sessionmaker(bind=self._engine)
        print("Conectado a MySQL via SQLAlchemy")

    def close(self):
        self._engine.dispose()
        print("Conexión cerrada")

    def insert(self, query: str, data: dict) -> int:
        """
        Inserta data en la tabla.
        Args:
            query: str (query con parámetros named style, ej: :title, :description)
            data: dict (los datos a insertar)
        Returns:
            last_id: int
            Esto sirve para la posterior insercion de datos con FK
        """
        session = self._Session()
        last_id = None
        try:
            result = session.execute(text(query), data)
            session.commit()
            last_id = result.lastrowid
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error al insertar en MySQL: {e}")
            raise
        finally:
            session.close()
        return last_id

    def get_buses_titles(self) -> set:
        """
        Recupera los titles de la tabla 'buses' para evitar duplicados.
        Returns:
            titles: set
        """
        session = self._Session()
        titles = set()
        try:
            result = session.execute(text("SELECT title FROM buses;"))
            titles = {row.title for row in result.fetchall()}
        except SQLAlchemyError as e:
            print(f"Error al obtener titles: {e}")
            raise
        finally:
            session.close()
        return titles
