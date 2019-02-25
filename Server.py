# napraviti da ne mogu 2 ista igraca da se konektuju

from socket import *
from threading import *
from pathlib import Path
import sqlalchemy as sa
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
import hashlib
import os
import traceback

basedir = os.path.abspath(os.path.dirname(__file__))
engine = sa.create_engine('sqlite:///' + os.path.join(basedir, 'quizDB.sqlite'))

session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(15), nullable=False, unique=True)
    password = sa.Column(sa.String(300), nullable=False)
    victories = sa.Column(sa.Integer)
    losses = sa.Column(sa.Integer)
    points = sa.Column(sa.Integer)

    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.sha224(password.encode()).hexdigest()
        self.victories = 0
        self.losses = 0
        self.points = 0


class Question(Base):
    __tablename__ = 'questions'

    id = sa.Column(sa.Integer, primary_key=True)
    question = sa.Column(sa.String, nullable=False)
    correct_answer = sa.Column(sa.String, nullable=False)
    false_answer1 = sa.Column(sa.String, nullable=False)
    false_answer2 = sa.Column(sa.String, nullable=False)
    false_answer3 = sa.Column(sa.String, nullable=False)

    def __init__(self, question, ca, fa1, fa2, fa3):
        self.question = question
        self.correct_answer = ca
        self.false_answer1 = fa1
        self.false_answer2 = fa2
        self.false_answer3 = fa3


Base.metadata.create_all(engine)


# sta ovo znaci


class UserSchema(ModelSchema):
    class Meta:
        model = User


class QuestionSchema(ModelSchema):
    class Meta:
        model = Question


user_schema = UserSchema()


class Game:
    guestions = {'prvo', 'drugo', 'trece', 'cetvto '
                                           'peto'}


class ClientHandler(Thread):
    # slanje usernamea moze biti problem zbog registracije i provere imena
    def __init__(self, client_socket, client_address):
        self.socket = client_socket
        self.address = client_address
        # self.username = client_username
        self.username = ''
        self.playing = False
        self.response = None

        self.invited = False
        self.has_invited = False

        super().__init__()
        self.start()
        # start poziva metodu run i tu pravim tredove

    def run(self):
        # print('<{}> has connected!'.format(self.username))
        '''
        try:
            self.socket.send('Welcome!'.encode())
            if len(active_players)==2:
                start_game(active_players[0], active_players[1])
        except ConnectionResetError:
            disconnect_message = 'User {} terminated his connection'.format(self.username)
            print(disconnect_message)
            if self in active_players:
                active_players.remove(self)

            self.socket.close()
        '''
        try:
            self.socket.send('Welcome!'.encode())
            self.commands()
        except ConnectionResetError:
            disconnect_message = 'User {} terminated his connection'.format(self.username)
            print(disconnect_message)
            if self in active_players:
                active_players.remove(self)

            self.socket.close()

    def commands(self):
        message_for_new_user = "What do you want to do? " \
                               "\n     REGISTER - for new users " \
                               "\n     LOGIN - for existing users" \
                               "\n     STAT - statistics of wins and losses" \
                               "\n     QUIT - for exiting application "
        self.socket.send(message_for_new_user.encode())
        while True:
            client_input = self.socket.recv(1024).decode()

            if client_input == 'REGISTER':
                self.registration()
                self.use_loggedin()
                break

            elif client_input == 'LOGIN':
                self.login()
                self.use_loggedin()
                break

            elif client_input == 'QUIT':
                self.quit()
                break
            elif client_input == 'STAT':
                self.statistics()
                self.use_loggedin()
                break

            else:
                self.socket.send("Entered symbols are not valid command "
                                 "\nPlease use one of above mentioned commands".encode())
        return

    def registration(self):
        self.socket.send('To register new user you have to enter username and password'.encode())
        # getting username
        while True:
            self.socket.send('Username: '.encode())
            username = self.socket.recv(1024).decode()
            validation = valid_username(username)
            if validation == 'VALID':
                self.username = username
                break
            elif validation == 'EXIST':
                self.socket.send('That username already exists. What do you want to do?'
                                 '\n    LOGIN - go to login'
                                 '\n    MENU - go to the main menu'
                                 '\n    REG - register'
                                 '\n    *** entering anything other than LOGIN or MENU will return you to registration'.encode())
                client_input = self.socket.recv(1024).decode()
                if client_input == 'LOGIN':
                    self.login()
                    return
                elif client_input == 'MENU':
                    self.commands()
                    return
            elif validation == 'ERROR':
                self.socket.send('An error occured while opening file with user data')
            else:
                self.socket.send(validation.encode())

        # getting password
        while True:
            self.socket.send('Password: '.encode())
            password = self.socket.recv(1024).decode()
            validation = valid_password(password)
            if validation == 'VALID':
                break

            else:
                self.socket.send(validation.encode())

        new_user = User(username, password)
        session.add(new_user)
        session.commit()
        self.username = username
        print('User {} has been registered'.format(self.username))
        self.socket.send('You have been registered. You can now continue using calculator'.encode())

    def login(self):
        self.socket.send('To login you have to enter username and password'.encode())

        while True:
            self.socket.send('Username: '.encode())
            username = self.socket.recv(1024).decode()
            if is_connected(username):
                self.socket.send(
                    'Player with this username is already connected, please use another account'.encode())
                continue
            exist = exist_username(username)
            if exist == 'EXIST':
                break

            else:

                self.socket.send(exist.encode())
                self.socket.send('Do you want to return to a main menu, or enter a new username? '
                                 '\n    MENU - return to a main menu'
                                 '\n    LOGIN - enter a new username'
                                 '\n    *** entering anything other than LOGIN wil return to a main menu'.encode())

                client_input = self.socket.recv(1024).decode()
                if client_input != 'LOGIN':
                    self.commands()
                    return
        while True:
            self.socket.send('Password: '.encode())
            password = self.socket.recv(1024).decode()
            matching = match_password(username, password)
            if matching == 'MATCH':
                break
            else:
                self.socket.send(matching.encode())
                self.socket.send('Do you want to return to a main menu, or enter a new password? '
                                 '\n    MENU - return to a main menu'
                                 '\n    PASS - enter a new password'
                                 '\n    *** entering anything other than PASS wil return to a main menu'.encode())
                client_input = self.socket.recv(1024).decode()
                if client_input != 'PASS':
                    self.commands()
                    return
        self.username = username
        print('User {} has connected'.format(self.username))
        self.socket.send('Login successful. '.encode())

    def use_loggedin(self):
        if self not in active_players:
            active_players.append(self)
        if len(active_players) == 1:
            self.socket.send('There are no active players, please wait for someone'.encode())

        else:
            self.show_active()
            user_input = self.socket.recv(1024).decode()
            if user_input == "QUIT":
                self.quit()
            elif not self.playing:
                if user_input == 'STAT':
                    self.statistics()
                    self.use_loggedin()
                opponent = self
                for player in active_players:
                    if player.username == user_input:
                        opponent = player
                        break
                start_game(self, opponent)
        while True:

            try:
                if self.playing:
                    self.play()
                if self.invited:
                    continue
                user_input = self.socket.recv(1024).decode()
                if user_input == "QUIT":
                    self.quit()
                    break

                elif user_input == 'STAT':
                    self.statistics()
                    self.use_loggedin()
                    break

                elif self.invited:
                    self.response = user_input

                elif user_input == 'CON':
                    self.use_loggedin()
                else:
                    self.socket.send("Entered symbols are not valid command "
                                     "\nPlease use one of above mentioned commands".encode())


            except ConnectionRefusedError:
                # korisnik se odjavio
                disconnect_message = 'User {} has disconnected'.format(self.username)
                print(disconnect_message)
                self.socket.send('CLOSE'.encode())
                if self in active_players:
                    active_players.remove(self)

                self.socket.close()
                break

        return

    def play(self):
        i = 0
        questions = ['prvo', 'drugo', 'trece', 'cetvto ', 'peto']
        while i < 5:
            self.socket.send(questions[i].encode())
            self.socket.recv(1024).decode()
            i += 1

        self.stop_game()

    def stop_game(self):
        message_for_player = "What do you want to do? " \
                             "\n     CON - play new game " \
                             "\n     QUIT - for exiting application "
        self.playing = False
        self.invited = False
        self.socket.send(message_for_player.encode())

    def quit(self):
        disconnect_message = 'User {} has been disconnected'.format(self.username)
        print(disconnect_message)
        # ConnectionAbortedError
        try:
            if self in active_players:
                active_players.remove(self)
            self.socket.send('CLOSE'.encode())
            self.socket.close()
        except ConnectionAbortedError:
            pass
        # ovo vrv nije pametno

    def statistics(self):

        player = list(session.query(User).filter_by(username=self.username))

        self.socket.send('Your statistics is'
                         '\n{} - wins'
                         '\n{} - losses'
                         '\n{} - Total numbers of points'.format(player[0].victories, player[0].losses,
                                                                 player[0].points).encode())

    def show_active(self):
        self.socket.send('These are active players'.encode())
        for player in active_players:
            if not self == player:
                self.socket.send(player.username.encode())
        self.socket.send('Type name one of them to start a game'.encode())

    def waiting_too_long(self):
        self.socket.send('There is no response'.encode())

def valid_username(name):
    if (' ' in name) or ('  ' in name):
        return 'Username cannot contain spaces, enter the new one'

    same_username = list(session.query(User).filter_by(username=name))

    if len(same_username) != 0:
        return 'EXIST'

    return 'VALID'


def valid_password(password):
    if (' ' in password) or ('  ' in password):
        return 'Password cannot contain spaces, enter the new one'

    if len(password) < 8:
        return 'Password must contain at least 8 characters, enter the new one'
    for c in password:
        if c.isupper():
            break
    else:
        return "Password must contain at least one uppercase letter, enter the new one"
    for c in password:
        if c.isdigit():
            break
    else:
        return "Password must contain at least one number, enter the new one"

    return 'VALID'


def exist_username(name):
    same_username = list(session.query(User).filter_by(username=name))
    if len(same_username) != 0:
        return 'EXIST'
    return 'That username does not exist'


def match_password(name, password):
    same_username = list(
        session.query(User).filter_by(username=name, password=hashlib.sha224(password.encode()).hexdigest()))

    if len(same_username) != 0:
        return 'MATCH'
    else:
        return 'Wrong password'


def start_game(player1, player2):
    if player2 not in active_players:
        player1.socket.send('That player is not active any more'.encode())
        player1.use_loggedin()
        return
    active_players.remove(player2)
    active_players.remove(player1)
    if player2.username == player1.username:
        player1.socket.send('Misspelling '.encode())
        player1.use_loggedin()
        return
    try:
        player2.socket.send('User {} wants to play against you'
                            '\nYES - play with him'
                            '\nNO - cancel play'.format(player1.username).encode())
        player2.invited = True
        # ne prima odgovore ako niju u proavoj vezi
        # response = player2.socket.recv(1024).decode()

        timer = Timer(30.0, player1.waiting_too_long)  # 30 seconds
        timer.start()
        while True:
            # response = player2.socket.recv(1024).decode()
            if player2.response is not None:
                timer.cancel()
                if player2.response == 'YES':
                    player2.socket.send('Starting game with {}'.format(player1.username).encode())
                    player1.socket.send('Starting game with {}'.format(player2.username).encode())
                    player1.playing = True
                    player2.playing = True

                else:
                    player1.socket.send('User {} declined request for game'.format(player2.username).encode())
                    active_players.append(player2)
                    active_players.append(player1)
                break
    except:
        traceback.print_exc()
        player1.socket.send("Error while begin of game".encode())
        player2.socket.send("Error while begin of game".encode())
        print("Error while begin of game")




def is_connected(username):
    for player in active_players:
        if player.username == username:
            return True

    return False


def play_game(player1, player2):
    player2.socket.send('playing'.encode())
    player1.socket.send('playing'.encode())
    player2.playing = True
    player1.playing = True

    '''
    ja bih ovde napravila objakat klase Game i onda tu sacuvana pitanja za ova dva igraca, 
    a onda ta pitanja ucitala u listu u metodi play i prikazivala.
    Ya svako pitanje treba prikazati i ponudjene odgovore i odvojeno pokrenuti tajmer
    tako da se vreme zaustavi kad korisnik odgovori, a ako ne odgovori za 15s da se prikaze novo pitanje
    na osnovu vremena odgovora bodovai oba igraca
    onda im uporediti broj pona i prikazati pobednika
    uneti u bazu podatke  pobedama i porazima    
    
    primer za koristenje tajmera imate u metodi start_game
    
    osmislti nacin bodovanja 
    '''






serverName = 'localhost'
serverPort = 8090

active_players = []

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(5)
print("Server is ready to accept new connection")
while True:
    print('Waiting for connection')
    try:
        clientSocket, clientAddress = serverSocket.accept()
        print("Connection established")
        # clientUsername = clientSocket.recv(1024).decode()
        # ovde ce ici provera imena
        client = ClientHandler(clientSocket, clientAddress)
    except OSError:
        print("Client tried to connect, but something went wrong and connection was not established")
        # treba li ovde da se zatvara konekcija
