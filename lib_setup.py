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

# Provides the standard-setup,the types of constants and routines to handle the setup

import os
import subprocess
import sys

from configobj import ConfigObj

class setup(object):

	def __init__(self,ConfigFilePath,rewrite_configfile=False):

		WORKING_DIR	= os.path.dirname(__file__)

		self.__uid		= os.getuid()
		self.__gid		= os.getgid()

		# config
		self.config	= self.__get_config_standard()

		self.__get_config_configured(ConfigFilePath)

		self.setup	= self.config

		if not os.path.isfile(ConfigFilePath):
			self.rewrite_configfile(ConfigFilePath)


	def get_val(self,setup_var):
		if setup_var in self.setup:
			return (self.setup[setup_var]['value'])
		else:
			return('Error: Unknown VARIABLE {}'.format(setup_var))

	def __norm_value(self,value,val_type):
		if val_type == 'int':
			return(int(value) if value else 0)

		elif val_type == 'int16':
				return(int(value,16) if value else 0)

		elif val_type == 'float':
			return(int(value))

		elif val_type == 'bool':
			return(
				(value == True) or
				(value == 1) or
				(value == '1') or
				(value.lower() == 'true')
			)

		else:
			return(str(value))

	def rewrite_configfile(self,ConfigFilePath):
		with open(ConfigFilePath,'w') as f:
			for ConfigVar in self.config:

				if self.config[ConfigVar]['type'] == 'str':
					Separator = "'"
				else:
					Separator = ''

				if self.config[ConfigVar]['type'] == 'int16':
					Separator = "'"
					if not isinstance(self.config[ConfigVar]['value'], str):
						self.config[ConfigVar]['value']	= hex(self.config[ConfigVar]['value'])

				f.write(f"{ConfigVar}={Separator}{self.config[ConfigVar]['value']}{Separator}\n")

		os.chown(ConfigFilePath, self.__uid, self.__gid)

	def __get_config_configured(self,ConfigFilePath):
		if os.path.isfile(ConfigFilePath):

			config_file = ConfigObj(ConfigFilePath)

			for conf_var in config_file:

				conf_val	= config_file[conf_var]

				# set type
				if conf_var in self.config:
					conf_type	= self.config[conf_var]['type']
				else:
					conf_type	= 'str'

				# set value
				self.config[conf_var]	= {'value': self.__norm_value(conf_val, conf_type), 'type': conf_type}

			return

	def __get_config_standard(self):
		return(
				{
					'conf_SOURCE_DIR':								{'value': '/your/source/dir', 'type' : 'str'},
					'conf_TARGET_DIR':								{'value': '/your/target/dir', 'type' : 'str'},
					'conf_MOVE_FILES':								{'value': True, 'type' : 'bool'},
					'conf_SET_USER':								{'value': '', 'type' : 'str'},
					'conf_SET_GROUP':								{'value': '', 'type' : 'str'},
					'conf_SET_PERMISSIONS':							{'value': '700', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_LIST_WEB_IMAGES':			{'value': 'jpg;jpeg;gif;png', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_LIST_HEIC':				{'value': 'heic;heif', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_LIST_RAW':				{'value': '3fr;arw;dcr;dng;cr2;cr3;crw;fff;gpr;j6i;k25;kc2;kdc;mdc;mrw;nef;nrw;orf;pef;raw;raf;rw2;rwl;sr2;srf;srw;x3f', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_LIST_TIF':				{'value': 'tif;tiff', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_LIST_VIDEO':				{'value': 'avi;lrv;mp4', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_LIST_AUDIO':				{'value': 'mp3;wav', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES':	{'value': '', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_SUBFOLDER_HEIC':			{'value': '', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_SUBFOLDER_RAW':			{'value': '', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_SUBFOLDER_TIF':			{'value': '', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO':			{'value': '', 'type' : 'str'},
					'conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO':			{'value': '', 'type' : 'str'},
					'conf_DB_MIN_IDLE_SEC':							{'value': 15, 'type' : 'int'},
					'conf_MIN_MEDIA_FILE_AGE_SEC':					{'value': 10, 'type' : 'int'},
					'conf_EXEC_SCRIPT_IF_SUCCESS':					{'value': 'echo "It worked."; echo "Replace this by whatever you need!"', 'type' : 'str'},
					'conf_MAIL_HTML':								{'value': True, 'type' : 'bool'},
					'conf_SMTP_SERVER':								{'value': '', 'type' : 'str'},
					'conf_SMTP_PORT':								{'value': '465', 'type' : 'str'},
					'conf_MAIL_SECURITY':							{'value': 'STARTTLS', 'type' : 'str'},
					'conf_MAIL_USER':								{'value': '', 'type' : 'str'},
					'conf_MAIL_PASSWORD':							{'value': '', 'type' : 'str'},
					'conf_MAIL_FROM':								{'value': '', 'type' : 'str'},
					'conf_MAIL_TO':									{'value': '', 'type' : 'str'},
					'conf_MAIL_TIMEOUT':							{'value': 15, 'type' : 'int'}
				}
		)


if __name__ == "__main__":
	# write config files
	__setup	= setup(True)




