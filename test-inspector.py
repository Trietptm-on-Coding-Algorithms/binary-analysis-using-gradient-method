#!/usr/bin/python
from nao.util import Inspector, Tactic

def test_if_statement_tree():
    print("\n[*] === simple-if-statement-tree ===")
    inspector = Inspector("sample/simple-if-statement-tree", debug=True)
    cmp1 = 0x7d6

    cond = inspector.get_condition_at(Tactic.near_path_constraint, relative_addr=cmp1)
    print("condition = {}".format(cond))
    variables = cond.get_variables()
    print("variables = {} (type={})".format(variables, type(variables)))

    breakpoint_addrs = sorted(set(map(lambda _: _.addr, variables)))

    inspector.run(args=["#aab"])
    y = {}
    for addr in breakpoint_addrs:
        inspector.set_breakpoint(relative_addr=addr)
        inspector.cont()
        res = inspector.read_vars(variables.find(addr=addr))
        print("read_var() = {}".format(res))
        y.update(res)
    return y

def test_elf_cheker(stdin):
    print("\n[*] === simple-elf-checker (stdin={}) ===".format(stdin))
    inspector = Inspector("sample/simple-elf-checker", debug=True)
    find_addr = 0x836

    cond = inspector.get_condition_at(Tactic.near_path_constraint, relative_addr=find_addr)
    print("constraints = {}".format(cond))
    variables = cond.get_variables()
    print("variables = {} (type={})".format(variables, type(variables)))

    breakpoint_addrs = sorted(set(map(lambda _: _.addr, variables)))

    inspector.run(stdin=stdin)
    y = {}
    for addr in breakpoint_addrs:
        b = inspector.set_breakpoint(relative_addr=addr)
        print("breakpioint address = {:#x}".format(b.address))
        try:
            inspector.cont()
        except Exception as e:
            print(e)
            break
        b.desinstall(set_ip=True)
        if not inspector.is_tracee_attached():
            break

        res = inspector.read_vars(variables.find(addr=addr))
        print("read_var() = {}".format(res))
        y.update(res)
    return y

if __name__ == "__main__":
    res = test_if_statement_tree()
    print(res)

    res = test_elf_cheker(stdin=b"\x7fELF") # satisfies all constraints
    print(res)

    res = test_elf_cheker(stdin=b"abcd")
    print(res)