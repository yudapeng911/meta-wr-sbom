#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import with_statement
from __future__ import absolute_import
import codecs
import os
from io import open

def packaged(pkg, d):
    return os.access(get_subpkgedata_fn(pkg, d) + '.packaged', os.R_OK)

def read_pkgdatafile(fn, d):
    pkgdata = {}

    def decode(str):
        c = codecs.getdecoder("unicode_escape")
        return c(str)[0]

    if os.access(fn, os.R_OK):
        import re
        with open(fn, 'r') as f:
            lines = f.readlines()

        distro_ver = d.getVar("DISTRO_VERSION", True)
        if 'Yocto' in d.getVar("DISTRO_NAME", True):
            if distro_ver[:3] > '3.3':
                r = re.compile(r"(^.+?):\s+(.*)")
            else:
                r = re.compile("([^:]+):\s*(.*)")
        elif 'Wind River' in d.getVar("DISTRO_NAME", True):
            if (distro_ver.split('.')[0] == '10') and (distro_ver.split('.')[1] > '21'):
                r = re.compile(r"(^.+?):\s+(.*)")
            else:
                r = re.compile("([^:]+):\s*(.*)")

        for l in lines:
            m = r.match(l)
            if m:
                pkgdata[m.group(1)] = decode(m.group(2))

    return pkgdata

def get_subpkgedata_fn(pkg, d):
    return d.expand('${PKGDATA_DIR}/runtime/%s' % pkg)

def has_subpkgdata(pkg, d):
    return os.access(get_subpkgedata_fn(pkg, d), os.R_OK)

def read_subpkgdata(pkg, d):
    return read_pkgdatafile(get_subpkgedata_fn(pkg, d), d)

def has_pkgdata(pn, d):
    fn = d.expand('${PKGDATA_DIR}/%s' % pn)
    return os.access(fn, os.R_OK)

def read_pkgdata(pn, d):
    fn = d.expand('${PKGDATA_DIR}/%s' % pn)
    return read_pkgdatafile(fn, d)

#
# Collapse FOO_pkg variables into FOO
#
def read_subpkgdata_dict(pkg, d):
    ret = {}
    subd = read_pkgdatafile(get_subpkgedata_fn(pkg, d), d)
    for var in subd:
        distro_ver = d.getVar("DISTRO_VERSION", True)
        if 'Yocto' in d.getVar("DISTRO_NAME", True):
            if distro_ver[:3] > '3.3':
                newvar = var.replace(":" + pkg, "")
                if newvar == var and var + ":" + pkg in subd:
                    continue
            else:
                newvar = var.replace("_" + pkg, "")
                if newvar == var and var + "_" + pkg in subd:
                    continue
        if 'Wind River' in d.getVar("DISTRO_NAME", True):
            if (distro_ver.split('.')[0] == '10') and (distro_ver.split('.')[1] > '21'):
                newvar = var.replace(":" + pkg, "")
                if newvar == var and var + ":" + pkg in subd:
                    continue
            else:
                newvar = var.replace("_" + pkg, "")
                if newvar == var and var + "_" + pkg in subd:
                    continue
        ret[newvar] = subd[var]
    return ret

def read_subpkgdata_extended(pkg, d):
    import json

    fn = d.expand("${PKGDATA_DIR}/extended/%s.json" % pkg)
    try:
        with open(fn, "rt", encoding="utf-8") as f:
            return json.load(f)
    except IOError:
        return None

def _pkgmap(d):
    """Return a dictionary mapping package to recipe name."""

    pkgdatadir = d.getVar("PKGDATA_DIR")

    pkgmap = {}
    try:
        files = os.listdir(pkgdatadir)
    except OSError:
        bb.warn("No files in %s?" % pkgdatadir)
        files = []

    for pn in [f for f in files if not os.path.isdir(os.path.join(pkgdatadir, f))]:
        try:
            pkgdata = read_pkgdatafile(os.path.join(pkgdatadir, pn), d)
        except OSError:
            continue

        packages = pkgdata.get("PACKAGES") or ""
        for pkg in packages.split():
            pkgmap[pkg] = pn

    return pkgmap

def pkgmap(d):
    """Return a dictionary mapping package to recipe name.
    Cache the mapping in the metadata"""

    pkgmap_data = d.getVar("__pkgmap_data", False)
    if pkgmap_data is None:
        pkgmap_data = _pkgmap(d)
        d.setVar("__pkgmap_data", pkgmap_data)

    return pkgmap_data

def recipename(pkg, d):
    """Return the recipe name for the given binary package name."""

    return pkgmap(d).get(pkg)
