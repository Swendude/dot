return {
  {
    "nvim-neotest/neotest",
    output_panel = {
      enabled = false,
    },
    output = {
      open_on_run = false,
    },
    opts = {
      quickfix = {
        open = false, -- prevents Trouble (or quickfix) from opening
      },
    },
  },
}
