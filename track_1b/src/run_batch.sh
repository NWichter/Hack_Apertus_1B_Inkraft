#!/bin/sh
# usage: run_batch.sh <batch_id> [suffix]
b="$1"; s="${2:-}"
start=$(date -Iseconds)
codex exec --skip-git-repo-check --ephemeral -s read-only -C . -c model_reasoning_effort="medium" -o "$b$s.out.jsonl" - < "$b$s.prompt.txt" > "$b$s.log" 2>&1
rc=$?
end=$(date -Iseconds)
printf '{"batch":"%s%s","start":"%s","end":"%s","exit":%s,"command":"codex exec --skip-git-repo-check --ephemeral -s read-only -C . -c model_reasoning_effort=\\"medium\\" -o %s%s.out.jsonl - < %s%s.prompt.txt"}\n' "$b" "$s" "$start" "$end" "$rc" "$b" "$s" "$b" "$s" >> runs.jsonl
