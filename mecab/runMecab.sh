#!/bin/bash

#!/usr/bin/bash

MDIR=${HOME}/.local/share/Anki2/addons21/MecabUnidic/support
export LD_LIBRARY_PATH=$MDIR:
export DYLD_LIBRARY_PATH=$MDIR:
$MDIR/mecab.lin -d $MDIR -r $MDIR/mecabrc "$1"
