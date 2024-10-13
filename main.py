import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UnauthorizedError, SessionPasswordNeededError, PeerFloodError, RPCError, UserBannedInChannelError, UserDeactivatedBanError
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import ChannelParticipantsSearch
from datetime import datetime
import os
import time
from telethon.errors import SessionPasswordNeededError
import logging

log_folder = 'logs'
os.makedirs(log_folder, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_folder, 'telegram_spam_parser.log'), level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')

API_ID = ''
API_HASH = ''

def get_account_files(folder):
    if folder == "accounts":
        return [f for f in os.listdir(folder) if f.endswith('.session')]
    elif folder == "parser_results":
        return [f for f in os.listdir(folder) if f.endswith('.txt')]
    else:
        return []

def display_account_list(folder):
    account_files = get_account_files(folder)
    if not account_files:
        print(f"Нет файлов в {folder}.")
        logging.info(f"Нет файлов в {folder}.")
        main_menu()
        return

    print("Список аккаунтов:")
    for idx, account_file in enumerate(account_files, start=1):
        print(f"{idx}. {account_file}")

def choose_account_file(folder):
    display_account_list(folder)
    try:
        choice = int(input("Выберите номер файла: "))
        account_files = get_account_files(folder)
        if 1 <= choice <= len(account_files):
            return account_files[choice - 1]
        else:
            print("Неверный выбор. Пожалуйста, выберите существующий номер файла.")
            return choose_account_file(folder)
    except ValueError:
        print("Введите число.")
        return choose_account_file(folder)

async def add_account():
    phone_number = input("Введите номер телефона: ")
    async with TelegramClient(f'accounts/{phone_number}', API_ID, API_HASH) as client:
        try:
            await client.connect()
            if not await client.is_user_authorized():
                try:
                    await client.send_code_request(phone_number)
                    await client.sign_in(phone_number, input('Введите код подтверждения: '))
                    print(f"Аккаунт {phone_number} успешно добавлен.")
                    logging.info(f"Аккаунт {phone_number} успешно добавлен.")
                except SessionPasswordNeededError:
                    password = input('Введите пароль для двухэтапной аутентификации: ')
                    await client.sign_in(password=password)
                    print(f"Аккаунт {phone_number} успешно добавлен.")
                    logging.info(f"Аккаунт {phone_number} успешно добавлен.")
        except UnauthorizedError as e:
            print(f'Ошибка авторизации: {e}')
            logging.error(f'Ошибка авторизации: {e}')
            await asyncio.sleep(10)
        except Exception as e:
            print(f'Ошибка авторизации: {e}')
            logging.error(f'Ошибка авторизации: {e}')
            await asyncio.sleep(10)

async def send_message(client, user_id, message):
    try:
        
        await client.send_message(user_id, message)
        print(f"Сообщение отправлено пользователю {user_id}")
        logging.info(f"Сообщение отправлено пользователю {user_id}")
        time.sleep(10)
        return True
    except PeerFloodError as e:
        print(f"Ошибка PeerFloodError: {e}")
        logging.error(f"Ошибка PeerFloodError: {e}")
        return False
    except UserBannedInChannelError as e:
        print(f"Ошибка UserBannedInChannelError: {e}")
        logging.error(f"Ошибка UserBannedInChannelError: {e}")
        return False
    except UserDeactivatedBanError as e:
        print(f"Ошибка UserDeactivatedBanError: {e}")
        logging.error(f"Ошибка UserDeactivatedBanError: {e}")
        return False
    except FloodWaitError as e:
        print(f"Ошибка FloodWaitError: {e}")
        logging.error(f"Ошибка FloodWaitError: {e}")
        await asyncio.sleep(e.seconds)
        return True
    except Exception as e:
        print(f"Ошибка отправки сообщения пользователю {user_id}: {str(e)}")
        logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {str(e)}")
        return False

async def spammer(client, message):
    users_file_path = choose_account_file("parser_results")
    rusers_file_path = f"{users_file_path}"
    os.makedirs('spammer_results', exist_ok=True)
    us = 'parser_results/' + users_file_path
    print(us)

    with open(us, 'r') as file:
        users = file.read().splitlines()

    if not users:
        print("Нет пользователей для отправки сообщений. Выход.")
        logging.info("Нет пользователей для отправки сообщений. Выход.")
        return

    users_copy = users[:]
    for user_info in users_copy:
        if user_info == '':
            break
        user_id, tag = user_info.split(':')

        target_user = user_id if tag.replace(" ","") == 'None' else tag
        if tag.replace(" ","") == 'None':
            continue
        target_user = tag
        time.sleep(5)
        print(target_user)
        try:
            if await send_message(client, target_user, message):
                logging.info(f"Сообщение отправлено пользователю {target_user}")

                users.remove(user_info)

                with open(us, 'w') as file:
                    file.write('\n'.join(users))

                with open(os.path.join('spammer_results', rusers_file_path), 'a') as rfile:
                    rfile.write(f"{user_info}\n")
            else:
                print(f"Не удалось отправить сообщение пользователю {target_user}")
                logging.error(f"Не удалось отправить сообщение пользователю {target_user}")

        except (PeerFloodError, UserBannedInChannelError, UserDeactivatedBanError) as e:
            print(f"Аккаунт заблокирован за спам. Завершение работы. Ошибка: {str(e)}")
            logging.error(f"Аккаунт заблокирован за спам. Завершение работы. Ошибка: {str(e)}")
            return
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {target_user}: {str(e)}")
            logging.error(f"Ошибка при отправке сообщения пользователю {target_user}: {str(e)}")

    print("Все сообщения отправлены.")
    logging.info("Все сообщения отправлены.")

async def parser(client):
    chat_username = input("Введите ссылку на чат: ")
    start_id = int(input("От: "))
    end_id = int(input("До: "))
    offset = start_id
    limit = 100
    all_participants = []

    while offset <= end_id:
        try:
            participants = await client(GetParticipantsRequest(
                channel=await client.get_entity(chat_username),
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=limit,
                hash=0
            ))
        except FloodWaitError as e:
            print(f'Необходимо подождать {e.seconds} секунд')
            logging.warning(f'Необходимо подождать {e.seconds} секунд')
            await asyncio.sleep(e.seconds)
            continue
        except RPCError as e:
            print(f'Произошла ошибка RPC: {e}')
            logging.error(f'Произошла ошибка RPC: {e}')
            break
        except Exception as e:
            print(f'Произошла ошибка при получении участников: {e}')
            logging.error(f'Произошла ошибка при получении участников: {e}')
            break

        if not participants.users:
            break

        for participant in participants.users:
            print(f"Найден пользователь: {participant.id} - {participant.username}")
            logging.info(f"Найден пользователь: {participant.id} - {participant.username}")
            await asyncio.sleep(1)

        all_participants.extend(participants.users)
        offset += limit
        await asyncio.sleep(1)

    filename = os.path.join('parser_results', f'users[{datetime.now().strftime("%Y%m%d_%H%M%S")}].txt')
    os.makedirs('parser_results', exist_ok=True)

    try:
        with open(filename, 'w', encoding='utf-8') as file:
            for participant in all_participants:
                file.write(f'{participant.id}: {participant.username}\n')
    except Exception as e:
        print(f'Произошла ошибка при сохранении результатов: {e}')
        logging.error(f'Произошла ошибка при сохранении результатов: {e}')

async def join_group_with_all_sessions(group_tag):
    sessions_folder = 'accounts'
    session_files = [f for f in os.listdir(sessions_folder) if f.endswith('.session')]

    for session_file in session_files:
        session_path = os.path.join(sessions_folder, session_file)
        client = TelegramClient(session_path, API_ID, API_HASH)
        time.sleep(10)
        try:
            await client.start()
            print(f'Logged in with session: {session_file}')

            await client(JoinChannelRequest(group_tag))
            print(f'Successfully joined group: {group_tag} with session: {session_file}')
        
        except SessionPasswordNeededError:
            print(f'Two-factor authentication is enabled for {session_file}. Please provide the password in your implementation.')
        
        except Exception as e:
            print(f'Failed to join group with session {session_file}: {e}')
        
        finally:
            await client.disconnect()

async def main_menu():
    while True:
        print("Меню:")
        print("1. Spammer")
        print("2. Parser")
        print("3. Добавить аккаунт")
        print("4. Массовое добавление чата\группы")
        print("0. Выход")

        choice = input("Введите свой выбор: ")

        if choice in ['1', '2']:
            account_file = choose_account_file("accounts")
            async with TelegramClient(f'accounts/{account_file}', API_ID, API_HASH) as client:
                try:
                    await client.connect()
                    if not await client.is_user_authorized():
                        try:
                            await client.send_code_request(phone_number)
                            await client.sign_in(phone_number, input('Введите код подтверждения: '))
                        except SessionPasswordNeededError:
                            password = input('Введите пароль для двухэтапной аутентификации: ')
                            await client.sign_in(password=password)
                except UnauthorizedError as e:
                    print(f'Ошибка авторизации: {e}')
                    logging.error(f'Ошибка авторизации: {e}')
                    await asyncio.sleep(10)
                    exit()
                except Exception as e:
                    print(f'Ошибка авторизации: {e}')
                    logging.error(f'Ошибка авторизации: {e}')
                    await asyncio.sleep(10)
                    exit()

                if choice == '1':
                    with open('message.txt', 'r', encoding='utf-8') as file:
                        message = file.read()
                    await spammer(client, message)
                elif choice == '2':
                    await parser(client)
        elif choice == '3':
            await add_account()
        elif choice == '4':
            group_tag = input('Введите тег чата или ссылку(@groupname): ')
            await join_group_with_all_sessions(group_tag)
        elif choice == '0':
            break
        else:
            print("Неверный выбор. Пожалуйста, введите допустимую опцию.")

if __name__ == '__main__':
    asyncio.run(main_menu())
