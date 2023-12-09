#!/usr/bin/env python

# Author: Stefan Saam, github@saams.de

#######################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#######################################################################

import os
import sqlite3
import subprocess


class database(object):
	def __init__(self, db_path):


		self.db_path	= db_path

		self.__con	= sqlite3.connect(self.db_path)
		self.__cur	= self.__con.cursor()

		self.__dbUpgrade()

	def __dbUpgrade(self):
		# define database, append lines for updates, do not change existing lines!
		dbCreateArray	= []

		dbCreateArray.append("create table CONFIG (VERSION integer);")
		dbCreateArray.append("insert into CONFIG (VERSION) values (0);")
		dbCreateArray.append("create table mediafiles (ID integer primary key autoincrement);")
		dbCreateArray.append("alter table mediafiles add column SourcePath text;")
		dbCreateArray.append("create unique index SourcePath_idx on mediafiles(SourcePath);")
		#dbCreateArray.append("alter table mediafiles add column ... text;")

		# try to get version of existing db
		dbVersion	= -1
		if os.path.isfile(self.db_path):
			try:
				res = self.__cur.execute("select VERSION from CONFIG ORDER BY VERSION DESC LIMIT 1;").fetchone()
				if res[0]:
					dbVersion	= res[0]
			except:
				dbVersion	= -1


		# update if necessary
		if dbVersion < len(dbCreateArray):
			i = 0
			for Command in dbCreateArray:
				i	+= 1
				if i > dbVersion:
					if Command != "DEPRECATED":
						#print(Command)
						self.__cur.execute(Command)

			self.dbExecute(f"update CONFIG set VERSION = {i};")

	def dbExecute(self,Command):
		try:
			self.__cur.execute(Command)
			self.__con.commit()
			return(True)
		except:
			return(False)

	def dbSelect(self,Command):
		try:
			return(self.__cur.execute(Command).fetchall())
		except:
			return(False)

	def dbMediaFileKnown(self, FilePath):
		return(self.dbSelect(f"select SourcePath from mediafiles where SourcePath='{FilePath}'"))


	def dbInsertMediaFile(self,SourcePath):
		#insert data
		Command	= f"insert into mediafiles (SourcePath) values ('{SourcePath}');"

		self.dbExecute(Command)



if __name__ == "__main__":
	pass
