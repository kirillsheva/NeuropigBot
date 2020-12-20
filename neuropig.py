import asyncio
import logging
import threading
import time
from checkers import game
import aiohttp
from player import pathFinder

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO
    )
    _loop = asyncio.get_event_loop()
    thread = threading.Thread(target=pathFinder(_loop)._s_t)
    thread.start()
    _loop.run_forever()

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
            self._player = {'color': res['color'], 'token': res['token']}

    async def _send_move_to_srv(self, move):
        json = {'move': move}
        headers = {'Authorization': f'Token {self._player["token"]}'}
        async with self._session.post(
                f'{self._api_url}/move',
                json=json,
                headers=headers
        ):
            logging.info(f'Player Нейросвиня made move {move}')

    async def _get_game(self):
        async with self._session.get(f'{self._api_url}/game') as resp:
            return (await resp.json())['data']

    async def _play_game(self):
        current_game_progress = await self._get_game()
        is_finished = current_game_progress['is_finished']
        is_started = current_game_progress['is_started']

        while is_started and not is_finished:

            if current_game_progress['whose_turn'] != self._player['color']:
                current_game_progress = await self._get_game()
                is_finished = current_game_progress['is_finished']
                is_started = current_game_progress['is_started']
                await asyncio.sleep(0.1)
                continue


            last_move = current_game_progress['last_move']
            if last_move and last_move['player'] != self._player['color']:
                for move in last_move['last_moves']:
                    self._game.move(move)


            player_turn = 1 if current_game_progress['whose_turn'] == 'RED' else 2
            start = time.time()
            move = pathFinder.next_move(self._game, 4, player_turn, False)
            end = time.time()
            self._elapsed_time.append(end - start)

            if not move:
                break
            self._game.move(move)

            await self._send_move_to_srv(move)

            current_game_progress = await self._get_game()
            is_finished = current_game_progress['is_finished']
            is_started = current_game_progress['is_started']

