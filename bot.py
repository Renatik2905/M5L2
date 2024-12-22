import telebot
from config import *
from logic import *
import os
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


bot = telebot.TeleBot(TOKEN)
manager = DB_Map(DATABASE)


@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обрабатывает команду /start."""
    bot.send_message(message.chat.id,
                     "Привет! Я бот, который может показывать города на карте. Напиши /help для списка команд.")


@bot.message_handler(commands=['help'])
def handle_help(message):
    """Обрабатывает команду /help."""
    bot.send_message(message.chat.id, "Доступные команды:\n"
                                      "/start - Начать работу с ботом\n"
                                      "/help - Показать список команд\n"
                                      "/show_city <city_name> [color:red/blue/green/yellow/black/purple/orange] [fill] [objects] - Показать город на карте\n"
                                      "/remember_city <city_name> - Запомнить город\n"
                                      "/show_my_cities [color:red/blue/green/yellow/black/purple/orange] [fill] [objects] - Показать мои сохраненные города")

@bot.message_handler(commands=['guid'])
def handle_help(message):
    """Обрабатывает команду /guid."""
    bot.send_message(message.chat.id, "КАК ИСПОЛЬЗОВАТЬ:\n"

                                        "Запустите бота.\n"
                                        "Используйте команды /show_city и /show_my_cities с новыми параметрами. Например:\n"
                                        "/show_city London color:blue\n"
                                        "/show_city Paris fill objects\n"
                                        "/show_my_cities color:green fill\n"
                                        "/show_my_cities objects") 


@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    """Обрабатывает команду /show_city."""
    try:
         parts = message.text.split()
         if len(parts) < 2:
            bot.send_message(message.chat.id, "Пожалуйста, укажите название города после команды /show_city")
            return

         city_name = ""
         marker_color_str = "red"
         fill_continents = False
         add_features = False

         i = 1 #Начинаем со второго слова в сообщении
         while i < len(parts):
            if parts[i].startswith('color:'):
                 marker_color_str = parts[i].split(':')[1].lower()
            elif parts[i] == 'fill':
                  fill_continents = True
            elif parts[i] == 'objects':
                 add_features = True
            else:
               if city_name:
                 city_name += " " + parts[i]
               else:
                  city_name = parts[i]
            i+=1 #Переходим к следующему слову
            
         if not city_name:
             bot.send_message(message.chat.id, "Не удалось распознать имя города.")
             return

         try:
            marker_color = MarkerColor(marker_color_str)
         except ValueError:
            marker_color = MarkerColor.RED
            bot.send_message(message.chat.id,
                             f"Неверно указан цвет маркера, используется {marker_color.value}. Доступные цвета: red, blue, green, yellow, black, purple, orange")
            
         coordinates = manager.get_coordinates(city_name)
         if coordinates:
            output_dir = 'user_maps'
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, f'{message.chat.id}_{city_name}.png')
            manager.create_grapf(path, [city_name], marker_color=marker_color, fill_continents=fill_continents,
                                 add_features=add_features)

            with open(path, 'rb') as photo:
               bot.send_photo(message.chat.id, photo)
            os.remove(path)
         else:
            bot.send_message(message.chat.id, "Не удалось найти координаты для указанного города. Проверьте корректность написания города.")


    except Exception as e:
        print(f"Ошибка при обработке show_city: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке вашего запроса.")


@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    """Обрабатывает команду /remember_city."""
    try:
        user_id = message.chat.id
        city_name = ' '.join(message.text.split()[1:])
        if not city_name:
            bot.send_message(message.chat.id, "Пожалуйста, укажите название города после команды /remember_city")
            return
        if manager.add_city(user_id, city_name):
            bot.send_message(message.chat.id, f'Город {city_name} успешно сохранен!')
        else:
            bot.send_message(message.chat.id,
                             'Такого города я не знаю. Убедись, что он написан на английском!')
    except Exception as e:
        print(f"Ошибка при обработке remember_city: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении города.")


@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    """Обрабатывает команду /show_my_cities."""
    try:
        parts = message.text.split()
        user_id = message.chat.id
        cities = manager.select_cities(user_id)
        if not cities:
            bot.send_message(message.chat.id, "Вы пока не добавили ни одного города.")
            return

        marker_color_str = "red"
        fill_continents = False
        add_features = False

        for part in parts:
            if part.startswith('color:'):
                marker_color_str = part.split(':')[1].lower()
            if part == 'fill':
                fill_continents = True
            if part == 'objects':
                add_features = True

        try:
            marker_color = MarkerColor(marker_color_str)
        except ValueError:
            marker_color = MarkerColor.RED
            bot.send_message(message.chat.id,
                             f"Неверно указан цвет маркера, используется {marker_color.value}. Доступные цвета: red, blue, green, yellow, black, purple, orange")

        output_dir = 'user_maps'
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f'{user_id}_my_cities.png')
        manager.create_grapf(path, cities, marker_color=marker_color, fill_continents=fill_continents,
                             add_features=add_features)
        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
        os.remove(path)
    except Exception as e:
        print(f"Ошибка при обработке show_my_cities: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отображении сохраненных городов.")


if __name__ == "__main__":
    bot.polling(none_stop=True)