return {
  "folke/snacks.nvim",
  keys = {
    {
      "<leader>ss",
      function()
        Snacks.picker.lsp_symbols({ filter = { typescript = { "Function", "Interface", "Type" } } })
      end,
      desc = "LSP Symbols (funcs)",
    },
    {
      "<leader>e",
      false,
    },
  },
  opts = {
    explorer = {
      replace_netrw = false,
    },
  },
}
