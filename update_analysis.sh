#!/bin/bash
GITINGEST="/home/ichigo/.local/bin/gitingest"
OUTPUT="/home/ichigo/.gemini/tmp/Alexandria-GitIngest-Analysis-NEW.md"
CORE_DIR="/home/ichigo/alexandria/anima-mundi/defense/alexandria-core"
ADAM_DIR="/home/ichigo/alexandria/ADAM"

echo "Directory structure:" > $OUTPUT
echo "└── alexandria-core/" >> $OUTPUT

# 1. Root files of core
$GITINGEST $CORE_DIR -e "*/" -o - >> $OUTPUT

# 2. Major subdirs of core
for dir in aegis vault phoenix chapel-xvi sentinelle paint-shop opensea-js alexandria-lite; do
  if [ -d "$CORE_DIR/$dir" ]; then
    echo "================================================" >> $OUTPUT
    echo "COMPONENT: $dir" >> $OUTPUT
    echo "================================================" >> $OUTPUT
    $GITINGEST "$CORE_DIR/$dir" -e "node_modules/*" -e "build/*" -e "dist/*" -e "*.zip" -e "*.gz" -o - >> $OUTPUT
  fi
done

# 3. ADAM root and key files
echo "================================================" >> $OUTPUT
echo "COMPONENT: ADAM (Core Updates)" >> $OUTPUT
echo "================================================" >> $OUTPUT
$GITINGEST $ADAM_DIR -e "*/" -o - >> $OUTPUT

# 4. Critical ADAM docs
for doc in ADAM_v7.0_IMPLEMENTATION_COMPLETE.md ADAM-STATUS.md ADAM_SELF_DISCOVERY_REPORT.md; do
  if [ -f "$ADAM_DIR/$doc" ]; then
    echo "================================================" >> $OUTPUT
    echo "FILE: $doc" >> $OUTPUT
    echo "================================================" >> $OUTPUT
    cat "$ADAM_DIR/$doc" >> $OUTPUT
  fi
done
