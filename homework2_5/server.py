import socket
import datetime

def load_users():
    users = {}
    try:
        with open('users.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    userid, password, balance = line.split(',')
                    users[userid] = {
                        'password': password,
                        'balance': float(balance)
                    }
    except FileNotFoundError:
        pass
    return users

def save_users(users):
    with open('users.txt', 'w') as f:
        for userid, data in users.items():
            line = f"{userid},{data['password']},{data['balance']:.2f}\n"
            f.write(line)

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('server.log', 'a') as f:
        f.write(f"{timestamp} - {message}\n")

def main():
    users = load_users()
    port = 2525
    s = socket.socket()
    # 修改此行，绑定到所有网络接口（允许其他设备连接）
    s.bind(('0.0.0.0', port))  # 原代码为 socket.gethostname()
    s.listen(5)
    print("服务器已启动，等待连接...")

    while True:
        clientsocket, address = s.accept()
        print(f"Connection from {address} established")
        current_user = None
        authenticated = False

        try:
            while True:
                data = clientsocket.recv(1024).decode().strip()
                if not data:
                    break

                parts = data.split(' ')
                command = parts[0]

                if command == 'HELO':
                    if len(parts) < 2:
                        clientsocket.send("401 ERROR!".encode())
                        log("Invalid HELO command")
                    else:
                        userid = parts[1]
                        if userid in users:
                            current_user = userid
                            clientsocket.send("500 AUTH REQUIRE".encode())
                            log(f"HELO received for user {userid}")
                        else:
                            clientsocket.send("401 ERROR!".encode())
                            log(f"Invalid user {userid}")

                elif command == 'PASS':
                    if not current_user:
                        clientsocket.send("401 ERROR!".encode())
                        log("PASS without HELO")
                    else:
                        if len(parts) < 2:
                            clientsocket.send("401 ERROR!".encode())
                            log("Invalid PASS command")
                        else:
                            password = parts[1]
                            if users[current_user]['password'] == password:
                                authenticated = True
                                clientsocket.send("525 OK!".encode())
                                log(f"User {current_user} authenticated")
                            else:
                                clientsocket.send("401 ERROR!".encode())
                                log(f"Wrong password for {current_user}")

                elif command == 'BALA':
                    if authenticated and current_user:
                        balance = users[current_user]['balance']
                        clientsocket.send(f"AMNT:{balance:.2f}".encode())
                        log(f"Balance checked for {current_user}")
                    else:
                        clientsocket.send("401 ERROR!".encode())
                        log("Unauthorized BALA request")

                elif command == 'WDRA':
                    if authenticated and current_user:
                        if len(parts) < 2:
                            clientsocket.send("401 ERROR!".encode())
                            log("Invalid WDRA command")
                        else:
                            try:
                                amount = float(parts[1])
                                if amount <= 0:
                                    clientsocket.send("401 ERROR!".encode())
                                    log(f"Invalid amount {amount}")
                                else:
                                    if users[current_user]['balance'] >= amount:
                                        users[current_user]['balance'] -= amount
                                        save_users(users)
                                        clientsocket.send("525 OK!".encode())
                                        log(f"Withdrawal {amount} from {current_user}")
                                    else:
                                        clientsocket.send("401 ERROR!".encode())
                                        log(f"Insufficient balance for {current_user}")
                            except ValueError:
                                clientsocket.send("401 ERROR!".encode())
                                log("Invalid amount format")
                    else:
                        clientsocket.send("401 ERROR!".encode())
                        log("Unauthorized WDRA request")

                elif command == 'BYE':
                    clientsocket.send("BYE".encode())
                    log(f"User {current_user} logged out")
                    break

                else:
                    clientsocket.send("401 ERROR!".encode())
                    log(f"Unknown command {command}")

        except ConnectionResetError:
            log("Connection reset by peer")
        finally:
            clientsocket.close()

if __name__ == '__main__':
    main()