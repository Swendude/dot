# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

export XDG_CONFIG_HOME="$HOME/.config"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time Oh My Zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME=""


plugins=(
  git tmux docker github z
)

source $ZSH/oh-my-zsh.sh

# Pure Path
fpath+=($HOME/.config/omz/themes/pure) 
autoload -U promptinit; promptinit
prompt pure

# Startup Tmux with a root session
if [ "$TMUX" = "" ]; then tmux new-session -As root; fi

# Preferred editor for local and remote sessions
if [[ -n $SSH_CONNECTION ]]; then
  export EDITOR='vim'
else
  export EDITOR='nvim'
fi

# Direnv setup
eval "$(direnv hook zsh)"

export GPG_TTY=$(tty)
alias python=python

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# pnpm
export PNPM_HOME="/Users/swen/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

# Claude with homebrew installed here
PATH="$HOME/.local/bin:$PATH"

# Dotnet
export PATH="$PATH:/usr/local/share/dotnet/dotnet"
export PATH="$PATH:/Users/swen/.dotnet/tools"

# Lazygit
alias lg=lazygit

# Nix
export PATH="$PATH:/nix/var/nix/profiles/default/bin"

# Enable Vi mode
bindkey -v

# If on WSL, add a browser
if uname -r | grep -q 'Microsoft' ; then export BROWSER="/mnt/c/Program\ Files/BraveSoftware/Brave-Browser/Application/brave.exe"; fi

if uname -r | grep -q 'Microsoft' ; then export PATH="$PATH:/opt/nvim-linux-x86_64/bin"

# wtfpl
alias wtfpl="curl http://www.wtfpl.net/txt/copying/ -o LICENSE.md"

# Created by `pipx` on 2025-02-11 19:46:57
export PATH="$PATH:/home/swen/.local/bin"
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"

# Go Path
export PATH="$PATH:/usr/local/go/bin"
