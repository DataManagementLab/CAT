#!/bin/bash

pg_restore -U cat -d cat -O /init_data/dump.tar
