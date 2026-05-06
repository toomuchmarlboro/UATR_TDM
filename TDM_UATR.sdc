create_clock -name board_clk -period 20.000 [get_ports {clk_18m432}]
derive_clock_uncertainty