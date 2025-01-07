stow --adopt -R -t ~/.config/ .
echo "Dotfiles stowed in ~/.config"
ln -s ~/.config/zsh/.zshrc ~/.zshrc
echo "Linked .zshrc to ~"
