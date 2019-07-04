#!/bin/bash

touch $1
shift
exec "$@"
