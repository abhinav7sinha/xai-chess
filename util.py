import chess
import chess.pgn as pgn
import chess.engine
import numpy as np
from copy import deepcopy

class Util():
    '''
    Util class
    '''

    def __init__(self):
        self.game_pgn = open("famous-games/anderssen_kieseritzky_1851.pgn")
        self.game=pgn.read_game(self.game_pgn)
        self.piece_score = {'P': 1, 'p': 1, 'N': 3, 'n': 3, 'B': 3, 'b': 3, 'R': 5, 'r': 5,\
            'Q': 9, 'q': 9, 'K': 10, 'k': 10}
        self.central_squares=list(range(18,22))+list(range(26,30))+list(range(34,38))+\
            list(range(42,50))
    
    def commentary(self, board, move):
        '''
        1. get commentary for attacked pieces
        2. get commentary for defended pieces
        '''
        # TODO: commentary for positional chess - rook on open file
        # rof=[]
        
        commentary_str=[]
        
        # commentary for an attacked piece
        attacks=[]
        # commentary for a defended piece
        defends=[]
        # commentary for positional chess - bishop on long diagonal
        bld=[]
        # commentary for positional chess - knight on central square
        kcs=[]
        # commentary for positional chess - queen on central square
        qcs=[]
        # commentary for positional chess - activate pieces
        activate=[]
        
        old_attacked_squares=board.attacks(move.from_square)
        old_unattacked_squares = list(set(list(range(64)))-set(board.attacks(move.from_square)))
        new_attacked_squares=self.get_critical_controlled_squares(board, move)
        print('sqs:', [chess.square_name(sq) for sq in (set(old_unattacked_squares) & set(new_attacked_squares))])
        for square in (set(old_unattacked_squares) & set(new_attacked_squares)):
            if board.color_at(square) is not board.turn:
                attacks.append(f'{board.piece_at(move.from_square)} attacks {board.piece_at(square)} at {chess.square_name(square)}')
            elif board.color_at(square) is board.turn:
                defends.append(f'{board.piece_at(move.from_square)} defends {board.piece_at(square)} at {chess.square_name(square)}')
        
        if self.check_bishop_ld(board, move):
            bld.append('Places Bishop on long diagonal')
        
        if self.check_activate_pieces(board, move):
            activate.append('Activates piece(s)')
            
        if self.check_knight_central(board, move):
            kcs.append('Places Knight on central square')
        
        if self.check_queen_central(board, move):
            qcs.append('Places Queen on central square')
        
        commentary_str=attacks+defends+activate+bld+kcs+qcs
        return commentary_str

    def get_critical_controlled_squares(self, board, move):
        '''
        takes board object and a move object as input
        returns a list of unique controlled squares wrt that specific move
        '''
        board.push(move)
        attacked_squares=board.attacks(move.to_square)
        critical_att_squares=[]
        for sqaure in (set(attacked_squares) & set(self.get_all_critical_squares(board))):
            # intersection of 2 sets -> attacked squares and all critical squares
            critical_att_squares.append(sqaure)
        board.pop()
        return critical_att_squares

    def get_all_critical_squares(self, board):
        '''
        takes board object as input
        returns a list of unique critical squares -> 
        critical_occupied_squares+critical_empty_squares+hanging_squares
        '''
        return list(
            set(
                self.check_critical_occupied_squares(board)+\
                    self.check_critical_empty_squares(board)+\
                        self.check_hanging_squares(board)))

    def check_critical_occupied_squares(self, board):
        '''
        takes board object as input
        uses the criterion = (piece score) * (number of attackers) to compute the most critical squares
        returns a list of occupied squares with highest criterion
        '''
        critical_squares={}
        for sq in range(64):
            # count number of pieces attacking a given square
            count=0
            if board.piece_at(sq):
                count=len(board.attackers(not board.color_at(sq), sq))
                critical_squares[sq]=self.piece_score[board.piece_at(sq).symbol()]*count
    #     for sq, count in critical_squares.items():
    #         print(f'{chess.square_name(sq)}: {count}')
        max_value = max(critical_squares.values())
        return [key for key, value in critical_squares.items() if value == max_value]

    def check_critical_empty_squares(self, board):
        '''
        takes board object as input
        returns a list of empty squares with the highest number of attackers
        '''
        critical_squares={}
        for sq in range(64):
            # count number of pieces attacking a given square
            count=0
            if not board.piece_at(sq):
                count=len(board.attackers(not board.turn, sq))
                critical_squares[sq]=count
    #     for sq, count in critical_squares.items():
    #         print(f'{chess.square_name(sq)}: {count}') 
        max_value = max(critical_squares.values())
        return [key for key, value in critical_squares.items() if value == max_value]

    def check_hanging_squares(self, board, color=None):
        '''
        takes board object, player color as input
        returns a list of squares containing hanging pieces of given color
        '''
        hanging_squares=[]
        if color is not None:
            for sq in range(64):
                if board.piece_at(sq) and board.color_at(sq)==color:
                    if self.is_attacked(board, sq):
                        hanging_squares.append(sq)
        else:
            for sq in range(64):
                if board.piece_at(sq):
                    if self.is_attacked(board, sq):
                        hanging_squares.append(sq)        
        return hanging_squares

    def check_bishop_ld(self, board, move):
        '''
        check is bishop was put on long diagonal from a passive position
        '''
        diag_a1_h8=list(range(0,64,9))
        diag_a2_g8=list(range(8,63,9))
        diag_b1_h7=list(range(1,56,9))
        diag_h1_a8=list(range(7,57,7))
        diag_g1_a7=list(range(6,49,7))
        diag_h2_b8=list(range(15,58,7))
        all_diags=diag_a1_h8+diag_a2_g8+diag_b1_h7+diag_h1_a8+diag_g1_a7+diag_h2_b8
        if board.piece_at(move.from_square).symbol().lower()=='b':
            if move.from_square not in all_diags and move.to_square in all_diags:
                return True
        return False
            
    def check_activate_pieces(self, board, move):
        '''
        takes board object and move as input
        returns True if the move leads to +5 more controlled squares on the board
        '''
        old_control_count=0
        for i in range(64):
            old_control_count+=self.is_control(board, board.turn, i)
        new_control_count=0
        board.push(move)
        for i in range(64):
            new_control_count+=self.is_control(board, not board.turn, i)
        board.pop()
        if new_control_count>old_control_count+5:
            return True
        else:
            return False
                        
    def check_rook_of(self, board, move):
        '''
        TODO: check if rook was placed on open file
        '''
        pass

    def check_knight_central(self, board, move):
        '''
        check if knight was placed on a central square
        '''
        if board.piece_at(move.from_square).symbol().lower()=='n':
            if move.from_square not in self.central_squares and move.to_square in self.central_squares:
                return True
        return False

    def check_queen_central(self, board, move):
        '''
        check if queen was placed on a central sqaure
        '''
        if board.piece_at(move.from_square).symbol().lower()=='q':
            if move.from_square not in self.central_squares and move.to_square in self.central_squares:
                return True
        return False

    def check_response_against_threat():
        '''
        check if a new move responds to a threat by counterattacking or defending
        '''
        pass

    def is_attacked(self, board, target_square):
        """
        takes board object and a target square as input
        returns True if the piece at that target square is attacked else False
        if there is no piece at that target square - return False
        """
        target_piece=board.piece_at(target_square)
        attacker_color=not target_piece.color
        t_piece_rank=np.argwhere(self.get_pieces([target_piece])==1).item()
        
        if not self.get_attackers(board, attacker_color, target_square):
            return False
        
        t_attacker_rank=np.min(np.argwhere(self.get_pieces(self.get_attackers(board, attacker_color, target_square))==1).flatten())
        # print(f't_piece_rank: {t_piece_rank}, t_attacker_rank: {t_attacker_rank}')
        if t_piece_rank>t_attacker_rank:
            return True
        elif self.check_control(board, attacker_color, target_square)==1: 
            return True
        else:
            return False

    def get_pieces(self, piece_list):
        """
        piece: P, N, B, R, Q, K
        index: 0, 1, 1, 2, 3, 4
        """
        new_piece_arr=np.zeros(5)
        for piece in piece_list:
            piecetype = piece.piece_type-1 if piece.piece_type<3 else piece.piece_type-2
            new_piece_arr[piecetype]+=1
        return new_piece_arr
    
    def get_attackers(self, board, player, target_square):
        attacking_pieces=[]
        for square in board.attackers(player, target_square):
            attacking_pieces.append(board.piece_at(square))
        return attacking_pieces
    
    def check_control(self, board, player, target_square):
        # get white attackers
        defenders = self.get_pieces(self.get_attackers(board, player, target_square))
        attackers = self.get_pieces(self.get_attackers(board, not player, target_square))
        
        control_list=defenders-attackers
        prefixsum=0
        for i in range(len(control_list)):
            prefixsum+=control_list[i]
            if np.abs(prefixsum)>1:
                return np.sign(prefixsum)
        return np.sign(prefixsum)

    def is_control(self, board, player, target_square):
        '''
        takes boolean player and target_square as input
        returns 1 if target_square is controlled by player
        returns 0 if target_square is contested by both players
        returns -1 if target_square is controlled by opponent
        '''
        if len(board.attackers(player, target_square))>len(board.attackers(not player, target_square)):
            return 1
        elif len(board.attackers(player, target_square))==len(board.attackers(not player, target_square)):
            return 0
        else:
            return -1
    
    def set_engine(self, UCI_Elo=3000):
        '''
        take UCI_Elo as input
        returns a SimpleEngine object
        '''
        stockfish = chess.engine.SimpleEngine.popen_uci(
            r"/opt/homebrew/Cellar/stockfish/14.1/bin/stockfish")
        if UCI_Elo is not None:
            stockfish.configure({"UCI_LimitStrength": True, "UCI_Elo": UCI_Elo})
        return stockfish

    def fen_flip_turn(self, fen_str):
        '''
        takes a FEN string as input
        flips the player turn and returns the flipped FEN string
        '''
        x=fen_str.split()
        x[1]='w' if x[1]=='b' else 'b'
        return ' '.join(x)

    def get_best_threat(self, board, engine):
        '''
        takes board object and a SimpleEngine object as input
        returns the engine evaluated best threat move in the position
        '''
        eng_board=deepcopy(board)
        eng_fen=self.fen_flip_turn(eng_board.fen())
        eng_board.set_fen(eng_fen)
        eng_move=engine.play(eng_board, chess.engine.Limit(time=1))
        # if you want to return uci string use eng_move.move.uci()
        return eng_move.move