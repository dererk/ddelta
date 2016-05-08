#!/usr/bin/env python3
import argparse
import ddelta
import sys

""" ddpatch

Given one specific version of a package pkg_v1.deb and a delta container, generate
the target package pkg_v2.deb allowing upload to the destination only the differences
between the old version and the new version.

At destination is necessary rebuild the current package using dpkg-repack, or an
archived version and this tool for applying the delta container to it.

"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='debian package minimization tool for low bandwidth xfers')
    parser.add_argument('-d', "--delta", default=None, help="Path to package delta xfer to be read from")
    parser.add_argument('-s', "--source", default=None, help="Source path from package to be used as original package")
    parser.add_argument('-c', "--check", action="store_true", help="Verify that produced package delta xfer patches properly once built")
    args = parser.parse_args()

    out_file = ''
    if args.source and args.delta:
        applied_delta = ddelta.delta_repackage_from_ddelta_xfer(args.source, args.delta)
        out_file = ddelta.deb_generate_final_package(applied_delta)
        out_file = ddelta.deb_rename_file_from_metadata(out_file)

        if args.check:
            if ddelta.deb_check_package_integrity(out_file):
                print("Integrity Check OK")
            else:
                print("Integrity Check FAILED!!!")

        print(out_file)

    else:
        print("Missing arguments for generating: ", args)
        sys.exit(1)
