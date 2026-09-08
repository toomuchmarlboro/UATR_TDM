#!/bin/bash
# Build 8 images: 4 nodes x {24K decimating, 96K plain}, all 192.168.3.x
#
# A LOCK, because two concurrent runs corrupt each other: both edit
# rtl/top_system.vhd and both write output_files/TDM_UATR.sof, so the .jic that
# gets copied can carry another run's C_NODE. That produces images labelled for
# one board containing another board's IP - the exact failure the filename
# convention exists to prevent.
set -e
LOCK=/tmp/tdm_build.lock
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "ANOTHER BUILD IS RUNNING (lock $LOCK). Refusing to start."
  exit 1
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

export PATH="/c/altera_lite/25.1std/quartus/bin64:$PATH"
setc () {
  python -c "
import re
p='rtl/top_system.vhd'
s=open(p,encoding='utf-8').read()
s=re.sub(r'constant C_NODE : integer range 1 to 4 := \d+;','constant C_NODE : integer range 1 to 4 := $1;',s)
s=re.sub(r'constant C_DECIMATE : boolean := (true|false);','constant C_DECIMATE : boolean := $2;',s)
open(p,'w',encoding='utf-8').write(s)
"
}
for MODE in true false; do
  if [ "$MODE" = "true" ]; then TAG=24K; else TAG=96K; fi
  for N in 1 2 3 4; do
    setc $N $MODE
    OUT="output_files/${TAG}_NODE${N}_192-168-3-10${N}.jic"
    if quartus_sh --flow compile TDM_UATR > /tmp/bl_${TAG}_$N.log 2>&1; then
      quartus_cpf -c -d EPCS16 -s EP4CE6E22C8 output_files/TDM_UATR.sof "$OUT" >/dev/null 2>&1
      LE=$(grep -m1 "Total logic elements" output_files/TDM_UATR.fit.summary | sed 's/.*: //')
      TNS=$(grep -m1 "Design-wide TNS" output_files/TDM_UATR.sta.rpt | awk -F';' '{gsub(/ /,"");print $3"/"$4"/"$5"/"$6"/"$7}')
      echo "$TAG node$N  LE $LE  TNS $TNS"
    else
      echo "$TAG node$N  BUILD FAILED"
      grep -m3 -i "^Error" /tmp/bl_${TAG}_$N.log
      exit 1
    fi
  done
done
setc 1 true      # leave the tree on a sane default
echo "ALL 8 DONE"
