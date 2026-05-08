#!/bin/bash
dir1=b/SolverCcxTools
dir2=b/SolverCalculiX
# Find the modification times of the latest .frd file in each directory
mtime1=$(find "$dir1" -maxdepth 1 -name "*.frd" -printf "%T+ " | sort | tail -n 1)
mtime2=$(find "$dir2" -maxdepth 1 -name "*.frd" -printf "%T+ " | sort | tail -n 1)

echo mtimes $mtime1 $mtime2

# Compare the modification times
if [[ "$mtime1" > "$mtime2" ]]; then
    echo "cd $dir1 # it has the newer .frd file."
    cd "$dir1" || echo "Failed to change into directory 1."
fi

echo "cd $dir2 # it has the newer .frd file."
cd "$dir2" || echo "Failed to change into directory 2."

# Focus the window
old=`xdotool getactivewindow`
cgx MeshNetgen.frd > /dev/null &
CGX_PID=$!
trap 'pkill -P $$' EXIT
sleep 0.1

if [ $(wc -l < "MeshNetgen.frd") -le 10 ]; then
  exit 1
fi

for trial in `seq 100`; do
  # Find the window ID of the process with _NET_WM_PID = CGX_PID
  WIN_ID=$(xdotool search --pid "$CGX_PID" --class cgx 2>/dev/null | head -1)
  if [ -n "$WIN_ID" ]; then
    break
  fi
  sleep 0.01
done

if [ -z "$WIN_ID" ]; then
    echo "Could not find cgx window for PID $CGX_PID"
    kill "$CGX_PID"
    exit 1
fi

xdotool windowactivate $WIN_ID
while IFS= read -r line; do
  # Execute the xdotool command for the current line
  xdotool type --clearmodifiers "$line"
  xdotool key Return
done <<< "
read MeshNetgen.frd
seta def-mesh e all
seta def-mesh n all
ds 1 e 3
view disp
"

echo focusing $old
xdotool windowactivate "$old"
echo done focusing $old

wait $CGX_PID
