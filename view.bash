#!/bin/bash
cd storage/$1

git ls-tree --full-tree -r --name-only HEAD

