"""
Tests the `tk_utils_core/messages.py` module

"""
from __future__ import annotations

import time
import datetime as dt
import io
import pathlib

from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )

from tk_utils_core.messages import (
        LogFunc,
        LogParms,
        Tee,
        align,
        align_by_char,
        colorize, 
        decolorize,
        dirtree,
        fmt_elapsed,
        fmt_name,
        fmt_now,
        fmt_str,
        fmt_type,
        fmt_value,
        get_type_name,
        join_names,
        justify_values,
        logfunc,
        tdelta_to_ntup,
        type_err_msg,
        trim_values,
        value_err_msg,
        )
from tk_utils_core.options import options

class TestMessagesMod(BaseTestCase):
    """
    Test the `tk_utils_core/messages.py` module
    """
    _only_in_debug = [
            'test_fmt_str',
            'test_fmt_now',
            'test_fmt_elapsed',
            'test_colorize',
            'test_decolorize',
            'test_fmt_name',
            'test_fmt_value',
            'test_fmt_type',
            'test_get_type_name',
            'test_join_names',
            'test_justify_values',
            'test_align_and_align_by_char',
            'test_tdelta_to_ntup',
            'test_type_err_msg_and_value_err_msg',
            'test_logfunc_instance',
            'test_logparms_defaults',
            'test_tee_write',
            'test_dirtree_output',
            ]


    def test_fmt_str(self):
        """
        """
        self._start_msg()
        func = fmt_str
        self._run_doctest(func)

        s = 'xxx'
        self.assertEqual(fmt_str(s, width=1), "x\nx\nx")
        self.assertEqual(fmt_str(s, indent=' '), " xxx")
        self.assertEqual(fmt_str(f"  {s}", dedent=True), "xxx")

    def test_fmt_now(self):
        """
        """
        self._start_msg()
        func = fmt_now
        self._run_doctest(func)

        now_str = func()
        self.assertRegex(now_str, r"\d{2}_\d{2}_\d{2}")

    def test_fmt_elapsed(self):
        """
        """
        self._start_msg()
        func = fmt_elapsed
        self._run_doctest(func)

        t1 = dt.datetime.now()
        time.sleep(0.01)
        t2 = dt.datetime.now()

        out = func(t2-t1)
        self.assertIsInstance(out, str)

    def test_colorize(self):
        """
        """
        self._start_msg()
        func = colorize
        self._run_doctest(func)

        colored = func("msg", color="red")
        self.assertIn("\x1b[31m", colored)

    def test_decolorize(self):
        """
        """
        self._start_msg()
        func = decolorize
        self._run_doctest(func)

        colored = colorize("msg", color="red")
        self.assertEqual(func(colored), "msg")

    def test_fmt_name(self):
        """
        """
        self._start_msg()
        func = fmt_name
        self._run_doctest(func)

        res = func("x")
        expected = '`x`'
        self.assertEqual(res, expected)

        res = func("value", quotes='"')
        expected = '"value"'
        self.assertEqual(res, expected)


    def test_fmt_value(self):
        """
        """
        self._start_msg()
        func = fmt_value
        self._run_doctest(func)
        self.assertEqual(fmt_value(123), "123")
        res = fmt_value(None, none_as_empty=True)
        expected = ''
        self.assertEqual(res, expected)
        res = fmt_value(None, none_as_empty=False)
        expected = 'None'
        self.assertEqual(res, expected)
        res = fmt_value([1, 2, 3], representer=str)
        expected = '[1, 2, 3]'
        self.assertEqual(res, expected)
        res = fmt_value("abc def ghi", width=5, representer=repr)
        expected = "'abc\ndef\nghi'"
        self.assertEqual(res, expected)
        res = fmt_value("a" * 100, max_lines=2, width=10)
        expected = "aaaaaaaaaa\n[...]"
        self.assertEqual(res, expected)

    def test_fmt_type(self):
        """
        """
        self._start_msg()
        func = fmt_type
        self._run_doctest(func)
        res = fmt_type(int)
        expected = "'int'"
        self.assertEqual(res, expected)

        res = fmt_type(dict, quotes='"')
        expected = '"dict"'
        self.assertEqual(res, expected)

    def test_get_type_name(self):
        """
        """
        self._start_msg()
        func = get_type_name
        self._run_doctest(func)
        self.assertEqual(get_type_name(type(3.14)), "float")
        self.assertEqual(get_type_name(type(str)), "type")

    def test_join_names(self):
        """
        """
        self._start_msg()
        func = join_names
        self._run_doctest(func)

        self.assertEqual(join_names(["x", "y"]), "x and y")
        self.assertEqual(join_names(["x", "y", "z"]), "x, y, and z")

        self.assertEqual(
                join_names(["x", "y", "z"], formatter=lambda x: f"'{x}'"), 
                "'x', 'y', and 'z'")

        for conjunction in ['or', '  or  ']:
            self.assertEqual(
                    join_names(["x", "y", "z"], 
                               formatter=lambda x: f"'{x}'",
                               conjunction=conjunction), 
                    "'x', 'y', or 'z'")

    def test_justify_values(self):
        """
        """
        self._start_msg()
        self._run_doctest(justify_values)

        res = justify_values(['a', 'bbb', 'cc'], how='left')
        assert res == ('a  ', 'bbb', 'cc ')

        res = justify_values(['a', 'bbb', 'cc'], how='right')
        assert res == ('  a', 'bbb', ' cc')

        res = justify_values(['a', 'bbb', 'cc'], how='center')
        assert res == (' a ', 'bbb', 'cc ')

    def test_align_and_align_by_char(self):
        """
        """
        self._start_msg()
        self._run_doctest(align)
        self._run_doctest(align_by_char)

        res = align([('abc:def',), ('a:xxx',), ('long',)], char=':', how='left')
        expected = ' abc:def\n   a:xxx\nlong   '
        self.assertEqual(res, expected)

        res = align([('a', '1.2'), ('bb', '22.22')], char='.')
        expected = 'a   1.2 \nbb 22.22'
        self.assertEqual(res, expected)

        res = align([('a', '1.2'), ('bb', '22.22')], char='.', how='center')
        expected = 'a   1.2 \nbb 22.22'
        self.assertEqual(res, expected)

        res = align([('a', '1.2'), ('bbb', '22.22')], char='.', how='center')
        expected = ' a   1.2 \nbbb 22.22'

        self.assertEqual(res, expected)

        res = align([('a', '1.2'), ('bb', '22.22')])
        expected = 'a  1.2  \nbb 22.22'
        self.assertEqual(res, expected)

        res = align([('a', '1.2'), ('bb', '22.22')], how='center')
        expected = 'a   1.2 \nbb 22.22'
        self.assertEqual(res, expected)

        res = align([('a', '1.2'), ('bbb', '22.22')], how='center')
        expected = ' a   1.2 \nbbb 22.22'
        self.assertEqual(res, expected)

        res = align([('a', '1.2'), ('bb', '22.22')], how='right')
        expected = ' a   1.2\nbb 22.22'
        self.assertEqual(res, expected)

        res = align(['x', 'yy', 'zzz'], how='right')
        expected = '  x\n yy\nzzz'
        self.assertEqual(res, expected)

        res = align([('abc:def',), ('a:xxx',), ('long',)], char=':', how='right')
        expected = 'abc:def \n  a:xxx \n    long'
        self.assertEqual(res, expected)

        s = ["a:1", "bb:2", "ccc:3"]
        res = align(s, char=':')
        expected = '  a:1\n bb:2\nccc:3'
        self.assertEqual(res, expected)

        res = align_by_char(
                ['abc:def', 'a:xxx', 'long'], char=':', how='left')
        expected = (' abc:def', '   a:xxx', 'long   ')
        self.assertEqual(res, expected)

        res = align_by_char(['abc:def', 'a:xxx', 'long'], char=':', how='right')
        expected = ('abc:def ', '  a:xxx ', '    long')
        self.assertEqual(res, expected)

        res = align_by_char(['abc:def', 'a:xxx', 'long'], char=':', how='center')
        expected = (' abc:def', '   a:xxx', '  long  ')
        self.assertEqual(res, expected)


    def test_tdelta_to_ntup(self):
        """
        """
        self._start_msg()
        self._run_doctest(tdelta_to_ntup)
        td = dt.timedelta(days=1, seconds=62)
        nt = tdelta_to_ntup(td)
        self.assertEqual(nt.days, 1)
        self.assertEqual(nt.hours, 0)
        self.assertEqual(nt.mins, 1)
        self.assertEqual(nt.secs, 2)

    def test_type_err_msg_and_value_err_msg(self):
        """
        """
        self._start_msg()
        self._run_doctest(type_err_msg)
        self._run_doctest(value_err_msg)

    def test_logfunc_instance(self):
        """
        """
        self._start_msg()
        self._run_doctest(logfunc)

    def test_logparms_defaults(self):
        """
        """
        self._start_msg()
        self._run_doctest(LogParms)

    def test_tee_write(self):
        """
        """
        self._start_msg()
        self._run_doctest(Tee)

    def test_dirtree_output(self):
        """
        """
        self._start_msg()
        self._run_doctest(dirtree)

def main(verbosity=2, *args, **kargs):
    cls = TestMessagesMod
    run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)

if __name__ == '__main__':
    main()
    #with options.set_values({'debug': True}):
    #    main()
