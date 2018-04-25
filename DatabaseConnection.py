import math as math
import numpy as np
from operator import itemgetter
import pymongo
import json




class DatabaseConnection:
	""" DatabaseConnection class to talk with MongoDB """

	def __init__(self, parameters):
		self.__conn_ok = False
		self.__mongo_host = str(parameters["mongodb"]["server"])
		self.__mongo_port = int(parameters["mongodb"]["port"])
		self.__mongodb    = str(parameters["mongodb"]["db"])
		self.__mongo_collection = str(parameters["mongodb"]["collection"])
		self.__mongo_user = str(parameters["mongodb"]["username"])
		self.__mongo_pass = str(parameters["mongodb"]["password"])

		uri = 'mongodb://' + self.__mongo_user + ':' + self.__mongo_pass + '@' + self.__mongo_host + ':' + str(self.__mongo_port) + '/' + self.__mongodb
		self.__client = pymongo.MongoClient(uri)

		#self.__conn_ok = self.__client[self.__mongodb].authenticate(self.__mongo_user, self.__mongo_pass, mechanism='MONGODB-CR')

		# if(self.__conn_ok == False):
		# 	print "ERROR"
		# 	exit(-1)
		# else:
		# 	print "connection OK"

	def save(self, msg, db=None, coll=None):
		if db is None:
			tmp_db = self.__mongodb
		else:
			tmp_db = db

		if coll is None:
			tmp_coll = self.__mongo_collection
		else:
			tmp_coll = coll
		
		self.__conn = self.__client[tmp_db][tmp_coll]

		self.__conn.insert_one(msg)


	def find(self, json=None, db=None, coll=None):
		if json is not None:
			cur =self.__conn.find(json)
		else:
			cur =self.__conn.find()
		return cur

	def find_one(self, json, db=None, coll=None):
		cur =self.__conn.find_one(json)
		return cur
		
# data = {"mongodb":{"username":"lazlazari", "password":"la787776", "port":"29415", "db":"video_converter","collection":"test","server":"ds229415.mlab.com"}}
#dbcon = DatabaseConnection(data)