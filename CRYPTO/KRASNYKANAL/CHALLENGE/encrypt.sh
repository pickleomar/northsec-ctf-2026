#!/bin/bash

ALG="des"
MODE="cbc"
KEY_MODE="hex"

mcrypt -a $ALG -c $MODE -o $KEY_MODE Ultimatum.jpg
