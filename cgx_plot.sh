#!/bin/bash
cd b/SolverCcxTools
# Focus the window
old=`xdotool getactivewindow`
cgx MeshNetgen.frd &
CGX_PID=$!
trap 'pkill -P $$' EXIT
sleep 0.1

if [ $(wc -l < "$FILE") -le 10]; then
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
