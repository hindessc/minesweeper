import subprocess
import pygame
import threading
import select

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
                                    new_event = pygame.event.Event( CONTINUE, { "board" : line } )
                            pygame.event.post( new_event )
                        self.data_buffer = ''  # all used-up

CLOSED   = pygame.USEREVENT + 1
WIN      = pygame.USEREVENT + 2
LOSE     = pygame.USEREVENT + 3
CONTINUE = pygame.USEREVENT + 4

def draw(grid):
    print(grid)
    grid = str(grid).split("n")
    for i in range(len(grid)):
        line = grid[i]
        for j in range(len(line)):
            pygame.draw.rect(screen, "grey", pygame.Rect(80*i+10, 80*j+10, 60, 60))
#            pygame.draw.rect(screen, "red", pygame.Rect(80*i+20, 80*j+20, 40, 40))
    
    for i in range(len(grid)):
        line = grid[i]
        for j in range(len(line)):
            char = line[j]
            match char:
                case "F":
                    print("flag")
                    pygame.draw.rect(screen, "red", pygame.Rect(80*i+20, 80*j+20, 40, 40))
                    pygame.draw.polygon(screen, "red", ((80*i+10, 80*j+10), (80*i+40, 80*j+10), (80*i+25, 80*j+60)))

def win(board):
    draw(board)
    print("You win")
    print("You lose")
    #new_event = pygame.event.Event( WIN, { "board" : board } )
    #pygame.event.post( new_event )

def lose(board):
    draw(board)
    print("You lose")
    #new_event = pygame.event.Event( LOSE, { "board" : board } )
    #pygame.event.post( new_event )

def play(file, board):
    screen.fill("black")
    draw(board)
    #write(file, "s " + str(random.randint(0,7)) + " " + str(random.randint(0,7)))
    pygame.event.post( pygame.event.Event( CONTINUE, { "board" : board } ))

def write(file, string):
    try:
        file.stdin.write(bytes(string + "\n", "utf-8"))
        file.stdin.flush()
    except:
        print("failed to write")

size = "8"

with subprocess.Popen(["./mineSweeper", size],
                      stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE) as proc:
    l = proc.stdout.readline()
    print(l)

    pygame.init()
    screen = pygame.display.set_mode((640, 640))
    clock = pygame.time.Clock()
    running = True

    write(proc, "f 1 2")

    print("1")

    play(proc, l)
    
    print("2")

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
            elif event.type == CONTINUE:
                play(proc, event.__dict__["board"])

        pygame.display.flip()
        clock.tick(10)  # limits FPS to 60

    pygame.quit()
    proc.stdin.close()


