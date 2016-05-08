#!/usr/bin/env python3
import argparse
from ddelta import ddelta
import sys
from os import stat
from time import monotonic

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
    parser.add_argument('-v', "--verbose", action="store_true", help="Prints a more vebose detail of the process, summary and performance")
    args = parser.parse_args()


    if args.source and args.target:
        init_t = monotonic()
        delta_name = ddelta.delta_get_friendly_name(args.source, args.target)
        result = ddelta.delta_prepare_ddelta_xfer(args.source, args.target, delta_name)

        if args.verbose:
            source_size = stat(args.source).st_size
            target_size = stat(args.target).st_size
            ddelta_xfer = stat(result).st_size
            rate = ddelta_xfer / source_size
            gain = source_size - ddelta_xfer
            gain_rate = '{}'.format('+' if gain > 0 else '-')
            print("================= SUMMARY STATS ====================\n\t" \
                  "- Source Size:\t{} bytes\n\t" \
                  "- Target Size:\t{} bytes\n\t" \
                  "- Ddelta Xfer:\t{} bytes\n\t" \
                  "- Total gain:\t{} bytes\n\t"  \
                  "- Gain rate:\t{}{:.2f}%\n\t"  \
                  "- Time Took:\t{:.2f} seconds\n" \
                  "================= SUMMARY STATS ====================".format(
                source_size,
                target_size,
                ddelta_xfer,
                gain,
                gain_rate,
                rate * 100,
                monotonic() - init_t
            ))
        print(result)

    else:
        print("Missing arguments for generating package delta: ", args)
        sys.exit(1)
