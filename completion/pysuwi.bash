# bash completion for pysuwi. The command list is queried on every TAB,
# so new plugins appear without reinstalling.
_pysuwi_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    if (( COMP_CWORD == 1 )); then
        local words
        words="$(pysuwi --list-commands 2>/dev/null) --help --version"
        COMPREPLY=( $(compgen -W "$words" -- "$cur") )
    fi
}
complete -o default -F _pysuwi_complete pysuwi
