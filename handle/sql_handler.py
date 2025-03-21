import pymysql

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
        print("Conectado a MySQL")
        
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