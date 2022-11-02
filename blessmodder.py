import os
import shutil
import struct
import re
import binascii
import stat
import traceback
import argparse

ver = "1.0.2"
domver = 5.58

BLESS_TABLE_SIZE = 100
BLESS_TABLE_RECORD_SIZE = 0x78

BLESS_TABLE_LENGTH = BLESS_TABLE_SIZE * BLESS_TABLE_RECORD_SIZE

# This is probably excessive, but better to be safe...
BLESS_TABLE_START_DATA = b"Increased Morale"
BLESS_TABLE_START_DATA += b"\x00" * 0x14
BLESS_TABLE_START_DATA += b"\xff\xff"
BLESS_TABLE_START_DATA += b"\x00" * 0xa
BLESS_TABLE_START_DATA += b"\x34\x01\x00\x00\x01"
BLESS_TABLE_START_DATA += b"\x00" * 0x37
BLESS_TABLE_START_DATA += b"\xff"
BLESS_TABLE_START_DATA += b"\x00" * 0xb
BLESS_TABLE_START_DATA += b"Superior Morale"
BLESS_TABLE_START_DATA += b"\x00" * 0x13
BLESS_TABLE_START_DATA += b"\x01\x00\xff\xff"
BLESS_TABLE_START_DATA += b"\x00" * 0xa
BLESS_TABLE_START_DATA += b"\x34\x01\x00\x00\x01\x00\x00\x00\x27\x02\x00\x00\x01"

BLESS_TABLE_CRC32 = 1716275267

class Executable(object):
    def __init__(self, fp):
        self.fp = fp
        with open(self.fp, "rb") as f:
            self.content = f.read()
        self.blesstableOffset = None
    def getBlesstable(self, ignorecrc=False):
        if self.blesstableOffset is None:
            self._findBlesstable()
        retval = self.content[self.blesstableOffset:self.blesstableOffset+BLESS_TABLE_LENGTH]
        if not ignorecrc and binascii.crc32(retval) != BLESS_TABLE_CRC32:
            raise ValueError(f"Checksum of bless table does not match, maybe Dominions was updated."
                             f"crc32 = {binascii.crc32(retval)}, expected {BLESS_TABLE_CRC32}")
        return retval
    def writeReplacedBlesstable(self, newfp, newblesstable):
        if newfp == self.fp:
            raise ValueError("Do not overwrite the original executable")
        self._findBlesstable()
        with open(newfp, "wb") as f:
            f.write(self.content[:self.blesstableOffset])
            f.write(newblesstable)
            f.write(self.content[self.blesstableOffset+BLESS_TABLE_LENGTH:])
    def _findBlesstable(self):
        if self.blesstableOffset is None:
            incidences = self.content.count(BLESS_TABLE_START_DATA)
            if incidences > 1:
                raise ValueError(f"Bless table data found {incidences} times in the executable {self.fp}")
            if incidences == 0:
                raise ValueError(f"Bless table data not found in executable {self.fp}")
            self.blesstableOffset = self.content.find(BLESS_TABLE_START_DATA)
            print(f"Bless table offset in {self.fp} = {hex(self.blesstableOffset)}")

class BlessEffect(object):
    def __init__(self, content):
        self.name = struct.unpack("<32s", content[:0x20])[0]
        self.path1 = struct.unpack("<h", content[0x20:0x22])[0]
        self.path1level = struct.unpack("<h", content[0x22:0x24])[0]
        self.path2 = struct.unpack("<h", content[0x24:0x26])[0]
        self.path2level = struct.unpack("<h", content[0x26:0x28])[0]
        self.effect10buffs = struct.unpack("<q", content[0x28:0x30])[0]
        self.effects = []
        self.scales = []
        # Strip null bytes
        if self.name[-1] == 0:
            while 1:
                if len(self.name) > 0 and self.name[-1] == 0:
                    self.name = self.name[:-1]
                    continue
                break
        for x in range(0, 7):
            startoffset = 0x30 + (x * 8)
            effectid = struct.unpack("<i", content[startoffset:startoffset+4])[0]
            effectmagnitude = struct.unpack("<i", content[startoffset+4:startoffset+8])[0]
            if effectid <= 0:
                break
            self.effects.append((effectid, effectmagnitude))
        for x in range(0, 6):
            startoffset = 0x6c + (x * 2)
            scaleid = content[startoffset]
            scaleamt = content[startoffset+1]
            if scaleid <= 0:
                break
            self.scales.append((scaleid, scaleamt))
    def clear(self):
        self.name = b"New Bless Effect"
        self.path1 = 0
        self.path1level = 0
        self.path2 = -1
        self.path2level = 0
        self.effect10buffs = 0
        self.effects = []
        self.scales = []
    def addEffect(self, effectid, effectmagnitude):
        if len(self.effects) >= 7:
            raise ValueError(f"No free effect slots for bless {self.name}")
        self.effects.append((effectid, effectmagnitude))
    def addScale(self, scaleid, scaleamt):
        # This is how scale negation is done internally it seems
        if scaleamt < 1:
            scaleid += 6
            scaleamt *= -1
        # The executable seems to stop reading these at 4
        if len(self.scales) >= 4:
            raise ValueError(f"No free scale slots for bless {self.name}")
        self.scales.append((scaleid, scaleamt))
    def pack(self):
        # Order effects: 550 always goes first, 551 always last
        if (550, 1) in self.effects:
            self.effects.pop(self.effects.index((550, 1)))
            self.effects.insert(0, (550, 1))
        if (551, 1) in self.effects:
            self.effects.pop(self.effects.index((551, 1)))
            self.effects.append((551, 1))

        out = b""
        out += struct.pack("<32s", self.name)
        out += struct.pack("<h", self.path1)
        out += struct.pack("<h", self.path1level)
        out += struct.pack("<h", self.path2)
        out += struct.pack("<h", self.path2level)
        out += struct.pack("<q", self.effect10buffs)
        for effect in self.effects:
            effid, effmag = effect
            out += struct.pack("<i", effid)
            out += struct.pack("<i", effmag)
        numToPad = 7 - len(self.effects)
        for x in range(0, numToPad):
            out += b"\x00" * 8
        # Looks like an extra 4b here
        out += b"\x00\x00\x00\x00"
        for scale in self.scales:
            effid, effmag = scale
            out += struct.pack("<B", effid)
            out += struct.pack("<B", effmag)
        # This seems to expect two terminators for some reason
        out += b"\xff\x00\xff\x00"
        numToPad = 4 - len(self.scales)
        out += b"\x00\x00" * numToPad
        if len(out) != BLESS_TABLE_RECORD_SIZE:
            raise ValueError(f"Edited bless data for {self.name} has an invalid length {hex(len(out))} vs {hex(BLESS_TABLE_RECORD_SIZE)}")
        return out
    def __repr__(self):
        out = f"BlessEffect({self.name}, path1={self.path1}, path2={self.path2}, path1level={self.path1level}, " \
              f"path2level={self.path2level}, effect10buffs={self.effect10buffs}, effects={self.effects}, " \
              f"scales={self.scales})"
        return out


class BlessTable(object):
    def __init__(self, content):
        self.blesses = []
        for x in range(0, 100):
            eff = BlessEffect(content)
            content = content[BLESS_TABLE_RECORD_SIZE:]
            self.blesses.append(eff)
    def pack(self):
        out = b""
        for eff in self.blesses:
            out += eff.pack()
        if len(out) != BLESS_TABLE_LENGTH:
            raise ValueError(f"Edited bless table has incorrect length of {hex(len(out))} vs {hex(BLESS_TABLE_LENGTH)}")
        return out


class DBM(object):
    def __init__(self, fp):
        self.fp = fp
        self.blesstabletemplate = None
        self.blesstabledata = None
    def apply(self, executable):
        if self.blesstabledata is None:
            self.blesstabletemplate = executable.getBlesstable()
            self.buildBlesstable()
        isexe = False
        newfp = executable.fp
        if executable.fp.endswith(".exe"):
            isexe = True
            newfp = executable.fp[:-4]
        newfp += self.fp[:-4]
        if isexe:
            newfp += ".exe"
        executable.writeReplacedBlesstable(newfp, self.blesstabledata)
        # Unix: mark the copy as executable (IE: chmod +x)
        os.chmod(newfp, os.stat(newfp).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    def buildBlesstable(self):
        bt = BlessTable(self.blesstabletemplate)
        with open(self.fp, "r") as f:
            blessindex = None
            for lineindex, line in enumerate(f):
                linenum = lineindex + 1
                if blessindex is None:
                    blesseffect = None
                else:
                    blesseffect = bt.blesses[blessindex]
                line = line.strip()
                if line == "": continue
                if line.startswith("--"): continue

                m = re.match(r"#selectbless\W+(\d*)", line)
                if m is not None:
                    blessindex = int(m.group(1))
                    if blessindex < 0 or blessindex >= 100:
                        raise ValueError(f"Attempted to select invalid bless index {blessindex}, must be 0-99")
                    continue

                m = re.match(r"#cleareffects", line)
                if m is not None:
                    blesseffect.effects = []
                    continue

                m = re.match(r"#clearscales", line)
                if m is not None:
                    blesseffect.scales = []
                    continue

                m = re.match(r"#clear", line)
                if m is not None:
                    blesseffect.clear()
                    continue

                m = re.match(r"#addeffect\W+(\d*)\W+?([-0-9]*)", line)
                if m is not None:
                    effid = int(m.group(1))
                    effmag = int(m.group(2))
                    blesseffect.addEffect(effid, effmag)
                    continue

                m = re.match(r"#reqscale\W+(\d*)\W+?([-0-9]*)", line)
                if m is not None:
                    effid = int(m.group(1))
                    effmag = int(m.group(2))
                    if effid < 0 or effid > 5:
                        raise ValueError(f"{self.fp}:{linenum} Bad scale ID: {effid}, must be 0-5 inclusive")
                    if effmag > 3 or effmag < -3 or effmag == 0:
                        raise ValueError(f"{self.fp}:{linenum} Bad scale value: {effmag}, must be nonzero and -3 to +3")
                    blesseffect.addScale(effid, effmag)
                    continue

                m = re.match(r"#multipick", line)
                if m is not None:
                    if (551, 1) not in blesseffect.effects:
                        blesseffect.addEffect(551, 1)
                    continue

                m = re.match(r"#alwaysactive", line)
                if m is not None:
                    if (550, 1) not in blesseffect.effects:
                        blesseffect.addEffect(550, 1)
                    continue

                m = re.match('#name\\W+"(.*)"', line)
                if m is not None:
                    name = m.group(1).encode("utf-8")
                    if len(name) == 0 or len(name) >= 0x20:
                        raise ValueError(f"{self.fp}:{linenum} Bless name must have a nonzero length, and cannot be 32+ characters")
                    blesseffect.name = name
                    continue

                m = re.match("#path1\\W+?([-0-9]*)", line)
                if m is not None:
                    blesseffect.path1 = int(m.group(1))
                    if blesseffect.path1 > 7 or blesseffect.path1 < 0:
                        raise ValueError(f"{self.fp}:{linenum} path1 must be 0-7 inclusive")
                    continue

                m = re.match("#path2\\W+?([-0-9]*)", line)
                if m is not None:
                    blesseffect.path2 = int(m.group(1))
                    if blesseffect.path2 > 7 or blesseffect.path2 < -1:
                        raise ValueError(f"{self.fp}:{linenum} path2 must be -1 to 7 inclusive")
                    continue

                m = re.match("#path1level\\W+?([-0-9]*)", line)
                if m is not None:
                    blesseffect.path1level = int(m.group(1))
                    if blesseffect.path1level < 0 or blesseffect.path1level > 20:
                        raise ValueError(f"{self.fp}:{linenum} path1level must be 0-20")
                    continue

                m = re.match("#path2level\\W+?([-0-9]*)", line)
                if m is not None:
                    blesseffect.path2level = int(m.group(1))
                    if blesseffect.path2level < 0 or blesseffect.path2level > 20:
                        raise ValueError(f"{self.fp}:{linenum} path2level must be 0-20")
                    continue

                m = re.match("#effect10buffs\\W+?([-0-9]*)", line)
                if m is not None:
                    blesseffect.effect10buffs = int(m.group(1))
                    if blesseffect.effect10buffs <= 0:
                        raise ValueError(f"{self.fp}:{linenum} effect10buffs cannot be negative")
                    if blesseffect.effect10buffs >= (1 << 64):
                        raise ValueError(f"{self.fp}:{linenum} effect10buffs cannot exceed 2^64")
                    continue

                if line == "#end":
                    blessindex = None
                    continue

                raise ValueError(f"{self.fp}: Unrecognised content: '{line}' on line {linenum}")

        self.blesstabledata = bt.pack()

def locateExecutables():
    found = []
    thisdir = os.listdir(".")
    for fp in ["dom5_amd64", "dom5_arm", "dom5_mac", "dom5_x86", "Dominions5.exe"]:
        if fp in thisdir:
            found.append(fp)
    return found

def locateBlessmods():
    found = []
    for fp in os.listdir("."):
        if fp.endswith(".dbm"):
            found.append(fp)
    return found

def backupExecutables(executables):
    for executable in executables:
        stem = executable
        if stem.endswith(".exe"):
            stem = stem[:-4]
        stem += "_unmoddedbackup"
        if executable.endswith(".exe"):
            stem += ".exe"
        if not os.path.isfile(stem):
            print(f"Creating backup {stem}...")
            shutil.copy(executable, stem)
        else:
            print(f"Backup {stem} already exists.")

def main(fp=None):
    if fp is not None:
        os.chdir(fp)
    print(f"Blessmodder v{ver}, intended for Dominions {domver}\n\n")
    executables = locateExecutables()
    blessmods = locateBlessmods()
    backupExecutables(executables)
    for executable in executables:
        execObj = Executable(executable)
        for blessmod in blessmods:
            dbmObj = DBM(blessmod)
            print(f"Applying {blessmod} to {executable}...")
            dbmObj.apply(execObj)
    print("Success!")

def dumpVanillaBlesses(fp=None, outfp="vanillablesses.txt"):
    if fp is not None:
        os.chdir(fp)
    executables = locateExecutables()
    rawblessdata = Executable(executables[0]).getBlesstable()
    bt = BlessTable(rawblessdata)
    with open(outfp, "w") as f:
        for i, bless in enumerate(bt.blesses):
            f.write(f"{i}: {bless}\n")

def dumpExecutable(executablefp, offset):
    print(f"Dumping bless table from {executablefp} offset {offset}...")
    ex = Executable(executablefp)
    ex.blesstableOffset = offset
    rawblessdata = ex.getBlesstable(True)
    bt = BlessTable(rawblessdata)
    print(os.getcwd())
    with open(f"{executablefp}-blesstable.txt", "w") as f:
        for i, bless in enumerate(bt.blesses):
            f.write(f"{i}: {bless}\n")
    print(f"Finished writing {executablefp}-blesstable.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Blessmodder v{ver} - intended for Dominions version {domver}")
    parser.add_argument("-d", "--dumpexecutable", help="Path to binary to dump bless table from")
    parser.add_argument("-o", "--dumpexecutableoffset", help="Offset to start of bless table in binary")
    args = parser.parse_args()
    try:
        if args.dumpexecutable is not None:
            if args.dumpexecutableoffset is None:
                raise ValueError("Cannot dump executable bless table without an offset")
            dumpExecutable(args.dumpexecutable, int(args.dumpexecutableoffset))
        elif args.dumpexecutableoffset is not None:
            raise ValueError("Cannot dump executable: no path specified")
        else:
            main()
        input("Press ENTER to exit.")
    except Exception:
        print(traceback.format_exc())
        input("Application failed. Press ENTER to exit.")
