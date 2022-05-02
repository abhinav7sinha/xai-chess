import util
import chess
import threading

import os
os.system('cls' if os.name == 'nt' else 'clear')

class xai_chess():
    '''
    class containing core xai-chess functionality
    '''

    def __init__(self) -> None:
        # initialize util object from Util class
        self.util_obj=util.Util()
    
    # def
    
if __name__=='__main__':
    xai_prog=xai_chess()
    util_obj=xai_prog.util_obj

    # remember to close this thread
    stockfish=util_obj.set_engine(UCI_Elo=2850)

    game=xai_prog.util_obj.game
    board=game.board()
    moves=iter(game.mainline_moves())
    for i in range(31):
        board.push(next(moves))
    commentary_str=util_obj.commentary(board, chess.Move.from_uci('f8c5'))
    for comment in commentary_str:
        print(comment)

    print(util_obj.get_best_threat(board, stockfish))
    stockfish.close()