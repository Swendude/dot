return {
  "stevearc/conform.nvim",
  opts = function(_, opts)
    opts.formatters_by_ft = vim.tbl_deep_extend("force", opts.formatters_by_ft or {}, {
      javascript = { "biome", "vtsls" },
      javascriptreact = { "biome", "vtsls" },
      typescript = { "biome", "vtsls" },
      typescriptreact = { "biome", "vtsls" },
      json = { "biome", "vtsls" },
    })
  end,
}
