#!/usr/bin/python

import sys, os
import git
import importlib

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), ".."))
import build_support as bs

class VulkanCtsBuilder(object):
    def __init__(self):
        self._pm = bs.ProjectMap()
        self._options = bs.Options()
        self._src_dir = self._pm.project_source_dir()
        self._build_dir = self._src_dir + "/build_" + self._options.arch
        self._build_root = self._pm.build_root()

    def build(self):
        spirvtools = self._src_dir + "/external/spirv-tools/src"
        if not os.path.islink(spirvtools):
            bs.rmtree(spirvtools)
        if not os.path.exists(spirvtools):
            os.symlink("../../../spirvtools", spirvtools)
        glslang = self._src_dir + "/external/glslang/src"
        if not os.path.islink(glslang):
            bs.rmtree(glslang)
        if not os.path.exists(glslang):
            os.symlink("../../../glslang", glslang)

        # change spirv-tools and glslang to use the commits specified
        # in the vulkancts sources
        sys.path = [os.path.abspath(os.path.normpath(s)) for s in sys.path]
        sys.path = [gooddir for gooddir in sys.path if "vulkancts" not in gooddir]
        sys.path.append(self._src_dir + "/external/")
        fetch_sources = importlib.import_module("fetch_sources", ".")
        for package in fetch_sources.PACKAGES:
            if not isinstance(package, fetch_sources.GitRepo):
                continue
            repo_path = self._src_dir + "/external/" + package.baseDir + "/src/"
            print "Checking out: " + repo_path + " : " + package.revision
            repo = git.Repo(repo_path)
            repo.git.checkout(package.revision)
        
        btype = "Release"
        if self._options.type == "debug":
            btype = "RelDeb"
        cmd = ["cmake", "-GNinja", "-DCMAKE_BUILD_TYPE=" + btype,
               "-DCMAKE_C_COMPILER=clang-3.7", "-DCMAKE_CXX_COMPILER=clang++-3.7",
               "-DCMAKE_INSTALL_PREFIX:PATH=" + self._build_root, ".."]
        if not os.path.exists(self._build_dir):
            os.makedirs(self._build_dir)
        os.chdir(self._build_dir)
        bs.run_batch_command(cmd)
        bs.run_batch_command(["ninja"])
        bin_dir = self._build_root + "/opt/deqp/"
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir)

        bs.run_batch_command(["cp", "-a", "-n",
                              self._build_dir + "/external/vulkancts/modules",
                              bin_dir])
        bs.Export().export()

    def clean(self):
        bs.git_clean(self._src_dir)

    def test(self):
        pass

if __name__ == "__main__":
    bs.build(VulkanCtsBuilder())