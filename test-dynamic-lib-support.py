#!/usr/bin/python
from nao.util import Inspector, Tactic
import signal

def test_file():
    print("\n[*] === file ===")
    name_libmagic_so = 'libmagic.so.1'
    inspector = Inspector("./sample/file", debug=True)
    # find_addr = 0x1742D # ret block of is_tar
    find_addr = 0x173F8 # return 3 at is_tar
    # find_addr = 0x17293

    cond = inspector.get_condition_at(Tactic.near_path_constraint, object_name=name_libmagic_so, relative_addr=find_addr)
    print("post condition = {}".format(cond))
    y_variables = cond.get_variables()
    print("y_variables = {} (type={})".format(y_variables, type(y_variables)))

    inspector.run(args=["/vagrant/sample.tar"], env={'LD_LIBRARY_PATH': '/vagrant/sample/'})

    return inspector.collect(y_variables)

if __name__ == "__main__":
    res = test_file()
    print(res)
    assert len(res) > 0
