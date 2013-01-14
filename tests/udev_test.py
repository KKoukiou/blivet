#!/usr/bin/python

import mock
import os

class UdevTest(mock.TestCase):

    def setUp(self):
        self.setupModules(["_isys", "block", "ConfigParser"])
        self.fs = mock.DiskIO()

        import blivet.udev
        blivet.udev.os = mock.Mock()
        blivet.udev.log = mock.Mock()
        blivet.udev.open = self.fs.open

    def tearDown(self):
        self.tearDownModules()

    def udev_enumerate_devices_test(self):
        import blivet.udev
        ENUMERATE_LIST = [
            '/sys/devices/pci0000:00/0000:00:1f.2/host0/target0:0:0/0:0:0:0/block/sda',
            '/sys/devices/virtual/block/loop0',
            '/sys/devices/virtual/block/loop1',
            '/sys/devices/virtual/block/ram0',
            '/sys/devices/virtual/block/ram1',
            '/sys/devices/virtual/block/dm-0',
        ]

        blivet.udev.global_udev.enumerate_devices = mock.Mock(return_value=ENUMERATE_LIST)
        ret = blivet.udev.udev_enumerate_devices()
        self.assertEqual(set(ret),
            set(['/devices/pci0000:00/0000:00:1f.2/host0/target0:0:0/0:0:0:0/block/sda',
            '/devices/virtual/block/loop0', '/devices/virtual/block/loop1',
            '/devices/virtual/block/ram0', '/devices/virtual/block/ram1',
            '/devices/virtual/block/dm-0'])
        )

    def udev_get_device_1_test(self):
        import blivet.udev

        class Device(object):
            def __init__(self):
                self.sysname = 'loop1'
                self.dict = {'symlinks': ['/dev/block/7:1'],
                    'SUBSYSTEM': 'block',
                    'MAJOR': '7',
                    'DEVPATH': '/devices/virtual/block/loop1',
                    'UDISKS_PRESENTATION_NOPOLICY': '1',
                    'UDEV_LOG': '3',
                    'DEVNAME': '/dev/loop1',
                    'DEVTYPE': 'disk',
                    'DEVLINKS': '/dev/block/7:1',
                    'MINOR': '1'
                }

            def __getitem__(self, key):
                return self.dict[key]

            def __setitem__(self, key, value):
                self.dict[key] = value

        blivet.udev.os.path.exists.return_value = True
        DEV_PATH = '/devices/virtual/block/loop1'
        dev = Device()
        blivet.udev.global_udev = mock.Mock()
        blivet.udev.global_udev.create_device.return_value = dev
        blivet.udev.udev_parse_uevent_file = mock.Mock(return_value=dev)

        ret = blivet.udev.udev_get_device(DEV_PATH)
        self.assertTrue(isinstance(ret, Device))
        self.assertEqual(ret['name'], ret.sysname)
        self.assertEqual(ret['sysfs_path'], DEV_PATH)
        self.assertTrue(blivet.udev.udev_parse_uevent_file.called)

    def udev_get_device_2_test(self):
        import blivet.udev
        blivet.udev.os.path.exists.return_value = False
        ret = blivet.udev.udev_get_device('')
        self.assertEqual(ret, None)

    def udev_get_device_3_test(self):
        import blivet.udev
        blivet.udev.os.path.exists.return_value = True
        blivet.udev.global_udev = mock.Mock()
        blivet.udev.global_udev.create_device.return_value = None
        ret = blivet.udev.udev_get_device('')
        self.assertEqual(ret, None)

    def udev_get_devices_test(self):
        import blivet.udev
        blivet.udev.udev_settle = mock.Mock()
        DEVS = \
            ['/devices/pci0000:00/0000:00:1f.2/host0/target0:0:0/0:0:0:0/block/sda',
            '/devices/virtual/block/loop0', '/devices/virtual/block/loop1',
            '/devices/virtual/block/ram0', '/devices/virtual/block/ram1',
            '/devices/virtual/block/dm-0']
        blivet.udev.udev_enumerate_devices = mock.Mock(return_value=DEVS)
        blivet.udev.udev_get_device = lambda x: x
        ret = blivet.udev.udev_get_devices()
        self.assertEqual(ret, DEVS)

    def udev_parse_uevent_file_1_test(self):
        import blivet.udev
        blivet.udev.os.path.normpath = os.path.normpath
        blivet.udev.os.access.return_value = True

        FILE_CONTENT = "MAJOR=7\nMINOR=1\nDEVNAME=loop1\nDEVTYPE=disk\n"
        self.fs.open('/sys/devices/virtual/block/loop1/uevent', 'w').write(FILE_CONTENT)
        dev = {'sysfs_path': '/devices/virtual/block/loop1'}
        ret = blivet.udev.udev_parse_uevent_file(dev)
        self.assertEqual(ret,
            {'sysfs_path': '/devices/virtual/block/loop1',
            'DEVNAME': 'loop1',
            'DEVTYPE': 'disk',
            'MAJOR': '7',
            'MINOR': '1'})

    def udev_parse_uevent_file_2_test(self):
        import blivet.udev
        blivet.udev.os.path.normpath = os.path.normpath
        blivet.udev.os.access.return_value = False

        dev = {'sysfs_path': '/devices/virtual/block/loop1'}
        ret = blivet.udev.udev_parse_uevent_file(dev)
        self.assertEqual(ret, {'sysfs_path': '/devices/virtual/block/loop1'})

    def udev_settle_test(self):
        import blivet.udev
        blivet.udev.util = mock.Mock()
        blivet.udev.udev_settle()
        self.assertTrue(blivet.udev.util.run_program.called)

    def udev_trigger_test(self):
        import blivet.udev
        blivet.udev.util = mock.Mock()
        blivet.udev.udev_trigger()
        self.assertTrue(blivet.udev.util.run_program.called)
