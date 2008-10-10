


def make_incrementor(start=0, by=5):
    def incrementor():
        i = incrementor.i
        incrementor.i += by
        return i
    incrementor.i = start
    return incrementor



def test_1():
    from pickle import Pickler, Unpickler
    from cStringIO import StringIO

    fives = make_incrementor(0, 5)
    print fives
    print fives(), fives(), fives()

    ba = BrineBarrel()
    ba.add_function(fives, "fives")

    buf = StringIO()

    pi = Pickler(buf)
    pi.dump(ba)

    up = Unpickler(StringIO(buf.getvalue()))
    new_ba = up.load()
    fives = new_ba.get_function("fives", locals())

    print fives
    print fives(), fives(), fives()



def make_recursive_adder(by_i=0):
    def add_i(x, rem=by_i):
        if rem > 0:
            return 1+add_i(x, rem-1)
        else:
            return x
    return add_i



def test_2():
    from pickle import Pickler, Unpickler
    from cStringIO import StringIO

    add_8 = make_recursive_adder(8)
    print add_8
    print add_8(10)

    ba = BrineBarrel()
    ba.add_function(add_8, "add_8")

    buf = StringIO()

    pi = Pickler(buf)
    pi.dump(ba)

    up = Unpickler(StringIO(buf.getvalue()))
    new_ba = up.load()
    new_ba.rename_function("add_8", "new_add_8")
    new_add_8 = new_ba.get_function("new_add_8", locals())

    print new_add_8
    print new_add_8(10)



def all_tests():
    test_1()
    test_2()



# placeholder until I use unittest here
def suite():
    return None



if __name__ == '__main__':
    all_tests()



#
# The end.
