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
import re
import subprocess
import sys#xxx

class mediafile(object):

	def __init__(self, FilePathName, rename = False):
		print(FilePathName)
		self.__pattern		= re.compile(r"^\d{4}-[01]\d-[0-3]\d_[0-2]\d-[0-5]\d-[0-5]\d_-")

		self.FilePathName	= FilePathName
		self.FileName		= os.path.basename(FilePathName)
		self.FilePath		= os.path.dirname(FilePathName)

		try:
			self.FileName_plain	= self.FileName.split('_-_', 1)[1]
		except:
			self.FileName_plain	= self.FileName

		self.rename			= rename
		self.pattern_match	= bool(self.__pattern.match(self.FileName))

		self.exifdate_exists	= True

		self.__read_datetime()

	def __read_datetime(self):

		if self.pattern_match:
			# use filename as date source
			if self.__get_datetime_from_string(self.FileName):
				return(True)
			else:
				return(self.set_panic_values())

		else:
			# read exif data from file
			DateTags		=  [
				'CreateDate',
				'CreationDate',
				'MediaCreateDate',
				'DateTimeOriginal',
				'FileModifyDate',
				'FileAccessDate'
			]

			EXIF_output	= ''
			for DateTag in DateTags:
				ExifCommand		= ['exiftool', os.path.join(self.FilePath, self.FileName), '-dateFormat', '%Y-%m-%d_%H-%M-%S'] + [f"-{DateTag}"] + ['-S']

				try:
					EXIF_output	= subprocess.check_output(ExifCommand, text=True).strip()
				except:
					pass

				if EXIF_output:
					# first hit finishes search
					break

			if not EXIF_output:
				return(self.set_panic_values())
			else:

				try:
					Val	= EXIF_Line.split(':', 1)[1].strip()
				except:
					Val	= None

				if not Val is None:
					return(self.__get_datetime_from_string(Val))
				else:
					self.exifdate_exists	= False
					return(self.set_panic_values())

		return(self.set_panic_values())

	def set_panic_values(self):
		if not self.get_filesystem_values():
			self.set_null_values()
			return(False)
		else:
			return(True)

	def get_filesystem_values(self):
		return(self.__get_datetime_from_string(datetime.fromtimestamp(os.path.getmtime(self.FilePathName)).strftime("%Y-%m-%d %H-%M-%S")))

	def set_null_values(self):
		self.year, self.month, self.day, self.hour, self.minute, self.second	= ['0000', '00', '00', '00', '00', '00']

	def __get_datetime_from_string(self, datetimeString):

		# replace separators
		separators = ['-', '_', '.', ':', ';', '|', ' ']

		# Create regex pattern from the list
		pattern = f"[{''.join(map(re.escape, separators))}]"

		datetime_prepared	= re.sub(pattern, '-', datetimeString)

		# remove duplicated separators
		datetime_prepared = re.sub(r'-+', '-', datetime_prepared)

		# add pseudo filename for compatibility
		datetime_prepared	= f'{datetime_prepared}-'

		try:
			# split date and time parts from cleaned string
			self.year, self.month, self.day, self.hour, self.minute, self.second, rest	= datetime_prepared.split('-', 6)
			return(True)
		except:
			self.set_null_values()
			return(False)

	def get_new_FilePath(self):
		PathLevel_year	= f'{self.year}'
		PathLevel_month	= f'{self.year}-{self.month}'
		PathLevel_day	= f'{self.year}-{self.month}-{self.day}'

		return(os.path.join(PathLevel_year, PathLevel_month, PathLevel_day))

	def get_new_FileName(self):
		if self.rename:
			FileDateTime	= f'{self.year}-{self.month}-{self.day}_{self.hour}-{self.minute}-{self.second}'

			return(f'{FileDateTime}_-_{self.FileName_plain}')
		else:
			return(self.FileName_plain)


