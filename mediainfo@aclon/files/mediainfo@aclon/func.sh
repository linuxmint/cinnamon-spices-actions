#!/bin/bash

col() {
echo -e "$buffer" | sed 's/ *:/齾:/' | column -t -L -s '齾' -o ''
buffer=""
}

format() {
buffer=""
# 读取输入文件的每一行
while IFS= read -r line; do
  # 如果这一行是空行，就格式化之前的行，并将结果添加到输出变量中
  if [[ -z $line ]] || [[ $line =~ ^[[:space:]]+$ ]]; then
    col
  else
    # 如果这一行不是空行，就将它添加到临时文件中
    buffer+=$line$'\n'
  fi
done

if [[ -n $buffer ]]; then
  col
fi
}

export -f col format