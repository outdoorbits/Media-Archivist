#!/bin/bash

rm /tmp/target/* -R
rm -R /tmp/source

cp -R /tmp/source_backup /tmp/source

python3 archivist.py --config=config.cfg

sqlite3 /tmp/source/archivist.sqlite3 'select * from mediafiles;'
