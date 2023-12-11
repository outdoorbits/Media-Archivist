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

from datetime import datetime
import os
import shutil
import subprocess
import sys
import time

import lib_database
import lib_setup

class archivist(object):

	def __init__(self, ConfigFilePath):
		# objects
		self.__setup			= lib_setup.setup(ConfigFilePath)

		self.__conf_SOURCE_DIR								= self.__setup.get_val('conf_SOURCE_DIR')
		self.__conf_TARGET_DIR								= self.__setup.get_val('conf_TARGET_DIR')

		if not os.path.isdir(self.__conf_SOURCE_DIR):
			sys.exit(f"Please edit the config file '{ConfigFilePath}': conf_SOURCE_DIR not set correctly")

		if not os.path.isdir(self.__conf_TARGET_DIR):
			sys.exit(f"Please edit the config file '{ConfigFilePath}': conf_TARGET_DIR not set correctly")

		self.__conf_MOVE_FILES								= self.__setup.get_val('conf_MOVE_FILES')

		self.__conf_SET_USER								= self.__setup.get_val('conf_SET_USER')
		self.__conf_SET_GROUP								= self.__setup.get_val('conf_SET_GROUP')
		self.__conf_SET_PERMISSIONS							= self.__setup.get_val('conf_SET_PERMISSIONS')

		self.__conf_FILE_EXTENSIONS_LIST_WEB_IMAGES			= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_WEB_IMAGES').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_HEIC				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_HEIC').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_RAW				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_RAW').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_TIF				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_TIF').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_VIDEO				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_VIDEO').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_AUDIO				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_AUDIO').split(';')

		self.__conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES	= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_HEIC			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_HEIC')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_RAW			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_RAW')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_TIF			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_TIF')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO')

		self.__conf_DB_MIN_IDLE_SEC					= self.__setup.get_val('conf_DB_MIN_IDLE_SEC')
		self.__conf_MIN_MEDIA_FILE_AGE_SEC			= self.__setup.get_val('conf_MIN_MEDIA_FILE_AGE_SEC')

		self.__conf_EXEC_SCRIPT_IF_SUCCESS			= self.__setup.get_val('conf_EXEC_SCRIPT_IF_SUCCESS')


		self.media_extensions	= 	self.__conf_FILE_EXTENSIONS_LIST_WEB_IMAGES + \
									self.__conf_FILE_EXTENSIONS_LIST_HEIC + \
									self.__conf_FILE_EXTENSIONS_LIST_RAW + \
									self.__conf_FILE_EXTENSIONS_LIST_TIF + \
									self.__conf_FILE_EXTENSIONS_LIST_VIDEO + \
									self.__conf_FILE_EXTENSIONS_LIST_AUDIO

		self.database_path	= os.path.join(self.__conf_SOURCE_DIR,'archivist.sqlite3')

		# be sure there is no active archivist prozess using the same database
		if os.path.isfile(self.database_path):
			if (time.time() - os.path.getmtime(self.database_path)) < self.__conf_DB_MIN_IDLE_SEC:
				sys.exit('archivist already working.')

		self.db	= lib_database.database(self.database_path)

	def run(self):
		DirsCreated		= 0
		FilesProcessed	= 0

		print(f'\nArchivist: Starting transfer from {self.__conf_SOURCE_DIR} to {self.__conf_TARGET_DIR} ...')

		# create list of valid extensions
		AllowedExtensionsOptions	= []
		for AllowedExtension in self.media_extensions:
			if AllowedExtensionsOptions:
				AllowedExtensionsOptions	+= ["-o"]

			AllowedExtensionsOptions	+= ["-iname", f"'*.{AllowedExtension}'"]

		Command	= f"find '{self.__conf_SOURCE_DIR}' -type f \( {' '.join(AllowedExtensionsOptions)} \)"

		MediaFilePathList	= subprocess.check_output(Command,shell=True).decode().strip().split('\n')
		MediaFilePathList	= list(filter(None, MediaFilePathList)) # remove None items

		for MediaFilePath in MediaFilePathList:

			if not self.db.dbMediaFileKnown(MediaFilePath):

				print(f"\nFile: {MediaFilePath}")

				while time.time() - os.path.getmtime(MediaFilePath) < self.__conf_MIN_MEDIA_FILE_AGE_SEC:
					print('.')
					time.sleep(1)

				FileDateDict	= self.getFileDate(MediaFilePath)

				# target path
				TargetPath	= os.path.join(
					self.__conf_TARGET_DIR,
					f"{FileDateDict['Y']}",
					f"{FileDateDict['Y']}-{FileDateDict['M']}",
					f"{FileDateDict['Y']}-{FileDateDict['M']}-{FileDateDict['D']}"
				)

				# special subfolders
				MediaFileExt	= os.path.splitext(MediaFilePath)[1][1:].lower()

				if self.__conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES:
					if MediaFileExt in (extension.lower() for extension in self.__conf_FILE_EXTENSIONS_LIST_WEB_IMAGES):
						TargetPath	= os.path.join(TargetPath, self.__conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES)

				if self.__conf_FILE_EXTENSIONS_SUBFOLDER_HEIC:
					if MediaFileExt in (extension.lower() for extension in self.__conf_FILE_EXTENSIONS_LIST_HEIC):
						TargetPath	= os.path.join(TargetPath, self.__conf_FILE_EXTENSIONS_SUBFOLDER_HEIC)

				if self.__conf_FILE_EXTENSIONS_SUBFOLDER_RAW:
					if MediaFileExt in (extension.lower() for extension in self.__conf_FILE_EXTENSIONS_LIST_RAW):
						TargetPath	= os.path.join(TargetPath, self.__conf_FILE_EXTENSIONS_SUBFOLDER_RAW)

				if self.__conf_FILE_EXTENSIONS_SUBFOLDER_TIF:
					if MediaFileExt in (extension.lower() for extension in self.__conf_FILE_EXTENSIONS_LIST_TIF):
						TargetPath	= os.path.join(TargetPath, self.__conf_FILE_EXTENSIONS_SUBFOLDER_TIF)

				if self.__conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO:
					if MediaFileExt in (extension.lower() for extension in self.__conf_FILE_EXTENSIONS_LIST_VIDEO):
						TargetPath	= os.path.join(TargetPath, self.__conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO)

				if self.__conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO:
					if MediaFileExt in (extension.lower() for extension in self.__conf_FILE_EXTENSIONS_LIST_AUDIO):
						TargetPath	= os.path.join(TargetPath, self.__conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO)

				# create target path
				print(f"TargetPath: {TargetPath}")

				if not os.path.isdir(TargetPath):
					DirsCreated	+= 1
					os.makedirs(TargetPath, exist_ok=True)

				# target file name
				TargetFileName	= os.path.join(TargetPath,os.path.basename(MediaFilePath))

				if not os.path.isfile(TargetFileName):
					FilesProcessed	+= 1
					# transfer
					if self.__conf_MOVE_FILES:
						print(f"move '{MediaFilePath}' to '{FileDateDict['Y']}-{FileDateDict['M']}-{FileDateDict['D']}'")
						shutil.move(MediaFilePath, TargetFileName)
					else:
						print(f"copy '{MediaFilePath}' to '{FileDateDict['Y']}-{FileDateDict['M']}-{FileDateDict['D']}'")
						shutil.copy(MediaFilePath, TargetFileName)

					if FileDateDict['Date missing']:
						print("writing 'Create Date' into media file")
						CreateDate	= f"{FileDateDict['Y']}:{FileDateDict['M']}:{FileDateDict['D']} {FileDateDict['h']}:{FileDateDict['m']}:{FileDateDict['s']}"
						Command	= ['exiftool', '-overwrite_original', f"-CreateDate='{CreateDate}'",TargetFileName]
						subprocess.run(Command)

				self.db.dbInsertMediaFile(MediaFilePath)

		print(f"\n * {FilesProcessed} files processed.")
		print(f" * {DirsCreated} new folders created.")

		if (FilesProcessed > 0) or (DirsCreated > 0):

			if self.__conf_SET_USER and self.__conf_SET_GROUP:
				print(f"Setting ownership to {self.__conf_SET_USER}:{self.__conf_SET_GROUP} ...")
				subprocess.run(['chown', '-R', f"{self.__conf_SET_USER}:{self.__conf_SET_GROUP}", self.__conf_TARGET_DIR])

			if self.__conf_SET_PERMISSIONS:
				print(f'Setting permissions to {self.__conf_SET_PERMISSIONS} ...')
				subprocess.run(['chmod', '-R', f"{self.__conf_SET_PERMISSIONS}", self.__conf_TARGET_DIR])

			if self.__conf_EXEC_SCRIPT_IF_SUCCESS:
				try:
					subprocess.run(self.__conf_EXEC_SCRIPT_IF_SUCCESS, shell=True)
				except:
					print('Your script defined in conf_EXEC_SCRIPT_IF_SUCCESS raised an error.')

		print ('\nFinished.')

	def getFileDate(self,MediaFilePath):
		try:
			EXIF_List_Raw	= subprocess.check_output(f"exiftool '{MediaFilePath}' | grep ':'",shell=True).decode().strip().split('\n')
		except:
			EXIF_List_Raw	= []

		EXIF_List	= {}
		for EXIF_Raw in EXIF_List_Raw:

			try:
				EXIF_Field, EXIF_Value	= EXIF_Raw.split(':',1)
			except:
				EXIF_Field	= EXIF_Raw
				EXIF_Value	= ''

			EXIF_Field	= EXIF_Field.strip()
			EXIF_Value	= EXIF_Value.strip()

			EXIF_List[EXIF_Field]	= EXIF_Value

		## date
		if 'Create Date' in EXIF_List:
			WriteEXIFCreateDate	= False
		else:
			WriteEXIFCreateDate	= True

			AlternativeDateTags	= [
				'Create Date',
				'Creation Date',
				'Media Create Date',
				'Date Time Original',
				'File Modification Date Time',
				'File Access Date Time'
			]

			Alternative_Spacers	= [
				' ',
				'_',
				'-',
				''
			]

			for AlternativeDateTag in AlternativeDateTags:
				for Alternative_Spacer in Alternative_Spacers:
					if ('Create Date' not in EXIF_List) and (AlternativeDateTag.replace(' ', Alternative_Spacer) in EXIF_List):
						if self.CreateDateCheck(EXIF_List[AlternativeDateTag.replace(' ', Alternative_Spacer)]):
							EXIF_List['Create Date']	= EXIF_List[AlternativeDateTag.replace(' ', Alternative_Spacer)]

			if 'Create Date' not in EXIF_List:
				print(f'MediaFilePath: {MediaFilePath} xxx')
				EXIF_List['Create Date']	= datetime.fromtimestamp(os.path.getmtime(MediaFilePath)).strftime("%Y:%m:%d:%H:%M:%S")

		FileDate	= EXIF_List['Create Date']

		del EXIF_List

		FileDateDict					= self.getFileDateDict(FileDate)
		FileDateDict['Date missing']	= WriteEXIFCreateDate

		return(FileDateDict)

	def CreateDateCheck(self,DateTimeStr):
		FileDateDict	= self.getFileDateDict(DateTimeStr)

		result	= (FileDateDict['Y'] != '0000') and (FileDateDict['M'] != '00') and (FileDateDict['D'] != '00')

		return(result)

	def getFileDateDict(self,DateTimeStr):
		FileDateDict	= {
			'Y':			'0000',
			'M':			'00',
			'D':			'00',
			'h':			'00',
			'm':			'00',
			's':			'00',
			'Date missing':	True
		}

		FileDateReplacings	= [
			'_',
			'-',
			' ',
			'.',
			',',
			'+'
		]

		for FileDateReplacing in FileDateReplacings:
			DateTimeStr	= DateTimeStr.replace(FileDateReplacing, ':')

		dateList	= DateTimeStr.split(':')

		if len(dateList) >= 3:
			FileDateDict['Y']	= dateList[0]
			FileDateDict['M']	= dateList[1]
			FileDateDict['D']	= dateList[2]

		if len(dateList) >= 4:
			FileDateDict['h']	= dateList[3]

		if len(dateList) >= 5:
			FileDateDict['m']	= dateList[4]

		if len(dateList) >= 6:
			FileDateDict['s']	= dateList[5]

		return(FileDateDict)

	def clean(self):
		if self.__conf_SOURCE_DIR in ['', '/']:
			sys.exit(f"--clean can not work if conf_SOURCE_DIR is '{self.__conf_SOURCE_DIR}'.")

		print(os.path.join(self.__conf_SOURCE_DIR))
		print(f"Wipe source folder '{os.path.join(self.__conf_SOURCE_DIR,'*')}'")
		if input("To proceed type 'YES': ") == 'YES':
			print('Starting in 5 seconds ...')
			time.sleep(5)

			shutil.rmtree(self.__conf_SOURCE_DIR)
			os.makedirs(self.__conf_SOURCE_DIR, exist_ok=True)

			print('All done.')


if __name__ == "__main__":
	ConfigFilePath	= ''
	CleanUp			= False

	for arg in sys.argv:
		# --config=...
		if arg[0:9] == '--config=':
			try:
				ConfigFilePath	= arg.split('=',1)[1]
			except:
				pass

			ConfigFilePath	= ConfigFilePath.strip(" '")
		elif arg == '--clean':
			CleanUp	= True

	if not ConfigFilePath:
		sys.exit('Please define a config file (existing or to create) by argument --config=/abc/archivist.conf')

	if CleanUp:
		archivist(ConfigFilePath).clean()
	else:
		archivist(ConfigFilePath).run()
