"*****************************************************************************
"" Custom configs
"*****************************************************************************
" html
" for html files, 2 spaces
autocmd Filetype html setlocal ts=2 sw=2 expandtab

" javascript
let g:javascript_enable_domhtmlcss = 1

" vim-javascript
augroup vimrc-javascript
  autocmd!
  autocmd FileType javascript setl tabstop=2|setl shiftwidth=2|setl expandtab softtabstop=2
augroup END

" typescript
let g:yats_host_keyword = 1

" Prettier
command! -nargs=0 Prettier :CocCommand prettier.formatFile

