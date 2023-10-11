#/bin/bash
cd storage/$1
git log --pretty=format:"%an"
