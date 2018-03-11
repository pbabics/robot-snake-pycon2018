from snakepit.robot_snake import RobotSnake

import random
import traceback
import queue
import sys


				
POSITION_DIRECTION = [RobotSnake.DOWN, RobotSnake.RIGHT, RobotSnake.UP, RobotSnake.LEFT] # COS
POSITION_CHANGE_X = [0, 1, 0, -1] # SIN
POSITION_CHANGE_Y = [1, 0, -1, 0] # COS


class TailChasingRobotSnake(RobotSnake):

	def __init__(self, *args):
		super().__init__(*args)

		self._planned_path = None
		self._target = None

	def scan_map(self):
		snakes = {}
		numbers = []
		obstacles = []
		for y in range(self.world.SIZE_Y):
			for x in range(self.world.SIZE_X):
				char, color = self.world[y][x]

				if char in {self.CH_TAIL, self.CH_BODY, self.CH_HEAD}:
					snake = snakes.get(color, [(y, x), 0])
					snake[1] += 1
					if char == self.CH_HEAD:
						snake[0] = (y, x)
					snakes[color] = snake
				elif char in {self.CH_STONE, self.CH_DEAD_HEAD, self.CH_DEAD_BODY, self.CH_DEAD_TAIL}:
					obstacles.append((y, x))
				elif '0' <= char <= '9': #	number
					numbers.append((y ,x, ord(char) - 48)) 

		sorted(numbers, key = lambda t: t[2])
		return snakes, numbers, obstacles


	@staticmethod
	def _manhattan_dist(start_x, start_y, end_x, end_y):
		return abs(start_x - end_x) + abs(start_y - end_y)


	def find_path(self, start_x, start_y, end_x, end_y):
		checked = set()
		q = queue.PriorityQueue()
		q.put((0, (start_y, start_x), []))
		while not q.empty():
			e = q.get()
			last_y, last_x = e[1]
			for i in range(4):
				next_x = last_x + POSITION_CHANGE_X[i]
				next_y = last_y + POSITION_CHANGE_Y[i]
				next_path = e[2] + [i]
				if not (0 <= next_y < self.world.SIZE_Y and 0 <= next_x < self.world.SIZE_X):
					continue
				if (next_y, next_x) in checked:
					continue
				checked.add((next_y, next_x))
				if next_x == end_x and next_y == end_y:
					return next_path
				if self.world[next_y][next_x][0] != self.CH_VOID:
					continue
				q.put((self._manhattan_dist(next_x, next_y, end_x, end_y) + len(next_path), (next_y, next_x), next_path))
		return None


	def _safe_next_direction(self, position_x, position_y, snakes):

		best_direction = None
		best_heuristics = None
		for i in range(4):
			next_x = position_x + POSITION_CHANGE_X[i]
			next_y = position_y + POSITION_CHANGE_Y[i]
			if not (0 <= next_y < self.world.SIZE_Y and 0 <= next_x < self.world.SIZE_X):
				continue
			if self.world[next_y][next_x][0] != self.CH_VOID:
				continue

			if not self._is_there_a_god(next_x, next_y, 8):
				continue

			min_snake_dist = 0
			mean_snake_dist = 0
			for snake in snakes.values():
				snake_x, snake_y = snake[0]
				if snake_x == position_x and snake_y == position_y:
					continue
				snake_dist = self._manhattan_dist(next_x, next_y, snake_x, snake_y)
				min_snake_dist = min(min_snake_dist, snake_dist)
				mean_snake_dist += snake_dist
			mean_snake_dist =  (mean_snake_dist / len(snakes) - 1) if snakes else 0
			heuristics = 1 + min_snake_dist * 8 + mean_snake_dist * 2
			if best_heuristics is None or best_heuristics < heuristics or (best_heuristics == heuristics and random.random() > 0.5):
				best_direction = i
				best_heuristics = heuristics
		return best_direction


	def _is_there_a_god(self, start_x, start_y, length):
		checked = set()
		q = queue.Queue()
		q.put(((start_y, start_x), []))
		while not q.empty():
			e = q.get()
			last_y, last_x = e[0]
			for i in range(4):
				next_x = last_x + POSITION_CHANGE_X[i]
				next_y = last_y + POSITION_CHANGE_Y[i]
				next_path = e[1] + [i]
				if not (0 <= next_y < self.world.SIZE_Y and 0 <= next_x < self.world.SIZE_X):
					continue
				if (next_y, next_x) in checked:
					continue
				checked.add((next_y, next_x))
				if len(e[1]) >= length:
					return True
				if self.world[next_y][next_x][0] != self.CH_VOID and not '0' <= self.world[next_y][next_x][0] <= '9':
					continue
				q.put(((next_y, next_x), next_path))
		return False


	def _harakriki_path(self, start_x, start_y):
		checked = set()
		q = queue.PriorityQueue()
		q.put((0, (start_y, start_x), []))
		while not q.empty():
			e = q.get()
			last_y, last_x = e[1]
			for i in range(4):
				next_x = last_x + POSITION_CHANGE_X[i]
				next_y = last_y + POSITION_CHANGE_Y[i]
				next_path = e[2] + [i]
				if (0 <= next_y < self.world.SIZE_Y and 0 <= next_x < self.world.SIZE_X):
					return next_path
				if (next_y, next_x) in checked:
					continue
				checked.add((next_y, next_x))
				if next_x == end_x and next_y == end_y:
					return next_path
				if self.world[next_y][next_x][0] in {self.CH_STONE, self.CH_DEAD_HEAD, self.CH_DEAD_BODY, self.CH_DEAD_TAIL}:
					return next_path
				if self.world[next_y][next_x][0] in {self.CH_HEAD, self.CH_BODY, self.CH_TAIL}:
					if self.world[next_y][next_x][1] == self.color:
						return next_path
					else:
						continue
				q.put((self._manhattan_dist(next_x, next_y, end_x, end_y) + len(next_path), (next_y, next_x), next_path))
		return None
		

	def _check_path(self, start_x, start_y):
		next_x, next_y = start_x, start_y
		for move in self._planned_path:
			if move is None:
				return False
			next_x = next_x + POSITION_CHANGE_X[move]
			next_y = next_y + POSITION_CHANGE_Y[move]
			
			if self.world[next_y][next_x][0] != self.CH_VOID and not '0' <= self.world[next_y][next_x][0] <= '9':
				return False
		return True


	def next_direction(self, initial=False):
		world = self.world

		try:
			snakes, numbers, obstacles = self.scan_map()
			(my_y, my_x), _ = snakes[self.color]

			nearest = None
			nearest_dist = None 
			#print('I am at', my_x, my_y)
			for number in numbers:
				dist = self._manhattan_dist(my_x, my_y, number[1], number[0]) 
				if dist == 0:
					continue

				#print('Number .. ', number[1], number[0], 'number: ', number[2], 'dist', dist)
				if nearest is None or (nearest_dist + nearest[2] / 2) > (dist + number[2] / 2):
					nearest = number
					nearest_dist = dist
			if nearest is not None:
				pass
				#print('Nearest .. ', nearest[1], nearest[0], 'number: ', nearest[2], 'dist', nearest_dist)

			if not self._is_there_a_god(my_x, my_y, 5):
				self._planned_path = self._harakriki_path(my_x, my_y)
				print('Going harakiri :(')
				self._target = None
			elif nearest is not None:

				if self._planned_path is not None and self._planned_path and self._target:
					if not self._check_path(my_x, my_y):
						self._planned_path = None

				if self._target is not None:
					target_dist = self._manhattan_dist(my_x, my_y, self._target[1], self._target[0])
					print('Checking against nearest, target: ', target_dist,  'nearest: ', nearest_dist)
					if target_dist > nearest_dist:
						self._planned_path = None

				if self._planned_path is None or not self._planned_path or not self._target:
					self._planned_path = self.find_path(my_x, my_y, nearest[1], nearest[0])
					self._target = nearest

			if self._planned_path is None or not self._planned_path:
				self._planned_path = [self._safe_next_direction(my_x, my_y, snakes)]

			if self._planned_path and self._planned_path[0] is not None:
				self.current_direction = POSITION_DIRECTION[self._planned_path[0]]
				self._planned_path = self._planned_path[1:]
			if not self._planned_path:
				self._target = None

			self.changed_direction = True
			return self.current_direction
		except KeyboardInterrupt:
			sys.exit(1)
		except:
			traceback.print_exc()
