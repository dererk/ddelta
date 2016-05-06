import lzma
import os
import tempfile
from subprocess import Popen, PIPE


# XXX :: TODO
# Some deb formats appears to be -9 while others -1
GZIP_PARAMS   = "-9 -n"
# Hack, works much better than default
XDELTA_PARAMS = "-9 -S lzma"


def sh(cmd):
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    if proc.poll() != 0:
        raise BaseException("{}\n{}".format(stdout, stderr))
    return stdout


def parse_debname(filename):
    filename, ext = os.path.splitext(os.path.basename(filename))
    debian_name, version, arch = filename.split("_")
    return debian_name, version, arch


def extract_ar(archive_file, output_dir):
    sh("cd {} && ar x {}".format(output_dir, archive_file))


def unpack(package, outdir):
    if sh("ar t {} |grep data.tar.xz".format(package)):
        sh("ar p {} {} | xz -d > {}".format(package, "data.tar.xz", os.path.join(outdir, "data.tar")))
    else:
        sh("ar p {} {} | gunzip > {}".format(package, "data.tar.gz", os.path.join(outdir, "data.tar")))
    sh("ar p {} {} | gunzip > {}".format(package, "control.tar.gz", os.path.join(outdir, "control.tar")))


def generate_delta(source, target, delta_file):
    def extract_ar(archive_file, output_dir):
        sh("cd {} && ar x {}".format(output_dir, archive_file))
    sh("xdelta3 {} -s {} {} {}".format(XDELTA_PARAMS, source, target, delta_file))


def package_xfer_ddelta(control_delta, data_delta, xfer_file):
    sh("ar Drcs {} {} {}".format(xfer_file, control_delta, data_delta))


def apply_delta_target(source, delta, target):
    sh("xdelta3 -d -s {} {} {}".format(source, delta, target))


def generate_deb(path, debian_package_name, version="2.0"):
    # http://tldp.org/HOWTO/html_single/Debian-Binary-Package-Building-HOWTO/#AEN66
    binary_path = os.path.join(path, "debian-binary")
    open(binary_path, "w").write("{}\n".format(version))

    # xz compress data
    data = os.path.join(path, "data.tar")
    data_xz = os.path.join(path, "data.tar.xz")
    with open(data, 'rb') as f:
        with open(data_xz, 'wb') as out:
            out.write(lzma.compress(bytes(f.read()), preset=6, check=1))

    # workaround broken gzip module not respecting compresslevel nor fileobj params
    # level 1, no file obj names (debian control standard)
    control = os.path.join(path, "control.tar")
    control_gz = os.path.join(path, "control.tar.gz")
    sh("gzip {} {}".format(GZIP_PARAMS, control))

    output_deb = os.path.join(path, "{}.deb".format(debian_package_name))
    sh("ar rcs {} {}/debian-binary {} {}".format(output_deb, path, control_gz, data_xz))
    return output_deb


def repackage_from_xfer_ddelta(source, xfer_file):
    tmp_dir = tempfile.mkdtemp()
    source_dir = os.path.join(tmp_dir, "source")
    os.mkdir(source_dir)
    unpack(source, source_dir)
    extract_ar(xfer_file, source_dir)

    source_data = os.path.join(source_dir, "data.tar")
    target_data = os.path.join(tmp_dir, "data.tar")
    delta_data = os.path.join(source_dir, "data.xdelta3")

    source_control = os.path.join(source_dir, "control.tar")
    target_control = os.path.join(tmp_dir, "control.tar")
    delta_control = os.path.join(source_dir, "control.xdelta3")

    apply_delta_target(source_data, delta_data, target_data)
    apply_delta_target(source_control, delta_control, target_control)

    return tmp_dir


def prepare_xfer_ddelta(old_pkg, new_pkg, xfer_file):
    tmp_dir = tempfile.mkdtemp()
    source_dir = os.path.join(tmp_dir, "source")
    target_dir = os.path.join(tmp_dir, "target")
    os.mkdir(source_dir)
    os.mkdir(target_dir)
    unpack(old_pkg, source_dir)
    unpack(new_pkg, target_dir)

    source_data = os.path.join(source_dir, "data.tar")
    target_data = os.path.join(target_dir, "data.tar")
    delta_data = os.path.join(tmp_dir, "data.xdelta3")

    source_control = os.path.join(source_dir, "control.tar")
    target_control = os.path.join(target_dir, "control.tar")
    delta_control = os.path.join(tmp_dir, "control.xdelta3")

    xfer_file_path = os.path.join(tmp_dir, xfer_file)

    generate_delta(source_data, target_data, delta_data)
    generate_delta(source_control, target_control, delta_control)

    package_xfer_ddelta(delta_control, delta_data, xfer_file_path)

    return xfer_file_path
