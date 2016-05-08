import ddelta
import os
import unittest
import tempfile
import shutil
from hashlib import md5



test_path = os.getcwd()
broken_deb = { 'file':'python3-imaplib2_2.45.0-1_all.deb' }
delta_last = { 'file':'python3-imaplib2_2.50-2_all.deb' }
delta_two = { 'file':'python3-imaplib2_2.50-1_all.deb' }
original =  { 'file':'python3-imaplib2_2.42-1_all.deb' }


class TestDDeltaPatcheability(unittest.TestCase):

    def test_checking_runtime_dependencies(self):
        self.assertTrue(os.path.exists('/usr/bin/ar'))
        self.assertTrue(os.path.exists('/usr/bin/xdelta3'))
        self.assertTrue(os.path.exists('/bin/tar'))
        self.assertTrue(os.path.exists('/bin/gzip'))
        self.assertTrue(os.path.exists('/bin/gzip'))

    def test_preparing_xfer_ddelta(self):
        ret = ddelta.delta_prepare_ddelta_xfer(original['file'], delta_last['file'], 'test_ddelta')
        self.assertTrue(ret)
        self.assertTrue(os.path.exists(ret))

    def test_preparing_xfer_ddelta_right_size(self):
        ret = ddelta.delta_prepare_ddelta_xfer(original['file'], delta_last['file'], 'test_ddelta_right_size')
        self.assertEqual(os.stat(ret).st_size, 3150)

    def test_preparing_xfer_ddelta_small_binary_change(self):
        ret = ddelta.delta_prepare_ddelta_xfer(delta_two['file'], delta_last['file'], 'test_ddelta_small_binary_change')
        self.assertEqual(os.stat(ret).st_size, 1104)
        hash = md5(open(ret, 'rb').read()).hexdigest()
        self.assertEqual(hash, "70d5d4857d8e4c6f6e9b614d1a4f3d2a")


class TestDDeltaRegenerate(unittest.TestCase):

    def setUp(self):
        os.chdir(test_path)
        self.xfer_file = ddelta.delta_prepare_ddelta_xfer(original['file'], delta_last['file'], 'test_skell')
        self.delta_large = ddelta.delta_repackage_from_ddelta_xfer(original['file'], self.xfer_file)

    def test_regenerate_deb_about_size_target(self):
        latest_repacked = ddelta.deb_generate_final_package(self.delta_large, 'new_foo_package')
        self.assertAlmostEqual(os.stat(delta_last['file']).st_size, os.stat(latest_repacked).st_size, delta=10)

    def test_regenerate_deb_use_metadata_filename(self):
        latest_repacked = ddelta.deb_generate_final_package(self.delta_large)
        print("escribio el nombre ", latest_repacked)
        self.assertEqual(delta_last['file'], latest_repacked)

    def test_repackaged_deb_internal_md5s(self):
        latest_repacked = ddelta.deb_generate_final_package(self.delta_large, 'new_foo_package_1')
        path = os.path.dirname(latest_repacked)
        os.chdir(path)
        ddelta.sh("ar x {}".format(latest_repacked))
        ddelta.sh("tar zxf {}".format('control.tar.gz'))
        ddelta.sh("tar Jxf {}".format('data.tar.xz'))
        self.assertTrue(ddelta.sh("md5sum -c md5sums"))

    def test_repackaged_deb_internal_md5s_must_fail(self):
        latest_repacked = ddelta.deb_generate_final_package(self.delta_large, 'new_foo_package_2')
        path = os.path.dirname(latest_repacked)
        os.chdir(path)
        ddelta.sh("ar x {}".format(latest_repacked))
        ddelta.sh("tar zxf {}".format('control.tar.gz'))
        ddelta.sh("tar Jxf {}".format('data.tar.xz'))
        ddelta.sh("echo 1 >> usr/lib/python3/dist-packages/imaplib2.py")
        with self.assertRaises(BaseException):
            ddelta.sh("md5sum -c md5sums")


class TestDDeltaLabelingXfer(unittest.TestCase):

    def test_labeling(self):
        self.assertEqual(ddelta.delta_get_friendly_name(original['file'], delta_last['file']), 'python3-imaplib2_2.42-1-to-2.50-2.ar')


class TestDebIntegrity(unittest.TestCase):

    def setUp(self):
        os.chdir(test_path)

    def test_deb_integrity_pass(self):
        self.assertTrue(ddelta.deb_check_package_integrity(original['file']))

    def test_deb_integrity_pass_2(self):
        self.assertTrue(ddelta.deb_check_package_integrity(delta_last['file']))

    def test_deb_integrity_fail(self):
        self.assertFalse(ddelta.deb_check_package_integrity(broken_deb['file']))

    def test_deb_integrity_pass_at_repackaging(self):
        self.xfer_file = ddelta.delta_prepare_ddelta_xfer(original['file'], delta_last['file'], 'test_skell')
        self.delta_large = ddelta.delta_repackage_from_ddelta_xfer(original['file'], self.xfer_file)
        latest_repacked = ddelta.deb_generate_final_package(self.delta_large, 'new_foo_package_1')
        self.assertTrue(ddelta.deb_check_package_integrity(latest_repacked))


class TestDebRenameFromMetadata(unittest.TestCase):

    def setUp(self):
        os.chdir(test_path)

    def test_deb_rename_from_metadata(self):
        tmp_dir = tempfile.mkdtemp()
        temp = os.path.join(tmp_dir, 'tmp.deb')
        shutil.copy(original['file'], temp)
        self.assertTrue(os.path.exists(temp))
        output = ddelta.deb_rename_file_from_metadata(temp)
        self.assertEqual(original['file'], os.path.basename(output))




if __name__ == '__main__':
    unittest.main()
