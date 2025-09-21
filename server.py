import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('localhost', 8080))
server_socket.listen(5)

print('🚀 Сервер запущен на localhost:8080')
print('📞 Ожидание подключений...')

try:
    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f'✅ Подключился клиент: {addr}')

            try:
                data = client_socket.recv(1024)
                if data:
                    print(f'📨 Получено от {addr}: {data.decode()}')
                    client_socket.send(b'Message received!')
            except ConnectionResetError:
                print(f'🔌 Клиент {addr} отключился неожиданно')
            except Exception as e:
                print(f'⚠️ Ошибка при обработке данных от {addr}: {e}')
            finally:
                client_socket.close()
                print(f'🔌 Соединение с {addr} закрыто')

        except OSError as e:
            if e.errno == 22:
                print('❌ Ошибка: Неверный аргумент при accept()')
                break
            else:
                print(f'❌ Ошибка accept(): {e}')
                break
        except KeyboardInterrupt:
            print('\n⏹️ Остановка сервера по запросу пользователя')
            break
        except Exception as e:
            print(f'❌ Неожиданная ошибка: {e}')
            break

finally:
    server_socket.close()
    print('🛑 Сервер остановлен')
