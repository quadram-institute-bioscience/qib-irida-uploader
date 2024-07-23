#Configs for huey
from huey import PriorityRedisHuey, SqliteHuey

huey = SqliteHuey(filename='queue.db')
#TODO: switch password value to ENV
# huey = PriorityRedisHuey('covid', host='localhost',
#                          password='pAE7x8pcUKk6QjPg')
huey.immediate = True
