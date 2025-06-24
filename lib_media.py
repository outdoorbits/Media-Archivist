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

class mediafile(object):

	def __init__(self, FilePathName, rename = False):

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
				'FileModificationDateTime',
				'FileAccessDateTime'
			]

			ExifCommand		= ['exiftool', os.path.join(self.FilePath, self.FileName), '-dateFormat', '%Y-%m-%d_%H-%M-%S'] + [f"-{tag}" for tag in DateTags] + ['-S']
			EXIF_output	= None
			try:
				EXIF_output	= subprocess.check_output(ExifCommand, text=True)
			except:
				return(self.set_panic_values())

			if EXIF_output is None:
				return(self.set_panic_values())

			if any(DateTag in EXIF_output for DateTag in DateTags):

				EXIF_Lines	= EXIF_output.strip().split('\n')

				FileCreateDate	= '0000-00-00_00-00-00'
				for EXIF_Line in EXIF_Lines[1:]:
					try:
						Var, Val	= EXIF_Line.split(':', 1)
					except:
						continue

					Val	= Val.strip()

					if Var in DateTags:
						if (Val > FileCreateDate) or (FileCreateDate == FileCreateDateNull):
							FileCreateDate	= Val

				if FileCreateDate != '0000-00-00_00-00-00':
					return(self.__get_datetime_from_string(FileCreateDate))
				else:
					self.exifdate_exists	= False
					return(self.set_panic_values())
			else:
				self.exifdate_exists	= False
				return(False)

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


