cd storage
mkdir $1
cd $1
git --bare init
touch bpauthor
echo $2 > bpauthor
touch bpdescribe
echo $3 > bpdescribe