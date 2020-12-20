import asyncio
import logging
import time
import aiohttp
from checkers import game
from copy import deepcopy

from checkers.game import Game


def _get_move(game: Game, depth, maximize):
    passing_move = None
    alfa = getMinNode
    for move in game.get_possible_moves():
        new_game = deepcopy(game)
        new_game.move(move)
        beta = -_minimax_a_b(new_game, depth - 1, new_game.whose_turn(), maximize, getMinNode, getMaxNode)
        if alfa < beta:
            alfa = beta
            passing_move = move
    return passing_move



def _minimax_a_b(game: Game, depth, current_p, maximize, alpha, beta):
    if depth == 0:
        return get_possible_options(game, maximize)
    if current_p != maximize:
        current_top_node = getMaxNode


        for move in game.get_possible_moves():
            game_simulation = deepcopy(game)
            game_simulation.move(move)


            current_top_node = min(current_top_node, _minimax_a_b(game_simulation, depth - 1, game_simulation.whose_turn(), maximize, alpha, beta))
            beta = min(beta, current_top_node)
            if beta <= alpha:
                break
        return current_top_node
    else:
        current_top_node = getMinNode


        for move in game.get_possible_moves():
            game_simulation = deepcopy(game)
            game_simulation.move(move)


            current_top_node = max(current_top_node, _minimax_a_b(game_simulation, depth - 1, game_simulation.whose_turn(), maximize, alpha, beta))
            alpha = max(alpha, current_top_node)
            if alpha >= beta:
                break
        return current_top_node

def get_possible_options(game: Game, current_player):
    current_squares = game.board.searcher.get_pieces_by_player(current_player)
    opposite_squares = game.board.searcher.get_pieces_by_player(1 if current_player == 2 else 2)
    current_squares = len(current_squares)
    opposite_squares = len(opposite_squares)
    if current_player==2:
        return opposite_squares
    else:
        return current_squares

getMaxNode= float('+inf')
getMinNode= float('-inf')

class pathFinder:
    def __init__(self, loop):
        self._api_url = 'http://localhost:8081'
        self._loop = loop
        self._session = aiohttp.ClientSession()
        self._player = {}
        self._game = game.Game()
        self._last_move = None
        self._elapsed_time = []

    async def _prepare_player(self):
        async with self._session.post(
                f'{self._api_url}/game',
                params={'team_name': 'Нейросвиня'}
        ) as resp:
            res = (await resp.json())['data']
            self._player = {
                'color': res['color'],
                'token': res['token']
            }

    async def _get_game(self):
        async with self._session.get(f'{self._api_url}/game') as resp:
            return (await resp.json())['data']

    async def _make_move(self, move):
        json = {'move': move}
        headers = {'Authorization': f'Token {self._player["token"]}'}
        async with self._session.post(
                f'{self._api_url}/move',
                json=json,
                headers=headers
        ):
            logging.info(f'Move coordinates {move}')


    async def _play_game(self):
        current_game_progress = await self._get_game()

        is_started = current_game_progress['is_started']

        while is_started:

            if current_game_progress['whose_turn'] != self._player['color']:
                current_game_progress = await self._get_game()

                is_started = current_game_progress['is_started']
                await asyncio.sleep(0.1)
                continue


            last_move = current_game_progress['last_move']
            if last_move and last_move['player'] != self._player['color']:
                for move in last_move['last_moves']:
                    self._game.move(move)


            current_p_turn = 1 if current_game_progress['whose_turn'] == 'RED' else 2
            start = time.time()
            move = _get_move(self._game, 1, current_p_turn)
            end = time.time()
            self._elapsed_time.append(end - start)

            if not move:
                break
            self._game.move(move)

            await self._make_move(move)

            current_game_progress = await self._get_game()
            is_started = current_game_progress['is_started']

    def _s_t(self):
        asyncio.run_coroutine_threadsafe(self.start(), self._loop)

    async def start(self):
            logging.info('Waiting for player')
            await asyncio.ensure_future(self._prepare_player())
            logging.info('Players initialized')

            logging.info(f'Player: {self._player}')

            await self._play_game()

            logging.info('Game finished')
            last_game_progress = await self._get_game()
            logging.info(str(last_game_progress))
            await self._session.close()

