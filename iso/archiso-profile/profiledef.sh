#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="deutschland-anschnur-bs"
iso_label="DABS_$(date +%Y%m)"
iso_publisher="Deutschland Anschnur BS <https://example.invalid>"
iso_application="Deutschland Anschnur BS Live/Rescue ISO"
iso_version="$(date +%Y.%m.%d)"
install_dir="arch"
buildmodes=("iso")
bootmodes=("bios.syslinux.mbr" "bios.syslinux.eltorito" "uefi-ia32.grub.esp" "uefi-x64.grub.esp" "uefi-ia32.grub.eltorito" "uefi-x64.grub.eltorito")
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=("-comp" "xz" "-Xbcj" "x86" "-b" "1M" "-Xdict-size" "1M")
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
)
