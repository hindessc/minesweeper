import subprocess
import pygame
import threading
import select
import sys
import time

class HandlerThread( threading.Thread ):
    """ A thread that handles a conversation with a single remote server.
        Accepts commands of 'close', 'red', 'green' or 'blue', and posts messages
        to the main PyGame thread for processing """
    def __init__( self, file ):
        threading.Thread.__init__(self)
        self.file        = file
        self.data_buffer = ''
        self.done        = False

    def stop( self ):
        self.done = True

    def run( self ):
        read_events_on   = [ self.file ]
        while ( not self.done ):
            # Wait for incoming data, or errors, or 0.3 seconds
            (read_list, write_list, except_list) = select.select( read_events_on, [], [], 0.5 )

            if ( len( read_list ) > 0 ):
                # New data arrived, read it
                incoming = self.file.readline()
                if ( len(incoming) == 0):
                    # Socket has closed
                    new_event = pygame.event.Event( CLOSED ) 
                    pygame.event.post( new_event )
                    self.file.close()
                    self.done = True
                else:
                    # Data has arrived
                    try:
                        new_str = incoming.decode('utf-8')
                        self.data_buffer += new_str
                    except:
                        pass # don't understand buffer

                    # Parse incoming message (trivial parser, not high quality) 
                    # commands are '\n' separated
                    if (self.data_buffer.find('\n') != -1 ):
                        for line in self.data_buffer.split('\n'):
                            line = line.strip()
                            # only make events for valid commands
                            match line[:4]:
                                case "win ":
                                    pygame.event.clear(CONTINUE, False)
                                    new_event = pygame.event.Event( WIN , { "board" : line[4:] } )
                                    self.stop()
                                case "lose":
                                    pygame.event.clear(CONTINUE, False)
                                    new_event = pygame.event.Event( LOSE, { "board" : line[5:] } )
                                    self.stop()
                                case _:
                                    if line:
                                        print("L", line)
                                        new_event = pygame.event.Event( CONTINUE, { "board" : line } )
                            pygame.event.post( new_event )
                        self.data_buffer = ''  # all used-up

CLOSED   = pygame.USEREVENT + 1
WIN      = pygame.USEREVENT + 2
LOSE     = pygame.USEREVENT + 3
CONTINUE = pygame.USEREVENT + 4

def draw(grid):
    grid = str(grid).split("n")
    for j in range(len(grid)):
        line = grid[j]
        for i in range(len(line)):
            char = line[i]
            pygame.draw.rect(screen, "grey", pygame.Rect(80*i+10, 80*j+10, 60, 60))
            if char == "F":
                pygame.draw.rect(screen, "black", pygame.Rect(80*i+15, 80*j+15, 10, 50))
                pygame.draw.polygon(screen, "red", ((80*i+15, 80*j+15), (80*i+15, 80*j+40), (80*i+60, 80*j+25)))
            elif char in ["0","1","2","3","4","5","6","7","8","9"]:
                text = font.render(char, True, "black")
                text_rect = text.get_rect()
                text_rect.center = (80*i+40,80*j+40)
                screen.blit(text, text_rect)

def win(board):
    draw(board)
    won_lost[0] = True
    print("You win")

def lose(board):
    draw(board)
    won_lost[1] = True
    print("You lose")

def play(file, board):
    screen.fill("black")
    draw(board)
    if won_lost[1]:
        text = endFont.render("You Lose", True, "purple")
        text_rect = text.get_rect()
        text_rect.center = (320, 320)
        screen.blit(text, text_rect)
    if won_lost[0]:
        text = endFont.render("You Win", True, "green")
        text_rect = text.get_rect()
        text_rect.center = (320, 320)
        screen.blit(text, text_rect)

def write(file, string):
    try:
        file.stdin.write(bytes(string + "\n", "utf-8"))
        file.stdin.flush()
    except:
        print("failed to write")

size = "8"

won_lost = [False, False]

with subprocess.Popen(["./mineSweeper", size],
                      stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE) as proc:
    board = proc.stdout.readline()
    print(board)

    pygame.init()
    font = pygame.font.Font(None, 72)
    endFont = pygame.font.Font(None, 180)
    screen = pygame.display.set_mode((640, 640))
    clock = pygame.time.Clock()
    running = True

    thread1 = HandlerThread(proc.stdout)
    thread1.start()
    
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == CLOSED:
                running = False
            elif event.type == WIN:
                win(event.__dict__["board"])
            elif event.type == LOSE:
                lose(event.__dict__["board"])
            elif event.type == pygame.MOUSEBUTTONDOWN and not won_lost[0] and not won_lost[1]:
                if pygame.mouse.get_pressed()[0]:
                    print("Left")
                    x, y = pygame.mouse.get_pos()
                    print (x // 80, y // 80)
                    write(proc, "s " + str(x // 80) + " " + str(y // 80))
                elif pygame.mouse.get_pressed()[2]:
                    print("Right")
                    x, y = pygame.mouse.get_pos()
                    write(proc, "f " + str(x // 80) + " " + str(y // 80))
            elif event.type == CONTINUE:
                board = event.__dict__["board"]
                print("C: ", board)
        play(proc, board)
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()
    proc.stdin.close()
#we love you caleb (Angus Milan and Benjamin)

