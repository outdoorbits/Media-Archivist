# Media Archivist

This script sorts media files from a source folder to a target folder according to their create date. At the destination, the files are stored under the following structure:

target-path/YYYY/YYYY-MM/YYYY-MM-DD/

Among other things, you can configure whether the files should be copied or moved.

## Usage
python3 /path-to-script/archivist.py config=CONFIG-FILE [--clean]

If CONFIG-FILE does not exist, it is created and then has to be edited.\

The source path can be cleared using the --clean option.\

## Configuration
Contents of the config file:\
conf_SOURCE_DIR='/your/source/dir'\
conf_TARGET_DIR='/your/target/dir'\
conf_MOVE_FILES=True\
conf_SET_USER\
conf_SET_GROUP\
conf_SET_PERMISSIONS='700'\
conf_FILE_EXTENSIONS_LIST_WEB_IMAGES='jpg;jpeg;gif;png'\
conf_FILE_EXTENSIONS_LIST_HEIC='heic;heif'\
conf_FILE_EXTENSIONS_LIST_RAW='3fr;arw;dcr;dng;cr2;cr3;crw;fff;gpr;j6i;k25;kc2;kdc;mdc;mrw;nef;nrw;orf;pef;raw;raf;rw2;rwl;sr2 ;srf;srw;x3f'\
conf_FILE_EXTENSIONS_LIST_TIF='tif;tiff'\
conf_FILE_EXTENSIONS_LIST_VIDEO='avi;lrv;mp4'\
conf_FILE_EXTENSIONS_LIST_AUDIO='mp3;wav'\
conf_DB_MIN_IDLE_SEC=15\
conf_MIN_MEDIA_FILE_AGE_SEC=10

### Configuration details
#conf_SOURCE_DIR
Source directory

#### conf_TARGET_DIR
Target directory

#### conf_MOVE_FILES
Copy files: False\
Move files: True

#### conf_SET_USER
Linux username that should own the files in the target directory\
This will only be applied if the user and group are defined.

#### conf_SET_GROUP
Linux group that the files in the target directory should belong to\
This will only be applied if the user and group are defined.

#### conf_SET_PERMISSIONS
Permissions of the files in the target directory. Example: '700'

#### conf_FILE_EXTENSIONS_LIST_WEB_IMAGES, conf_FILE_EXTENSIONS_LIST_HEIC, conf_FILE_EXTENSIONS_LIST_RAW, conf_FILE_EXTENSIONS_LIST_TIF, conf_FILE_EXTENSIONS_LIST_VIDEO, conf_FILE_EXTENSIONS_LIST_AUDIO
Endings of media files to be copied. All other endings are ignored. Upper and lower case letters are not taken into account.

#### conf_FILE_EXTENSIONS_SUBFOLDER_WEB_IMAGES, conf_FILE_EXTENSIONS_SUBFOLDER_HEIC, conf_FILE_EXTENSIONS_SUBFOLDER_RAW, conf_FILE_EXTENSIONS_SUBFOLDER_TIF, conf_FILE_EXTENSIONS_SUBFOLDER_VIDEO, conf_FILE_EXTENSIONS_SUBFOLDER_AUDIO
Define an optional subpath at target for this file extensions, for example:
conf_FILE_EXTENSIONS_SUBFOLDER_RAW='RAW'
Makes RAW files are transfered to
target-path/YYYY/YYYY-MM/YYYY-MM-DD/RAW

#### conf_DB_MIN_IDLE_SEC
To avoid the script being executed multiple times, the script is only executed if the database created in the source directory has not been changed for at least this many seconds

#### conf_MIN_MEDIA_FILE_AGE_SEC
Files will not be copied until they have reached this age. This is to avoid sorting files that are currently being written to the source directory.
