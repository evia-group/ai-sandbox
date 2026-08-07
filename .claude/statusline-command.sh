#!/bin/bash
input=$(cat)

model_name=$(echo "$input" | jq -r '.model.display_name // ""')

total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
total_tokens=$((total_input + total_output))

if [ "$total_tokens" -ge 1000 ]; then
  tokens_display="$((total_tokens / 1000))k"
else
  tokens_display="$total_tokens"
fi

five_hour_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
seven_day_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

if [ -n "$five_hour_pct" ]; then
  five_hour_display=$(printf '%.0f' "$five_hour_pct")
else
  five_hour_display="-"
fi

if [ -n "$seven_day_pct" ]; then
  seven_day_display=$(printf '%.0f' "$seven_day_pct")
else
  seven_day_display="-"
fi

printf '%s \033[1;38;5;208m| %s\033[0m | 5h: %s%%  7d: %s%%\n' "$model_name" "$tokens_display" "$five_hour_display" "$seven_day_display"