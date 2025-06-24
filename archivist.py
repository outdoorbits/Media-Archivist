#!/usr/bin/env python3

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
import lib_mail
import lib_media
import lib_setup

class archivist(object):

	def __init__(self, ConfigFilePath):

		# config
		self.ConfigFilePath		= ConfigFilePath

		# objects
		self.__setup			= lib_setup.setup(ConfigFilePath)

		self.__conf_SOURCE_DIR								= self.__setup.get_val('conf_SOURCE_DIR')
		self.__conf_TARGET_DIR								= self.__setup.get_val('conf_TARGET_DIR')

		if not os.path.isdir(self.__conf_SOURCE_DIR):
			sys.exit(f"Please edit the config file '{ConfigFilePath}': conf_SOURCE_DIR not set correctly")

		if not os.path.isdir(self.__conf_TARGET_DIR):
			sys.exit(f"Please edit the config file '{ConfigFilePath}': conf_TARGET_DIR not set correctly")

		self.__conf_MOVE_FILES								= self.__setup.get_val('conf_MOVE_FILES')
		self.__conf_RENAME_FILES							= self.__setup.get_val('conf_RENAME_FILES')
		self.__conf_OVERWRITE								= self.__setup.get_val('__conf_OVERWRITE')

		self.__conf_SET_USER								= self.__setup.get_val('conf_SET_USER')
		self.__conf_SET_GROUP								= self.__setup.get_val('conf_SET_GROUP')
		self.__conf_SET_PERMISSIONS							= self.__setup.get_val('conf_SET_PERMISSIONS')

		self.__conf_FILE_EXTENSIONS_LIST_WEB_IMAGES			= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_WEB_IMAGES').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_HEIC				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_HEIC').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_RAW				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_RAW').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_TIF				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_TIF').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_VIDEO				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_VIDEO').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_AUDIO				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_AUDIO').split(';')
		self.__conf_FILE_EXTENSIONS_LIST_GEO				= self.__setup.get_val('conf_FILE_EXTENSIONS_LIST_GEO').split(';')

		self.__conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES	= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_HEIC			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_HEIC')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_RAW			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_RAW')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_TIF			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_TIF')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO')
		self.__conf_FILE_EXTENSIONS_SUBFOLDER_GEO			= self.__setup.get_val('conf_FILE_EXTENSIONS_SUBFOLDER_GEO')

		self.__conf_DB_MIN_IDLE_SEC					= self.__setup.get_val('conf_DB_MIN_IDLE_SEC')
		self.__conf_MIN_MEDIA_FILE_AGE_SEC			= self.__setup.get_val('conf_MIN_MEDIA_FILE_AGE_SEC')

		self.__conf_EXEC_SCRIPT_IF_SUCCESS			= self.__setup.get_val('conf_EXEC_SCRIPT_IF_SUCCESS')


		self.media_extensions	= 	self.__conf_FILE_EXTENSIONS_LIST_WEB_IMAGES + \
									self.__conf_FILE_EXTENSIONS_LIST_HEIC + \
									self.__conf_FILE_EXTENSIONS_LIST_RAW + \
									self.__conf_FILE_EXTENSIONS_LIST_TIF + \
									self.__conf_FILE_EXTENSIONS_LIST_VIDEO + \
									self.__conf_FILE_EXTENSIONS_LIST_AUDIO + \
									self.__conf_FILE_EXTENSIONS_LIST_GEO

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

		FilesAtTarget	= {}

		for MediaFilePath in MediaFilePathList:
			SourceModificationTime	= os.path.getmtime(MediaFilePath)

			if not self.db.dbMediaFileKnown(MediaFilePath, SourceModificationTime):

				print(f"\nFile: {MediaFilePath}")

				# wait until copy has finished
				while time.time() - os.path.getmtime(MediaFilePath) < self.__conf_MIN_MEDIA_FILE_AGE_SEC:
					print('.')
					time.sleep(1)

				fileobj	= lib_media.mediafile(MediaFilePath, self.__conf_RENAME_FILES)

				# target path
				TargetPath	= os.path.join(
					self.__conf_TARGET_DIR,
					fileobj.get_new_FilePath()
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

				if self.__conf_FILE_EXTENSIONS_SUBFOLDER_GEO:
					if MediaFileExt in (extension.lower() for extension in self.__conf_FILE_EXTENSIONS_LIST_GEO):
						TargetPath	= os.path.join(TargetPath, self.__conf_FILE_EXTENSIONS_SUBFOLDER_GEO)

				# create target path
				print(f"TargetPath: {TargetPath}")

				if not os.path.isdir(TargetPath):
					DirsCreated	+= 1
					os.makedirs(TargetPath, exist_ok=True)

				# FileName
				TargetFileName	= fileobj.get_new_FileName()

				# target file path and name
				TargetFilePathName	= os.path.join(TargetPath, TargetFileName)

				if not os.path.isfile(TargetFilePathName) or self.__conf_OVERWRITE:
					FilesProcessed	+= 1
					# transfer
					if self.__conf_MOVE_FILES:
						print(f"move '{MediaFilePath}' to '{TargetFilePathName}'")
						shutil.move(MediaFilePath, TargetFilePathName)
					else:
						print(f"copy '{MediaFilePath}' to '{TargetFilePathName}'")
						shutil.copy(MediaFilePath, TargetFilePathName)

					if not fileobj.exifdate_exists:
						print(f"Writing 'Create Date' into media file: {fileobj.year}:{fileobj.month}:{fileobj.day} {fileobj.hour}:{fileobj.minute}:{fileobj.second}")
						CreateDate	= f"{fileobj.year}:{fileobj.month}:{fileobj.day} {fileobj.hour}:{fileobj.minute}:{fileobj.second}"
						Command	= ['exiftool', '-overwrite_original', f"-CreateDate='{CreateDate}'", TargetFilePathName]
						subprocess.run(Command)

				self.db.dbInsertMediaFile(MediaFilePath, SourceModificationTime)

				TargetSubPath	= TargetPath.replace(self.__conf_TARGET_DIR, '', 1).strip('/')
				if TargetSubPath not in FilesAtTarget.keys():
					FilesAtTarget[TargetSubPath]	= []
				FilesAtTarget[TargetSubPath].append(os.path.basename(MediaFilePath))

		print(f"\n * {FilesProcessed} files processed.")
		print(f" * {DirsCreated} new folders created.")

		for TargetSubPath in FilesAtTarget.keys():
			print(f"\n{TargetSubPath}")
			for FileName in FilesAtTarget[TargetSubPath]:
				print(f" - {FileName}")

		if (FilesProcessed > 0) or (DirsCreated > 0):
			mail	= lib_mail.mail(self.__setup)

			if mail.mail_configured():
				mail_subject	= f'archivist: {ConfigFilePath}'

				mail_text_plain	= f"""
 * {FilesProcessed} files processed.
 * {DirsCreated} new folders created.
				"""

				for TargetSubPath in FilesAtTarget.keys():
					mail_text_plain	+= f"\n\n{TargetSubPath}"

					for FileName in FilesAtTarget[TargetSubPath]:
						mail_text_plain	+= f"\n - {FileName}"

				mail_text_html	= f"""
<ul>
	<li>{FilesProcessed} files processed.</li>
	<li>{DirsCreated} new folders created.</li>
</ul>
				"""
				for TargetSubPath in FilesAtTarget.keys():
					mail_text_html	+= f"<h3>{TargetSubPath}</h3>"

					mail_text_html	+= "\n<ul>"
					for FileName in FilesAtTarget[TargetSubPath]:
						mail_text_html	+= f"\n<li>{FileName}</li>"
					mail_text_html	+= "\n</ul>"

				mail.sendmail(Subject=mail_subject, TextPlain=mail_text_plain, TextHTML=mail_text_html)

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
