#!/bin/sh

N=${1:-1000}
OUT="${2:-mass.template}"
P=${3:-test}

cat << EOF > "$OUT"
file "mass.db" {
pattern {N}
EOF

for i in `seq $N`
do
	printf '{\"%s%u\"}\n' "$P" $i
done >> "$OUT"


cat <<EOF >> "$OUT"
}
EOF
