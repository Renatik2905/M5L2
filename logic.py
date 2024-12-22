import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from enum import Enum


class MarkerColor(Enum):
    """Перечисление для выбора цвета маркера"""
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    BLACK = "black"
    PURPLE = "purple"
    ORANGE = "orange"


class DB_Map():
    def __init__(self, database):
        self.database = database

    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city
                            FROM users_cities
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))

            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_grapf(self, path, cities, marker_color=MarkerColor.RED, fill_continents=False, add_features=False):
        """Создает карту с отметками городов, возможностью заливки континентов и добавления географических объектов"""
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        
        # Добавляем заливку континентов и океанов
        if fill_continents:
           ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0) # Добавляем континенты
           ax.add_feature(cfeature.OCEAN, facecolor='lightblue', zorder=0)  # Добавляем океаны
        else:
            ax.stock_img()  # Используем стандартную карту если не нужна заливка
        
        ax.add_feature(cfeature.COASTLINE) #Добавляем береговую линию
        
        if add_features:
           ax.add_feature(cfeature.BORDERS, linestyle=':', zorder=1) # Добавляем границы стран
           ax.add_feature(cfeature.STATES, linestyle='-', linewidth=0.5, zorder=1) # Добавляем границы штатов
           ax.add_feature(cfeature.LAKES,  facecolor='lightblue', zorder=1) # Добавляем озера
           ax.add_feature(cfeature.RIVERS, edgecolor='blue', zorder=1) # Добавляем реки
        
        
        
        if cities:  # Рисуем города только, если они есть в списке
            for city in cities:
                coordinates = self.get_coordinates(city)
                if coordinates:
                    lat, lng = coordinates
                    ax.plot(lng, lat, color=marker_color.value, marker=".", transform=ccrs.Geodetic(), label=city)  # Добавляем подпись и маркер
            ax.legend(loc="upper left")  # Добавляем легенду
            plt.savefig(path)
        else:
            plt.savefig(path)  # Сохраняем пустую карту, если нет городов

        plt.close()

    def draw_distance(self, city1, city2, marker_color=MarkerColor.RED, fill_continents=False, add_features=False):
        """Создает карту с линией, соединяющей два города"""
        ax = plt.axes(projection=ccrs.PlateCarree())

        if fill_continents:
           ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0) # Добавляем континенты
           ax.add_feature(cfeature.OCEAN, facecolor='lightblue', zorder=0)  # Добавляем океаны
        else:
             ax.stock_img() # Используем стандартную карту если не нужна заливка

        ax.add_feature(cfeature.COASTLINE)

        if add_features:
           ax.add_feature(cfeature.BORDERS, linestyle=':', zorder=1)
           ax.add_feature(cfeature.STATES, linestyle='-', linewidth=0.5, zorder=1)
           ax.add_feature(cfeature.LAKES,  facecolor='lightblue', zorder=1) # Добавляем озера
           ax.add_feature(cfeature.RIVERS, edgecolor='blue', zorder=1)  # Добавляем реки

        coord1 = self.get_coordinates(city1)
        coord2 = self.get_coordinates(city2)

        if coord1 and coord2:
            lon1, lat1 = coord1
            lon2, lat2 = coord2

            ax.plot([lon1, lon2], [lat1, lat2],
                    color=marker_color.value, linewidth=2, marker='o',
                    transform=ccrs.Geodetic())

            ax.plot([lon1, lon2], [lat1, lat2],
                    color='gray', linestyle='--',
                    transform=ccrs.PlateCarree())

            plt.text(lon1 - 3, lat1 - 12, city1,
                    horizontalalignment='right',
                    transform=ccrs.Geodetic())

            plt.text(lon2 + 3, lat2 - 12, city2,
                    horizontalalignment='left',
                    transform=ccrs.Geodetic())

            plt.show()
        else:
            print("Не удалось получить координаты для одного или обоих городов")


if __name__ == "__main__":
    m = DB_Map(DATABASE)
    # m.create_user_table() # Убрано, чтобы не создавать таблицу каждый раз при отладке.
    # Пример использования create_grapf
    m.create_grapf('test_map.png', ['Tokyo', 'London', 'Paris'], marker_color=MarkerColor.GREEN, fill_continents=True, add_features=True) #Тест для нескольких городов
    # Пример использования draw_distance
    m.draw_distance('Tokyo', 'London', marker_color=MarkerColor.BLUE, fill_continents=False, add_features=True)
