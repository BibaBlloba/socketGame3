import socket
import threading
from dataclasses import dataclass
from typing import Dict


@dataclass
class Player:
    name: str
    x: int
    y: int


players: Dict[str, Player] = {}


class TCPServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False

    def start(self):
        """Запуск сервера"""
        try:
            # Создаем TCP сокет
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Разрешаем повторное использование адреса
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Привязываем сокет к адресу и порту
            self.server_socket.bind((self.host, self.port))

            # Начинаем прослушивание (максимум 5 подключений в очереди)
            self.server_socket.listen(5)

            self.running = True
            print(f'🚀 Сервер запущен на {self.host}:{self.port}')
            print('📞 Ожидание подключений...')

            # Основной цикл принятия подключений
            while self.running:
                try:
                    # Принимаем входящее подключение
                    client_socket, client_address = self.server_socket.accept()
                    print(f'✅ Подключился клиент: {client_address}')

                    # Обрабатываем клиента в отдельном потоке
                    client_thread = threading.Thread(
                        target=self.handle_client, args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except OSError as e:
                    if self.running:
                        print(f'❌ Ошибка при принятии подключения: {e}')
                    break

        except Exception as e:
            print(f'💥 Ошибка запуска сервера: {e}')
        finally:
            self.stop()

    def handle_client(self, client_socket, client_address):
        """Обработка клиентского подключения"""
        try:
            # Отправляем приветственное сообщение
            welcome_msg = f'Добро пожаловать на сервер! Ваш адрес: {client_address}\r\n'
            client_socket.send(welcome_msg.encode('utf-8'))

            # Цикл обработки данных от клиента
            while self.running:
                try:
                    # Получаем данные от клиента (максимум 1024 байта)
                    data = client_socket.recv(1024)
                    if not data:
                        break  # Клиент отключился

                    # Декодируем и обрабатываем сообщение
                    message = data.decode('utf-8').strip()
                    print(f'📨 От {client_address}: {message}')

                    # Эхо-ответ
                    response = f'ECHO: {message}\r\n'
                    client_socket.send(response.encode('utf-8'))

                    # Завершаем работу если клиент отправил "exit"
                    if message.lower() == 'exit':
                        break

                except ConnectionResetError:
                    break
                except Exception as e:
                    print(f'❌ Ошибка обработки данных от {client_address}: {e}')
                    break

        except Exception as e:
            print(f'💥 Ошибка в обработчике клиента {client_address}: {e}')
        finally:
            # Закрываем соединение с клиентом
            client_socket.close()
            print(f'🔌 Клиент отключен: {client_address}')

    def stop(self):
        """Остановка сервера"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print('🛑 Сервер остановлен')


def main():
    # Создаем и запускаем сервер
    server = TCPServer()

    try:
        server.start()
    except KeyboardInterrupt:
        print('\n⏹️  Остановка сервера по запросу пользователя')
        server.stop()


if __name__ == '__main__':
    main()
