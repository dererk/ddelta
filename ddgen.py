#!/usr/bin/env python3
import argparse
import ddelta
import sys

""" ddgen

Given one specific version of a package pkg_v1.deb and a delta container, generate
the target package pkg_v2.deb allowing upload to the destination only the differences
between the old version and the new version.

In the destination is necessary rebuild the current package using dpkg-repack
and this tool for applying the delta container to it.

"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='debian package minimization tool for low bandwidth xfers')
    parser.add_argument('-s', "--source", default=None, help="Source path from package to be used as original package")
    parser.add_argument('-t', "--target", default=None, help="Target path from package to be used as final package")
    args = parser.parse_args()


    if args.source and args.target:
        delta_name = ddelta.delta_get_friendly_name(args.source, args.target)
        print(ddelta.delta_prepare_ddelta_xfer(args.source, args.target, delta_name))
    else:
        print("Missing arguments for generating package delta: ", args)
        sys.exit(1)
