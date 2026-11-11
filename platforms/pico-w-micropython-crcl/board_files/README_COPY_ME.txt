Copy the CONTENTS of this board_files directory to the Pico W filesystem root.

Do not rename the sdl/, drivers/, capabilities/, apps/, or staging/ directories.
A /config.json file is optional. Without one, config_default.py is used and Wi-Fi
is left unconfigured, so USB-console bring-up still works.

For PicoBricks Wi-Fi operation, create /config.json from
../config.picobricks.example.json and insert your own SSID/password.
