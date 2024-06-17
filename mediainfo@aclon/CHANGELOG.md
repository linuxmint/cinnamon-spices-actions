Full changelog on: https://github.com/AClon314/cinnamon-spices-actions/commits/master/?since=2024-06-16
run this to update changelog:
```sh
pushd mediainfo@aclon ;\
git log --since 2024-06-16 --pretty=format:'#### %ad `%an` %s%n%b' --date=short --grep='mediainfo' --grep='aclon' >> CHANGELOG.md &&\
popd
```

#### v1.0.1 2024-06-17 `AClon314` mediainfo@aclon: new `format()` to shorten the 1st col, but disable for default.
- refactor script by $format

#### v1.0.0 2024-06-17 `AClon314` mediainfo@aclon: Init project
